import os
import re
import json
import requests
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
MILVUS_HOST = os.getenv('MILVUS_HOST', '127.0.0.1')
MILVUS_PORT = os.getenv('MILVUS_PORT', '19530')
COLLECTION_NAME = os.getenv('MILVUS_COLLECTION_NAME', 'test')
EMBEDDING_SERVICE_URL = os.getenv('EMBEDDING_SERVICE_URL', 'http://127.0.0.1:12345/embed')

# JSON文件路径
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), 'table_ontology', 'tables.json')


def read_json_file():
    if not os.path.exists(JSON_FILE_PATH):
        # 如果JSON文件不存在，创建一个空的JSON文件
        os.makedirs(os.path.dirname(JSON_FILE_PATH), exist_ok=True)
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"tables": []}, f, ensure_ascii=False, indent=2)
        return {"tables": []}
    
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:  # 文件为空
                return {"tables": []}
            return json.loads(content)
    except json.JSONDecodeError:
        # JSON解析错误，返回空结构
        return {"tables": []}

def write_json_file(data):
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式提取各部分内容
    table_name_match = re.search(r'# table name\s+(.*?)(?=\s+#|\s*$)', content, re.DOTALL)
    table_description_match = re.search(r'# table description\s+(.*?)(?=\s+#|\s*$)', content, re.DOTALL)
    headers_description_match = re.search(r'# headers description\s+(.*?)(?=\s+#|\s*$)', content, re.DOTALL)
    example_match = re.search(r'# example\s+(.*?)(?=\s+#|\s*$)', content, re.DOTALL)
    
    table_name = table_name_match.group(1).strip() if table_name_match else ""
    table_description = table_description_match.group(1).strip() if table_description_match else ""
    headers_description = headers_description_match.group(1).strip() if headers_description_match else ""
    example = example_match.group(1).strip() if example_match else ""
    
    return {
        "table_name": table_name,
        "table_description": table_description,
        "headers_description": headers_description,
        "example": example
    }

def register_to_json(data_list):
    # 读取JSON文件
    json_data = read_json_file()
    
    for data in data_list:
        # 检查是否已存在相同表名的表
        existing_table = next((table for table in json_data["tables"] if table["table_name"] == data["table_name"]), None)
        if existing_table:
            # 如果存在，更新表信息
            existing_table.update(data)
        else:
            # 如果不存在，添加新表
            json_data["tables"].append(data)
    
    # 保存更新后的JSON数据
    write_json_file(json_data)


def read_all_markdown_files(directory):
    data_list = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            file_path = os.path.join(directory, filename)
            data = read_markdown_file(file_path)
            data_list.append(data)
    return data_list

if __name__ == "__main__":
    data_list = read_all_markdown_files('/home/wangling/projects/agents_herd/data/table_headers')
    register_to_json(data_list)