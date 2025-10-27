from mcp.types import Content
from utils.whiteboard import Whiteboard
from models.llm import get_llm_response_gpt_4o_with_tools
from graph.graph_match import graph_match
from memory.long_term_memory import experience_match
import json
import asyncio
from models import llm_openai
from tools.mcp_client import get_available_tools_async, convert_mcp_tool_to_openai, call_tool

master_agent_system_prompt = f"""
你是一个工具调用专家。系统通过whiteboard向你呈现有用的信息。白板上可能包含用户的输入问题，记忆系统相关的参考经验，图谱上相关的节点、边等信息。
你必须调用工具进行输出，你的输出也会被写到白板上。你可以调用think工具去思考，指定plan，也可以调用write工具去输出，这些工具也看得到白板上的信息。你还可以调用特定的一些工具完成一些任务，如获取数据，查询数据库，计算等等。

## 白板的字段解释
input_query: 用户的原始查询问题
experience_nld: 可能与用户查询问题相关的参考经验，自然语言描述
related_graph: 可能与用户查询问题相关业务相关节点图谱，展示查询路径中涉及的节点和关系
*_tool_results: 特定工具执行结果，展示查询路径中使用的工具和其输出结果
think_process: 之前的显示思考结果
plan: 之前的执行计划
output: 关于input_query输出给用户的结果
"""

master_agent_prompt = """
通过工具调用继续再whiteboard推演，直至解答出whiteboard上用户的input query。

## whiteboard
{whiteboard_str}
"""



class MasterAgent:
    def __init__(self, whiteboard: Whiteboard = None):
        # 如果没有传入whiteboard，使用全局共享实例
        self.whiteboard = whiteboard if whiteboard is not None else Whiteboard.get_instance()

    def llm_step(self) -> str:

        messages = self.whiteboard.read()
        print(f"messages: {messages}")
        mcp_tools = asyncio.run(get_available_tools_async())
        print(f"可用工具: {mcp_tools}")
        tools = [convert_mcp_tool_to_openai(tool.__dict__) for tool in mcp_tools]

        response = get_llm_response_gpt_4o_with_tools(messages, tools)
        print(f"LLM响应: {response}")
        return response

    def execute_tool_calls(self, response: dict) -> dict:
        tool_calls = response.get("tool_calls")
        tool_results = []

        if not tool_calls:
            return tool_results
        
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_id = tool_call["id"]
            tool_result = asyncio.run(call_tool(function_name, arguments))
            
            # 构建工具调用结果消息
            tool_call_result = {
                "role": "tool",
                "content": tool_result,
                "tool_call_id": tool_id
            }
            tool_results.append(tool_call_result)
        
        return tool_results
    
    def solve(self) -> str:
        turn = 0
        final_response = None
        while turn < 10:
            llm_result = self.llm_step()
            # 如果response不是工具调用，跳出循环
            if llm_result.get("role") == "assistant" and llm_result.get("content") is not None:
                final_response = llm_result
                break
            self.whiteboard.append(llm_result)
            tool_execution_results = self.execute_tool_calls(llm_result)
            print(f"工具调用结果: {tool_execution_results}")
            for result in tool_execution_results:
                self.whiteboard.append(result)
            turn += 1

        if final_response is None:
            return "我无法解决这个问题。"
        
        return final_response["content"]

if __name__ == "__main__":
    whiteboard = Whiteboard("test_board")
    whiteboard.clear()
    master_agent = MasterAgent(whiteboard)

    
    # while True:
    #     query = input("用户query: ")
    #     if query.lower() == "exit":
    #         break
        
    #     shared_whiteboard.user_input({"content": query})

    #     # 这里需要实现experience_match和graph_match函数
    #     experience = experience_match(query)
    #     graph = graph_match(query)
        
    #     if experience:
    #         shared_whiteboard.experience_nld({"content": experience})
    #     if graph:
    #         shared_whiteboard.related_graph({"content": graph})

    #     result = master_agent.solve()
    #     print(result)
    query = """这些订单的总金额是多少？
order_id,contract_id,order_amount,order_date,delivery_date,status
SO20251020,SC20251004,1100000.00,2025-10-20,2025-11-05,pending
SO20251030,SC20251006,650000.00,2025-10-30,2025-11-15,pending
SO20251110,SC20251008,820000.00,2025-11-10,2025-11-30,pending"""
    
    print(query)
    messages = [{"role": "user", "content": query}]
    whiteboard.append(messages[0])

    # 这里需要实现experience_match和graph_match函数
    # experience = experience_match(query)
    # graph = graph_match(query)
    
    # if experience or graph:
    #     faked_assistant_response = {
    #         "role": "assistant", 
    #         "content": None,
    #         "tool_calls": [
    #             {
    #                 "id": "retrieve_experience_001",
    #                 "type": "function",
    #                 "function": {
    #                     "name": "retrieve_experience_tool",
    #                     "arguments": ""
    #                 }
    #             }
    #         ]
    #     }
    #     whiteboard.append(faked_assistant_response)
    #     full_related_info = f"相关经验: {experience}\n相关图谱: {graph}"
    #     faked_tool_response = {
    #         "role": "tool",
    #         "tool_call_id": "retrieve_experience_001",
    #         "content": full_related_info
    #     }        
    #     whiteboard.append(faked_tool_response)

    result = master_agent.solve()
    print(result)