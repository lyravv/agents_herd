import datetime
def get_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_weekday():
    re =  datetime.datetime.now().weekday()
    if re == 0:
        return "星期一"
    elif re == 1:
        return "星期二"
    elif re == 2:
        return "星期三"
    elif re == 3:
        return "星期四"
    elif re == 4:
        return "星期五"
    elif re == 5:
        return "星期六"
    elif re == 6:
        return "星期日"

def clean_json_response(response):
    """清理LLM响应中的markdown代码块标记"""
    if not response:
        return '{}'
    
    # 移除开头的```json标记
    if response.strip().startswith('```json'):
        response = response.strip()[7:]
    elif response.strip().startswith('```'):
        response = response.strip()[3:]
    
    # 移除结尾的```标记
    if response.strip().endswith('```'):
        response = response.strip()[:-3]
    
    cleaned = response.strip()
    # 如果清理后的响应为空，返回空的JSON对象
    if not cleaned:
        return '{}'
    
    return cleaned

def clean_sql_response(response):
    """清理LLM响应中的markdown代码块标记"""
    if not response:
        return ''
    
    # 移除开头的```sql标记
    if response.strip().startswith('```sql'):
        response = response.strip()[6:]
    elif response.strip().startswith('```'):
        response = response.strip()[3:]
    
    # 移除结尾的```标记
    if response.strip().endswith('```'):
        response = response.strip()[:-3]
    
    cleaned = response.strip()
    # 如果清理后的响应为空，返回空字符串
    if not cleaned:
        return ''
    
    return cleaned  

def quote_sql_identifiers(sql: str, fields: list[str]) -> str:
    """
    为包含非字母数字字符（如中文、空格、括号等）的列名自动加上双引号，以兼容SQLite等数据库。

    简化策略：
    - 对传入的所有字段名，在SQL中出现且未被双引号包裹时，统一替换为双引号包裹的形式。
    - 避免替换已经被双引号包裹的内容。
    - 不处理单引号中的字符串常量（通常不会包含列名）。

    说明：
    - 该方法是字符串级的健壮化处理，无法覆盖所有SQL语法细节，但对当前包含括号、中文列名的场景足够。
    """
    if not sql or not fields:
        return sql

    try:
        import re

        # 先粗略保护单引号中的字符串，避免误替换
        # 将其替换为占位符，并在最后再还原
        str_literals = []
        def _str_replacer(m):
            str_literals.append(m.group(0))
            return f"__STR_LIT_{len(str_literals)-1}__"

        protected_sql = re.sub(r"'(?:''|[^'])*'", _str_replacer, sql)

        # 针对每个字段做未加引号的替换
        for fld in sorted(set(fields), key=len, reverse=True):
            if not fld:
                continue
            # 跳过已经是双引号包裹的情况
            # 使用负向环视确保不在双引号内，且尽量按边界替换
            # 注意：中文环境下\b边界不可靠，这里使用非引号前后限定。
            pattern = rf'(?<!\"){re.escape(fld)}(?!\")'
            protected_sql = re.sub(pattern, f'"{fld}"', protected_sql)

        # 还原字符串常量
        def _restore(m):
            idx = int(m.group(1))
            return str_literals[idx]
        protected_sql = re.sub(r"__STR_LIT_(\d+)__", _restore, protected_sql)

        return protected_sql
    except Exception:
        # 发生异常则返回原始SQL，避免影响执行
        return sql