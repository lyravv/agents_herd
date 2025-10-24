from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

client = OpenAI(
    api_key=os.getenv("TOKEN", ""),
    base_url=os.getenv("BASE_URL", "https://api.apiyi.com/v1"),
)

def case1():
    messages = [
        {"role": "user", "content": "英伟达当前的股价"},
        {
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "call_web_search_001",
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": '{"query": "英伟达股价"}'
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_web_search_001",
            "content": "英伟达当前的股价是120美元"
        }
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
        }
    ]

    # 调用 API
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            messages=messages,
            tools=tools,  # 注意：标准 OpenAI 工具格式是 {"type": "function", "function": {...}}，这里假设该 API 支持自定义工具
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            max_tokens=int(os.getenv("MAX_TOKENS", 2000)),
        )

        print("Full Response:")
        print(response)

        # 提取回答内容
        if response.choices:
            message = response.choices[0].message
            if message.content:
                print("Assistant Reply:", message.content)
            else:
                print("Tool call or empty content.")
                print("Message:", message)

    except Exception as e:
        print(f"Error: {e}")


"""
python models/llm_openai.py 
Full Response:
ChatCompletion(id='chatcmpl-CTjBRHcsZIp6irTAENHpKbnQ0OrYY', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='截至我最近的更新，中英伟达的实时股价信息可能会有所变化。要获取最新的股价信息，建议您访问金融新闻网站或使用股票交易应用程序，如雅虎财经、谷歌财经或彭博终端等。这些平台提供最新的股价和市场信息。', refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=None))], created=1761201233, model='gpt-4o-2024-08-06', object='chat.completion', service_tier=None, system_fingerprint='fp_4a331a0222', usage=CompletionUsage(completion_tokens=67, prompt_tokens=14, total_tokens=81, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
Assistant Reply: 截至我最近的更新，中英伟达的实时股价信息可能会有所变化。要获取最新的股价信息，建议您访问金融新闻网站或使用股票交易应用程序，如雅虎财经、谷歌财经或彭博终端等。这些平台提供最新的股价和市场信息。
"""

def case2():
    retrive_graph = """
    {
    "nodes": [
        {
        "id": "tool_1",
        "label": "sales_contract_tool",
        "type": "Tool"
        },
        {
        "id": "action_1",
        "label": "查询",
        "type": "Action"
        },
        {
        "id": "table_1",
        "label": "销售合同表",
        "type": "DataEntity"
        }
    ],
    "edges": [
        {
        "source": "tool_1",
        "target": "action_1",
        "relation": "performs"
        },
        {
        "source": "action_1",
        "target": "table_1",
        "relation": "operates_on"
        }
    ]
    }
    """

    input = """
    用户问题：
    {{今年合同额大于100w的有合同总额是多少}}
    参考经验：
    {{
        "experience_nl": {{
            "title": "合同查询相关问题",
            "answer": "合同相关信息存放于"销售合同表"中，使用"sales_contract_tool"可以查询相关合同情况"
        }},
        "related_graph": {retrive_graph}
    }}
    """.format(retrive_graph=retrive_graph)

    todo_list = """
    [] 使用sales_contract_tool查询今年合同额大于100w的合同
    [] 使用sum_with_nl_tool计算这些合同的合同额总和
    """
    think_result = """
        {{
            "think_process":"根据用户问题，需要先查询今年合同额大于100w的合同，然后计算这些合同的合同额总和",
            "todo_list":{todo_list}
        }}
    """.format(todo_list=todo_list)

    retrive_content = """
    contract_id,customer_name,total_amount,sign_date,status,version,is_active
    SC20250301,北京智控科技,1200000.00,2025-03-01,active,1,TRUE
    SC20250502,上海数联信息,1750000.00,2025-05-05,active,1,TRUE
    SC20250503,广州科创电子,3200000.00,2025-05-10,pending,1,FALSE
    """
    
    messages = [
        {"role": "system", "content": "你是一个工具调用专家。通过链式的工具调用和观察工具调用的结果，最终回答用户的问题。当你觉得有足够信息回答用户问题时候，直接回答用户问题，不需要再调用工具。"},
        {"role": "user", "content": input},
        {
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "call_think_tool_001",
                    "type": "function",
                    "function": {
                        "name": "think_tool",
                        "arguments": "think时候会查看整个history"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_think_tool_001",
            "content": think_result
        },
        {
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "call_sales_contract_tool_001",
                    "type": "function",
                    "function": {
                        "name": "sales_contract_tool",
                        "arguments": "今年合同额大于100w的合同"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_sales_contract_tool_001",
            "content": retrive_content
        },
        {
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "call_sum_with_nl_tool_001",
                    "type": "function",
                    "function": {
                        "name": "sum_with_nl_tool",
                        "arguments": retrive_content
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_sum_with_nl_tool_001",
            "content": "6150000"
        }
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
    # 调用 API
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            messages=messages,
            tools=tools,  # 注意：标准 OpenAI 工具格式是 {"type": "function", "function": {...}}，这里假设该 API 支持自定义工具
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            max_tokens=int(os.getenv("MAX_TOKENS", 2000)),
        )

        print("Full Response:")
        print(response)

        # 提取回答内容
        if response.choices:
            message = response.choices[0].message
            if message.content:
                print("Assistant Reply:", message.content)
            else:
                print("Tool call or empty content.")
                print("Message:", message)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # case1()
    case2()