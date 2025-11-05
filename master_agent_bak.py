from mcp.types import Content
from utils.whiteboard import Whiteboard
from models.llm import get_llm_response_gpt_4o_with_tools
# from graph.graph_match import graph_match
# from memory.long_term_memory import experience_match
import json
import asyncio
from models import llm_openai
from tools.mcp_client import get_available_tools_async, convert_mcp_tool_to_openai, call_tool

master_agent_system_prompt = f"""
你是一个严谨的智能助手，你会通过工具调用来思考、规划、获取足够的信息来解决用户的问题。
为了让你解决问题时有所参考（提高效率，避免过多的不确定尝试），已经使用预设流程对用户问题进行了预分析，包括相似问题匹配召回，业务图谱匹配召回等。如果有召回，在graph_retrive_tool和retrieve_experience_tool的召回中会呈现。

注意事项：
- 如果问题比较复杂(如POD异常分析)，你必须使用思考工具显示推理，并制定计划的任务执行图。
- 如果你拿到了任务执行图，你必须使用todo_write工具对其进行管理，包括创建、更新
- 你需要兼顾计划和各步骤的执行结果，如果发现计划不可行或执行失败，你需要使用思考工具及时调整计划。
- 即时不需要更新计划，你仍可以调用思考工具显示推理。
- 召回经验不一定对解决问题有帮助。
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
    
#     query = """这些订单的总金额是多少？
# order_id,contract_id,order_amount,order_date,delivery_date,status
# SO20251020,SC20251004,1100000.00,2025-10-20,2025-11-05,pending
# SO20251030,SC20251006,650000.00,2025-10-30,2025-11-15,pending
# SO20251110,SC20251008,820000.00,2025-11-10,2025-11-30,pending"""
    # query = "上海数联信息的合同为什么还没有POD？"
    # query = "SC20251010合同为什么还不能确认收入，帮忙看下什么情况"
    # query = "SC20251010合同还有什么物资没有处理，导致不能确认收入。"
    query = "sr20251104这个发货单的成套物资为什么还没有出库"
    # query = "SC20251010合同哪些物资、什么原因影响未出库？对应负责人是谁？"
    
    print(query)
    messages = [{"role": "user", "content": query}]
    whiteboard.append(messages[0])

    # tables = json.load(open("/home/wangling/projects/agents_herd/data/table_ontology_simulation/tables.json"))
    # relations = json.load(open("/home/wangling/projects/agents_herd/data/table_ontology_simulation/relation.json"))
    # graph_retrive_result = json.dumps(tables, ensure_ascii=False, indent=2) + json.dumps(relations, ensure_ascii=False, indent=2)
    
    graph_retrive_result = json.dumps(json.load(open("/home/wangling/projects/agents_herd/data_2/hyper_schema_workflow.json")))
    graph_retrive = [{
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "call_graph_retrive_tool_001",
                    "type": "function",
                    "function": {
                        "name": "graph_retrive_tool",
                        "arguments": ""
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_graph_retrive_tool_001",
            "content": graph_retrive_result
        }]
        
    whiteboard.append(graph_retrive[0])
    whiteboard.append(graph_retrive[1])

    # pre defined plan

    result = master_agent.solve()
    print(result)