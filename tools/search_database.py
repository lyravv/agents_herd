

from typing import List, Dict
import sqlite3  
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

client = OpenAI(
    api_key=os.getenv("TOKEN", ""),
    base_url=os.getenv("BASE_URL", "https://api.apiyi.com/v1"),
)

def get_table_schema(conn, table_name: str):
    """从数据库提取表结构"""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    fields = [row[1] for row in cursor.fetchall()]
    return fields

def get_db_path_and_schema(table_name: str) -> Dict:
    """
    根据表名返回数据库路径和schema。
    这里你可以自己实现逻辑，比如从表注册中心或配置文件获取。
    """
    # 示例映射
    registry = {
        "sales_order": {"db_path": "/data/erp.db"},
        "customer_info": {"db_path": "/data/erp.db"},
        "supplier_list": {"db_path": "/data/srm.db"}
    }
    db_path = registry[table_name]["db_path"]
    conn = sqlite3.connect(db_path)
    schema_text = f"{get_table_schema(conn, table_name)}"
    conn.close()
    return {"db_path": db_path, "schema": schema_text}

def search_database(tables: List[str], query: str):
    # Step 1: 获取每个表的数据库信息
    table_info = [get_db_path_and_schema(t) for t in tables]
    if None in table_info:
        missing = [t for t, info in zip(tables, table_info) if info is None]
        return {"error": f"表未注册: {missing}"}

    # Step 2: 检查是否为同一个数据库
    db_paths = set(info["db_path"] for info in table_info)
    if len(db_paths) > 1:
        return {"error": f"不能跨数据库查询: {list(db_paths)}"}

    schema_text = "\n\n".join([info["schema"] for info in table_info])
    
    messages = [
        {"role": "system", "content": f"你是一个SQL专家，数据库结构如下:\n{schema_text}"},
        {"role": "user", "content": f"根据以下查询描述生成SQL查询: {query}"}
    ]
    response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            messages=messages,
            tools=tools,  # 注意：标准 OpenAI 工具格式是 {"type": "function", "function": {...}}，这里假设该 API 支持自定义工具
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            max_tokens=int(os.getenv("MAX_TOKENS", 2000)),
        )
    sql = response.choices[0].message.content

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
    tables = ["sales_order", "customer_info"]
    query = "查询所有客户的订单"
    result = search_database(tables, query)
    print(result)