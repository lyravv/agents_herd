#!/usr/bin/env python3
import os
import argparse
import requests
from pymilvus import connections, Collection, utility
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
MILVUS_HOST = os.getenv('MILVUS_HOST', '127.0.0.1')
MILVUS_PORT = os.getenv('MILVUS_PORT', '19530')
COLLECTION_NAME = os.getenv('MILVUS_COLLECTION_NAME', 'test')
EMBEDDING_SERVICE_URL = os.getenv('EMBEDDING_SERVICE_URL', 'http://127.0.0.1:12345/embed')

# 连接 Milvus
def connect_to_milvus():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print("Connected to Milvus")
    
    if not utility.has_collection(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME} does not exist. Please run register_table_header.py first.")
        return None
    
    return Collection(name=COLLECTION_NAME)

# 获取 Embedding
def get_embedding(text):
    payload = {"texts": [text]}
    response = requests.post(EMBEDDING_SERVICE_URL, json=payload)
    if response.status_code == 200:
        # API返回的是一个embedding列表，我们取第一个
        return response.json()[0]
    else:
        raise Exception(f"Embedding service error: {response.text}")

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

# 关键词查询（支持所有文本字段）
def keyword_search(collection, keyword, field="headers_description"):
    collection.load()
    
    # 确保字段名有效
    valid_fields = ["table_name", "table_description", "headers_description", "example"]
    if field not in valid_fields:
        raise ValueError(f"Invalid field for keyword search. Use one of {valid_fields}")
    
    # 使用字符串匹配查询
    expr = f'{field} like "%{keyword}%"'
    results = collection.query(
        expr=expr,
        output_fields=["table_name", "table_description", "headers_description", "example"]
    )
    
    return results

# 打印查询结果
def print_results(results, query_type="vector"):
    if not results:
        print("No results found.")
        return
    
    print(f"\n找到 {len(results)} 条结果:")
    print("=" * 80)
    
    if query_type == "vector":
        # 向量查询结果
        for i, hit in enumerate(results):
            print(f"结果 {i+1}:")
            print(f"相似度得分: {1 - hit.distance:.4f}")  # 转换距离为相似度得分
            print(f"表名: {hit.entity.get('table_name')}")
            print(f"表描述: {hit.entity.get('table_description')}")
            print(f"表头描述: {hit.entity.get('headers_description')}")
            print(f"示例数据: {hit.entity.get('example')}")
            print("-" * 80)
    else:
        # 关键词查询结果
        for i, result in enumerate(results):
            print(f"结果 {i+1}:")
            print(f"表名: {result['table_name']}")
            print(f"表描述: {result['table_description']}")
            print(f"表头描述: {result['headers_description']}")
            print(f"示例数据: {result['example']}")
            print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description='表格数据查询工具')
    parser.add_argument('--query', '-q', type=str, required=True, help='查询文本')
    parser.add_argument('--mode', '-m', type=str, default='vector', choices=['vector', 'keyword'], 
                        help='查询模式: vector(向量查询) 或 keyword(关键词查询)')
    parser.add_argument('--field', '-f', type=str, default='table_name', 
                        help='查询字段: table_name, table_description, headers_description, example')
    parser.add_argument('--top_k', '-k', type=int, default=3, help='返回结果数量 (仅向量查询)')
    
    args = parser.parse_args()
    
    # 连接到Milvus
    collection = connect_to_milvus()
    if collection is None:
        return
    
    try:
        if args.mode == 'vector':
            # 向量查询模式
            if args.field not in ['table_name', 'table_description']:
                print(f"向量查询只支持 'table_name' 或 'table_description' 字段，您指定的是 '{args.field}'")
                print("自动切换到 'table_name' 字段进行查询")
                args.field = 'table_name'
                
            print(f"执行向量查询: 字段={args.field}, 查询文本='{args.query}', top_k={args.top_k}")
            results = vector_search(collection, args.query, args.field, args.top_k)
            print(f"向量查询结果: {results}")
            print_results(results, "vector")
        else:
            # 关键词查询模式
            print(f"执行关键词查询: 字段={args.field}, 关键词='{args.query}'")
            results = keyword_search(collection, args.query, args.field)
            print(f"关键词查询结果: {results}")
            print_results(results, "keyword")
    
    except Exception as e:
        print(f"查询出错: {str(e)}")

if __name__ == "__main__":
    main()