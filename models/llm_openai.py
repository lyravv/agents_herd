from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

client = OpenAI(
    api_key=os.getenv("TOKEN", ""),
    base_url=os.getenv("BASE_URL", "https://api.apiyi.com/v1"),
)

# 构造消息和工具
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


# 看起来不起作用

"""
python models/llm_openai.py 
Full Response:
ChatCompletion(id='chatcmpl-CTjBRHcsZIp6irTAENHpKbnQ0OrYY', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='截至我最近的更新，中英伟达的实时股价信息可能会有所变化。要获取最新的股价信息，建议您访问金融新闻网站或使用股票交易应用程序，如雅虎财经、谷歌财经或彭博终端等。这些平台提供最新的股价和市场信息。', refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=None))], created=1761201233, model='gpt-4o-2024-08-06', object='chat.completion', service_tier=None, system_fingerprint='fp_4a331a0222', usage=CompletionUsage(completion_tokens=67, prompt_tokens=14, total_tokens=81, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
Assistant Reply: 截至我最近的更新，中英伟达的实时股价信息可能会有所变化。要获取最新的股价信息，建议您访问金融新闻网站或使用股票交易应用程序，如雅虎财经、谷歌财经或彭博终端等。这些平台提供最新的股价和市场信息。
"""