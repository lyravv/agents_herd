# from utils.note_board import Whiteboard
# from tools.mcp_server import MCP
from utils.whiteboard import Whiteboard
from models.llm import get_llm_response_with_function_call
from graph.graph_match import graph_match
from memory.long_term_memory import experience_match
import json
import asyncio
from tools.mcp_client import get_available_tools_async, call_tool

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

    def step(self) -> str:

        print(f"当前白板状态: {self.whiteboard.summarize_entries_as_string()}")
        messages = [
            {"role": "system", "content": master_agent_system_prompt},
            {"role": "user", "content": master_agent_prompt.format(whiteboard_str=self.whiteboard.summarize_entries_as_string())}
        ]
        tools = asyncio.run(get_available_tools_async())
        print(f"可用工具: {tools}")
        functions = [tool.__dict__ for tool in tools]

        response = get_llm_response_with_function_call(messages, functions)
        if response.get("function_call"):
            function_call = response["function_call"]
            function_args = json.loads(function_call["arguments"])
            function_name = function_call["name"]
            function_response = asyncio.run(call_tool(function_name, function_args))
            messages.append(response)
            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_response
            })
            return function_response
        else:
            messages.append(response)
            return response.get("content", "")


    def solve(self) -> str:
        while True:
            latest_entry = self.whiteboard.get_latest_entry()
            if latest_entry and latest_entry.get("type") == "output":
                break
            result = self.step()
        return result

if __name__ == "__main__":
    # 使用全局共享的whiteboard实例
    # whiteboard = Whiteboard.get_instance()
    whiteboard = Whiteboard("whiteboard.json")
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
    whiteboard.user_input({"content": query})

    # 这里需要实现experience_match和graph_match函数
    experience = experience_match(query)
    graph = graph_match(query)
    
    if experience:
        whiteboard.experience_nld({"content": experience})
    if graph:
        whiteboard.related_graph({"content": graph})

    result = master_agent.step()
    print(result)