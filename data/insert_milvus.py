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

# 读取JSON文件
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

# 写入JSON文件
def write_json_file(data):
    os.makedirs(os.path.dirname(JSON_FILE_PATH), exist_ok=True)
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {JSON_FILE_PATH}")

JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), 'table_ontology', 'tables.json')

def connect_to_milvus():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print("Connected to Milvus")

def create_collection(dim=1024):
    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME} already exists.")
        return Collection(name=COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="table_name", dtype=DataType.VARCHAR, max_length=256),  # 表名
        FieldSchema(name="table_description", dtype=DataType.VARCHAR, max_length=65535),  # 表描述
        FieldSchema(name="headers_description", dtype=DataType.VARCHAR, max_length=65535),  # 表头描述
        FieldSchema(name="example", dtype=DataType.VARCHAR, max_length=65535),  # 示例数据
        FieldSchema(name="table_name_embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),  # 表名向量
        FieldSchema(name="table_description_embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)  # 表描述向量
    ]
    schema = CollectionSchema(fields, description="Table Headers Collection")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    
    index_params = {
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
        "metric_type": "L2"
    }
    collection.create_index(field_name="table_name_embedding", index_params=index_params)
    collection.create_index(field_name="table_description_embedding", index_params=index_params)
    
    print(f"Collection {COLLECTION_NAME} created with indexes.")
    return collection

def get_embedding(text):
    payload = {"texts": [text]}
    response = requests.post(EMBEDDING_SERVICE_URL, json=payload)
    if response.status_code == 200:
        # API返回的是一个embedding列表，我们取第一个
        return response.json()[0]
    else:
        raise Exception(f"Embedding service error: {response.text}")

def read_json_file():
    if not os.path.exists(JSON_FILE_PATH):
        os.makedirs(os.path.dirname(JSON_FILE_PATH), exist_ok=True)
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"tables": []}, f, ensure_ascii=False, indent=2)
        return {"tables": []}
    
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def insert_data(collection, data_list):
    if not data_list:
        print("No data to insert")
        return
    
    table_names = []
    table_descriptions = []
    headers_descriptions = []
    examples = []
    table_name_embeddings = []
    table_description_embeddings = []
    
    for data in data_list:
        table_names.append(data["table_name"])
        table_descriptions.append(data["table_description"])
        headers_descriptions.append(data["headers_description"])
        examples.append(data["example"])
        
        table_name_embeddings.append(get_embedding(data["table_name"]))
        table_description_embeddings.append(get_embedding(data["table_description"]))
    
    entities = [
        table_names,
        table_descriptions,
        headers_descriptions,
        examples,
        table_name_embeddings,
        table_description_embeddings
    ]
    
    collection.insert(entities)
    print(f"Inserted {len(data_list)} records into collection {COLLECTION_NAME}")
    
    
def vector_search(collection, query_text, field="table_name", top_k=5):
    query_embedding = get_embedding(query_text)
    collection.load()
    
    if field == "table_name":
        vector_field = "table_name_embedding"
    elif field == "table_description":
        vector_field = "table_description_embedding"
    else:
        raise ValueError("Invalid field for vector search. Use 'table_name' or 'table_description'")
    
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    results = collection.search(
        data=[query_embedding],
        anns_field=vector_field,
        param=search_params,
        limit=top_k,
        output_fields=["table_name", "table_description", "headers_description", "example"]
    )
    
    return results[0]

def keyword_search(collection, keyword):
    collection.load()
    
    expr = f'headers_description like "%{keyword}%"'
    results = collection.query(
        expr=expr,
        output_fields=["table_name", "table_description", "headers_description", "example"]
    )
    
    return results

def drop_collection():
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)
        print(f"Collection {COLLECTION_NAME} dropped.")

def main():
    connect_to_milvus()
    drop_collection()
    collection = create_collection()

    # 读取并插入数据
    data_list = read_json_file().get("tables", [])
    insert_data(collection, data_list)

    # 示例查询 - 向量查询表名
    query_table_name = "销售"
    print("\n使用表名进行向量搜索的结果:")
    results = vector_search(collection, query_table_name, field="table_name", top_k=3)
    for i, hit in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"距离: {hit.distance}")
        print(f"表名: {hit.entity.get('table_name')}")
        print(f"表描述: {hit.entity.get('table_description')}")
        print("-" * 50)

    # 示例查询 - 向量查询表描述
    query_description = "发货信息"
    print("\n使用表描述进行向量搜索的结果:")
    results = vector_search(collection, query_description, field="table_description", top_k=3)
    for i, hit in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"距离: {hit.distance}")
        print(f"表名: {hit.entity.get('table_name')}")
        print(f"表描述: {hit.entity.get('table_description')}")
        print("-" * 50)

    # 示例查询 - 关键词查询表头描述
    keyword = "订单"
    print(f"\n使用关键词 '{keyword}' 查询表头描述的结果:")
    results = keyword_search(collection, keyword)
    for i, result in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"表名: {result['table_name']}")
        print(f"表描述: {result['table_description']}")
        print(f"表头描述: {result['headers_description']}")
        print("-" * 50)

    print("\n查询结果包含完整数据，包括表名、表描述、表头描述和示例数据")

if __name__ == "__main__":
    main()
