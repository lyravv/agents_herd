import os
import re
import requests
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# 配置参数
MILVUS_URI = "http://10.50.56.243:19530"
DB_NAME = "default"
COLLECTION_NAME = "wangling_tables_header"
EMBEDDING_SERVICE_URL = "http://10.50.60.21:12345/embed"

# 连接 Milvus
def connect_to_milvus():
    connections.connect(host='10.50.56.243', port='19530')
    print("Connected to Milvus")

# 创建 Collection
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
    
    # 创建索引
    index_params = {
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
        "metric_type": "L2"
    }
    collection.create_index(field_name="table_name_embedding", index_params=index_params)
    collection.create_index(field_name="table_description_embedding", index_params=index_params)
    
    print(f"Collection {COLLECTION_NAME} created with indexes.")
    return collection

# 获取 Embedding
def get_embedding(text):
    payload = {"texts": [text]}
    response = requests.post(EMBEDDING_SERVICE_URL, json=payload)
    if response.status_code == 200:
        # API返回的是一个embedding列表，我们取第一个
        return response.json()[0]
    else:
        raise Exception(f"Embedding service error: {response.text}")

# 读取 Markdown 文件
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

# 读取目录下所有Markdown文件
def read_all_markdown_files(directory_path):
    data_list = []
    for filename in os.listdir(directory_path):
        if filename.endswith('.md'):
            file_path = os.path.join(directory_path, filename)
            data = read_markdown_file(file_path)
            data_list.append(data)
    return data_list

# 插入数据到 Milvus
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
        
        # 生成表名和表描述的嵌入向量
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

# 向量查询（表名或表描述）
def vector_search(collection, query_text, field="table_name", top_k=5):
    query_embedding = get_embedding(query_text)
    collection.load()
    
    # 根据查询字段选择对应的向量字段
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

# 关键词查询（表头描述）
def keyword_search(collection, keyword):
    collection.load()
    
    # 使用字符串匹配查询
    expr = f'headers_description like "%{keyword}%"'
    results = collection.query(
        expr=expr,
        output_fields=["table_name", "table_description", "headers_description", "example"]
    )
    
    return results

# 删除集合
def drop_collection():
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)
        print(f"Collection {COLLECTION_NAME} dropped.")

# 主函数
def main():
    table_headers_dir = "/home/wangling/projects/agents_herd/data/table_headers"  # 表头数据目录
    connect_to_milvus()
    drop_collection()  # 先删除现有集合
    collection = create_collection()

    # Step 1: 读取并插入数据
    data_list = read_all_markdown_files(table_headers_dir)
    insert_data(collection, data_list)

    # Step 2: 示例查询 - 向量查询表名
    query_table_name = "销售"
    print("\n使用表名进行向量搜索的结果:")
    results = vector_search(collection, query_table_name, field="table_name", top_k=3)
    for i, hit in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"距离: {hit.distance}")
        print(f"表名: {hit.entity.get('table_name')}")
        print(f"表描述: {hit.entity.get('table_description')}")
        print("-" * 50)

    # Step 3: 示例查询 - 向量查询表描述
    query_description = "发货信息"
    print("\n使用表描述进行向量搜索的结果:")
    results = vector_search(collection, query_description, field="table_description", top_k=3)
    for i, hit in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"距离: {hit.distance}")
        print(f"表名: {hit.entity.get('table_name')}")
        print(f"表描述: {hit.entity.get('table_description')}")
        print("-" * 50)

    # Step 4: 示例查询 - 关键词查询表头描述
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
