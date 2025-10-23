import requests
import json
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def get_llm_response_gpt_4o(system_prompt, user_prompt):
    LLM_URL = os.getenv("BASE_URL", "https://api.apiyi.com/v1") + "/chat/completions"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('TOKEN', '')}"
    }
    payload = {
        "model": os.getenv("MODEL_NAME", "gpt-4o"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": float(os.getenv("TEMPERATURE", 0.7)),
        "max_tokens": int(os.getenv("MAX_TOKENS", 2000))
    }
    try:
        response = requests.post(LLM_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"LLM调用失败: {response.status_code} - {response.text}"
    except Exception as e:
        return f"LLM调用异常: {str(e)}"

def get_llm_response_with_function_call(messages, functions=None):
    """使用function call功能的LLM调用"""
    LLM_URL = os.getenv("BASE_URL", "https://api.apiyi.com/v1/chat/completions")
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
        print(f"LLM请求 payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        response = requests.post(LLM_URL, headers=HEADERS, json=payload)
        print(f"LLM响应: {response.status_code} - {response.text}")
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

# def get_llm_response_with_mcp_tools():

# def get_llm_response_with_function_call(messages, functions=None):




if __name__ == "__main__":
    system_prompt = "你是一个专业的法律问答助手"
    user_prompt = "法律问题：什么是合同？"
    response = get_llm_response_gpt_4o(system_prompt, user_prompt)
    print(response)