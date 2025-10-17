

import os
import json
import pandas as pd
from models.llm import get_llm_response_with_function_call

def sales_contract_search(query: str) -> dict:
    """
    搜索销售合同信息

    :param query: 搜索查询字符串
    :return: 销售合同信息字典
    """
    # 读取销售合同CSV文件
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "data/table_headers/sales_contract.csv")
    
    # 定义查询销售合同的函数
    functions = [
        {
            "name": "query_sales_contract",
            "description": "根据查询条件搜索销售合同信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "string",
                        "description": "销售合同编号"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "客户名称"
                    },
                    "status": {
                        "type": "string",
                        "description": "合同状态，如active、pending、expired"
                    },
                    "sign_date_start": {
                        "type": "string",
                        "description": "签约日期范围开始，格式为YYYY-MM-DD"
                    },
                    "sign_date_end": {
                        "type": "string",
                        "description": "签约日期范围结束，格式为YYYY-MM-DD"
                    },
                    "total_amount_min": {
                        "type": "number",
                        "description": "最小销售金额"
                    },
                    "total_amount_max": {
                        "type": "number",
                        "description": "最大销售金额"
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "排序字段，如contract_id、customer_name、total_amount、sign_date等"
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "排序方式，asc（升序）或desc（降序）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制"
                    }
                },
                "required": []
            }
        }
    ]
    
    # 构建消息
    messages = [
        {"role": "system", "content": "你是一个专业的销售合同查询助手，可以根据用户的查询条件查找销售合同信息。当前日期是2025-11-20"},
        {"role": "user", "content": f"请帮我查询以下销售合同信息：{query}"}
    ]
    
    # 调用LLM获取查询条件
    response = get_llm_response_with_function_call(messages, functions)
    
    # 处理LLM响应
    if response and "function_call" in response and response["function_call"]:
        # 解析查询参数
        function_args = json.loads(response["function_call"]["arguments"])
        
        # 读取CSV文件
        df = pd.read_csv(csv_path)
        
        # 根据查询条件过滤数据
        filtered_df = df.copy()
        
        # 处理普通文本字段查询
        for key, value in function_args.items():
            if value and key in df.columns:
                filtered_df = filtered_df[filtered_df[key].astype(str).str.contains(value, case=False)]
        
        # 处理日期范围查询
        if "sign_date_start" in function_args and function_args["sign_date_start"]:
            filtered_df = filtered_df[filtered_df["sign_date"] >= function_args["sign_date_start"]]
        
        if "sign_date_end" in function_args and function_args["sign_date_end"]:
            filtered_df = filtered_df[filtered_df["sign_date"] <= function_args["sign_date_end"]]
        
        # 处理金额范围查询
        if "total_amount_min" in function_args and function_args["total_amount_min"] is not None:
            filtered_df = filtered_df[filtered_df["total_amount"].astype(float) >= float(function_args["total_amount_min"])]
        
        if "total_amount_max" in function_args and function_args["total_amount_max"] is not None:
            filtered_df = filtered_df[filtered_df["total_amount"].astype(float) <= float(function_args["total_amount_max"])]
        
        # 处理排序
        if "sort_by" in function_args and function_args["sort_by"]:
            sort_field = function_args["sort_by"]
            if sort_field in df.columns:
                # 默认升序
                ascending = True
                if "sort_order" in function_args and function_args["sort_order"] and function_args["sort_order"].lower() == "desc":
                    ascending = False
                
                # 对数值型字段进行类型转换后排序
                if sort_field == "total_amount":
                    filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending, key=lambda x: x.astype(float))
                else:
                    filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending)
        
        # 处理结果数量限制
        if "limit" in function_args and function_args["limit"] is not None:
            limit = int(function_args["limit"])
            if limit > 0:
                filtered_df = filtered_df.head(limit)
        
        # 转换为字典列表
        if not filtered_df.empty:
            result = filtered_df.to_dict(orient='records')
            return {"status": "success", "data": result}
        else:
            return {"status": "not_found", "message": "未找到匹配的销售合同信息"}
    else:
        return {"status": "error", "message": "LLM查询处理失败"}

    return {}


if __name__ == "__main__":
    query = "合同额最大的3个合同"
    result = sales_contract_search(query)
    print(result)