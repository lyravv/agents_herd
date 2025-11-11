import requests
import json
import os
from dotenv import load_dotenv, find_dotenv
from utils.logger import setup_logger

load_dotenv(find_dotenv())

# 初始化logger，统一通过utils.logger控制控制台开关
logger = setup_logger('llm', enable_console=False)

def get_llm_response_gpt_4o(messages):
    LLM_URL = os.getenv("BASE_URL", "https://api.apiyi.com/v1") + "/chat/completions"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('TOKEN', '')}"
    }
    payload = {
        "model": os.getenv("MODEL_NAME", "gpt-4o"),
        "messages": messages,
        "temperature": float(os.getenv("TEMPERATURE", 0.7)),
        "max_tokens": int(os.getenv("MAX_TOKENS", 2000))
    }
    try:
        logger.info(f"LLM请求 payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        response = requests.post(LLM_URL, headers=HEADERS, json=payload)
        logger.info(f"LLM响应: {response.status_code}")
        logger.info(f"LLM响应详情: {response.text}")
        if response.status_code == 200:
            result = response.json()
            logger.info("LLM API调用成功")
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"LLM调用失败: {response.status_code} - {response.text}")
            return f"LLM调用失败: {response.status_code} - {response.text}"
    except Exception as e:
        logger.exception(f"LLM调用异常: {str(e)}")
        return f"LLM调用异常: {str(e)}"

def get_llm_response_with_function_call(messages, functions=None):
    """使用function call功能的LLM调用"""
    LLM_URL = os.getenv("BASE_URL", "https://api.apiyi.com/v1") + "/chat/completions"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('TOKEN', '')}"
    }
    
    payload = {
        "model": os.getenv("MODEL_NAME", "gpt-4o"),
        "messages": messages,
        "temperature": float(os.getenv("TEMPERATURE", 0.1)),
        "max_tokens": int(os.getenv("MAX_TOKENS", 2000))
    }
    if functions:
        payload["functions"] = functions
        payload["function_call"] = "auto"
    
    try:
        logger.info(f"LLM请求 payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        response = requests.post(LLM_URL, headers=HEADERS, json=payload)
        logger.info(f"LLM响应: {response.status_code}")
        logger.info(f"LLM响应详情: {response.text}")
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']
        else:
            return {
                "content": f"LLM调用失败: {response.status_code} - {response.text}",
                "function_call": None
            }
    except Exception as e:
        return {
            "content": f"LLM调用异常: {str(e)}",
            "function_call": None
        }

def get_llm_response_gpt_4o_with_tools(messages, tools=None):
    """使用tools功能的LLM调用"""    
    LLM_URL = os.getenv("BASE_URL", "https://api.apiyi.com/v1") + "/chat/completions"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('TOKEN', '')}"
    }
    
    payload = {
        "model": os.getenv("MODEL_NAME", "gpt-4o"),
        "messages": messages,
        "temperature": float(os.getenv("TEMPERATURE", 0.1)),
        "max_tokens": int(os.getenv("MAX_TOKENS", 2000))
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    try:
        logger.info(f"LLM请求 payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        response = requests.post(LLM_URL, headers=HEADERS, json=payload)
        logger.info(f"LLM响应: {response.status_code}")
        logger.info(f"LLM响应详情: {response.text}")
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']
        else:
            return {
                "content": f"LLM调用失败: {response.status_code} - {response.text}",
                "tool_calls": None
            }
    except Exception as e:
        return {
            "content": f"LLM调用异常: {str(e)}",
            "tool_calls": None
        }




if __name__ == "__main__":
    # messages1 = [
    #     {"role": "system", "content":  "你是一个专业的法律问答助手"},
    #     {"role": "user", "content": "法律问题：什么是合同？"}
    # ]
    # response = get_llm_response_gpt_4o(messages1)
    # print(response)

    # messages2 = [
    #     {"role": "system", "content":  "你是一个专业的销售合同查询助手"},
    #     {"role": "user", "content": "合同编号为123456的合同是否有客户签名？"}
    # ]

    # functions = [
    #     {
    #         "name": "sales_contract_tool",
    #         "description": "用于查询销售合同信息",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "contract_id": {
    #                     "type": "string",
    #                     "description": "销售合同的唯一标识符"
    #                 }
    #             },
    #             "required": ["contract_id"]
    #         }
    #     }
    # ]
    # response = get_llm_response_with_function_call(messages2, functions)
    # print(f"完整响应: {response}")

    messages3 = [
        {"role": "system", "content":  "你是一个专业的销售合同查询助手"},
        {"role": "user", "content": "合同编号为123456的合同是否有客户签名？"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜索网络信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "think_tool",
                "description": "思考工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "think_process": {
                            "type": "string",
                            "description": "思考过程"
                        },
                        "todo_list": {
                            "type": "string",
                            "description": "待办事项列表"
                        }
                    },
                    "required": ["think_process", "todo_list"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sales_contract_tool",
                "description": "销售合同工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "销售合同查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sum_with_nl_tool",
                "description": "从文本中提取所有用于求和的数值，计算它们的总和。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "计算结果表达式"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
    
    response = get_llm_response_gpt_4o_with_tools(messages3, tools)
    # print(f"完整响应: {response}")