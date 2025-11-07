

from typing import List, Dict
import sqlite3
import os
import json
from pathlib import Path
from models.llm import get_llm_response_gpt_4o
from utils.trival_process import clean_sql_response, quote_sql_identifiers


def get_table_schema(conn, table_name: str):
    """从数据库提取表结构"""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    fields = [row[1] for row in cursor.fetchall()]
    return fields


def get_table_and_db_path_and_schema(table_name: str) -> Dict:
    """根据中文表名或表代码获取数据库路径和字段schema描述"""
    config_path = Path("/home/wangling/projects/agents_herd/data_2/tables.json")
    if not config_path.exists():
        return None

    # 加载配置
    with config_path.open(encoding="utf-8") as f:
        cfg = json.load(f)

    tables_list = cfg.get("tables", [])
    if not isinstance(tables_list, list) or not tables_list:
        return None

    # 优先精确匹配 table_name 或表代码 table；找不到则进行包含匹配
    target = None
    for item in tables_list:
        if item.get("table_name") == table_name or item.get("table") == table_name:
            target = item
            break
    if target is None:
        for item in tables_list:
            name = str(item.get("table_name", ""))
            code = str(item.get("table", ""))
            if table_name and (table_name in name or table_name in code):
                target = item
                break

    if target is None:
        return None

    db_path = target.get("table_path")
    

    # 连接数据库并提取 schema；如果库或表不存在，回退到 JSON 中的字段定义
    fields: List[str] = []
    try:
        conn = sqlite3.connect(db_path)
        fields = get_table_schema(conn, table_name) or []
        conn.close()
    except Exception:
        fields = []

    if not fields:
        fields = [f.get("name") for f in target.get("fields", []) if isinstance(f, dict) and f.get("name")]

    # schema_text = f"表 {target.get('table_name', table_name)}({table_code}) 的字段: {', '.join(fields)}"
    schema_text = """
    表名称：{table_name}
    表描述：{table_desc}
    字段：{fields}
    """.format(table_name=target.get('table_name', table_name), table_desc=target.get('table_desc', ''), fields=', '.join(fields))

    return { "db_path": db_path, "table_name": table_name, "schema": schema_text, "fields": fields}

def get_table_relations(table_names: List[str]) -> Dict:
    """根据输入的表名列表，返回这些表之间的关系。
    - 支持中文表名或表代码；会用 tables.json 规范化为中文表名。
    - 从 relations.json 中匹配无方向的两两关系并返回。

    Args:
        table_names: 表名列表，例如 ["A", "B", "C"]

    Returns:
        {"relations": [ {source, target, relation, join_key}, ... ] } 或 None
    """
    if not table_names:
        return {"relations": []}

    relations_path = Path("/home/wangling/projects/agents_herd/data_2/relations.json")
    tables_cfg_path = Path("/home/wangling/projects/agents_herd/data_2/tables.json")
    if not relations_path.exists():
        return None

    # 构建代码->中文名映射，便于将输入转换成 relations.json 使用的中文表名
    code_to_name: Dict[str, str] = {}
    name_to_name: Dict[str, str] = {}
    if tables_cfg_path.exists():
        try:
            cfg = json.load(tables_cfg_path.open(encoding="utf-8"))
            for item in cfg.get("tables", []):
                tn = item.get("table_name")
                code = item.get("table")
                if tn:
                    name_to_name[str(tn)] = str(tn)
                if code and tn:
                    code_to_name[str(code)] = str(tn)
        except Exception:
            # 如果解析失败，直接使用原始输入名
            pass

    def canon(n: str) -> str:
        return code_to_name.get(n, name_to_name.get(n, n))

    canon_names = [canon(n) for n in table_names]

    # 生成两两组合键，用于无方向匹配
    pair_keys = set()
    for i in range(len(canon_names)):
        for j in range(i + 1, len(canon_names)):
            pair_keys.add(frozenset({canon_names[i], canon_names[j]}))

    # 加载并过滤 relations
    rels_all = json.load(relations_path.open(encoding="utf-8")).get("relation", [])
    result = []
    for r in rels_all:
        s = str(r.get("source"))
        t = str(r.get("target"))
        if frozenset({s, t}) in pair_keys:
            result.append({
                "source": s,
                "target": t,
                "relation": r.get("relation"),
                "join_key": r.get("join_key"),
            })

    return {"relations": result}

def search_database(tables: List[str], query: str):
    # Step 1: 获取每个表的数据库信息
    table_info = [get_table_and_db_path_and_schema(t) for t in tables]
    if None in table_info:
        missing = [t for t, info in zip(tables, table_info) if info is None]
        return {"error": f"表未注册: {missing}"}

    # Step 2: 检查是否为同一个数据库
    db_paths = set(info["db_path"] for info in table_info)
    if len(db_paths) > 1:
        return {"error": f"不能跨数据库查询: {list(db_paths)}。跨系统的数据建议根据其关联关系分步查询。"}

    schema_text = "\n\n".join([info["schema"] for info in table_info])
    # 聚合所有字段用于后续标识符引号处理
    all_fields = []
    for info in table_info:
        fs = info.get("fields", [])
        if isinstance(fs, list):
            all_fields.extend(fs)

    table_relations = get_table_relations(tables)
    if table_relations is None:
        return {"error": "无法获取表关系"}
    
    system_prompt = f"""你是一个SQL专家，根据数据表之间的schema、表关系和用户的查询描述，生成符合要求的SQL查询。
    数据库结构如下:\n{schema_text}
    表关系如下:\n{table_relations}
    
    注意：
    - db中的表是以表代码为名称的，而不是中文表名。表代码与表名称不一定一致，以表代码为查询条件。
    - 如果字段名包含中文、空格或括号等特殊字符，请使用双引号包裹列名和表名，例如 "实际交货数量(库存单位)"。

    要求:
    - 不能生成除了SQL查询以外的任何内容。
    """

    print(system_prompt)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"根据以下查询描述生成SQL查询: {query}"}
    ]
    response = get_llm_response_gpt_4o(messages)
    sql = response.strip()
    
    sql = clean_sql_response(sql)
    # 为包含括号、中文或特殊字符的列名加双引号，避免SQLite解析错误
    sql = quote_sql_identifiers(sql, all_fields)
    print(sql)
    # Step 4: 执行 SQL
    db_path = table_info[0]["db_path"]
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        conn.close()
    except Exception as e:
        return {"error": str(e), "sql": sql}

    return {
        "sql": sql,
        "result": [dict(zip(cols, r)) for r in rows]
    }

if __name__ == "__main__":
    
     # 示例：使用配置中存在的中文表名进行测试
    # result = get_table_and_db_path_and_schema("销售订单")
    # print(result)
    
    # tables = ["合同", "销售订单"]
    # query = "杭州吉高智能电子科技有限公司的合同的订单号"

    tables = ["合同", "销售订单"]
    query = "查询合同编号为SCJSD20231226-SCGLB01的销售订单状态和生效时间"
    result = search_database(tables, query)
    print(result)

 