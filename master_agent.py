from utils.note_board import Whiteboard
from tools.mcp_server import MCP
from models.llm import get_llm_response_with_function_call
import json

# 获取全局共享的whiteboard实例
whiteboard = Whiteboard.get_instance()

master_agent_system_prompt = f"""
你是一个工具调用专家。系统通过whiteboard向你呈现有用的信息。白板上可能包含用户的输入问题，记忆系统相关的参考经验，图谱上相关的节点、边等信息。
你必须调用工具进行输出，你的输出也会被写到白板上。你可以调用think工具去思考，指定plan，也可以调用write工具去输出，这些工具也看得到白板上的信息。你还可以调用特定的一些工具完成一些任务，如获取数据，查询数据库，计算等等。
"""

master_agent_prompt = f"""
通过工具调用继续再whiteboard推演，直至解答出whiteboard上用户的input query。

## whiteboard
{whiteboard}
"""



class MasterAgent:
    def __init__(self, mcp: MCP, whiteboard: Whiteboard = None):
        self.mcp = mcp
        # 如果没有传入whiteboard，使用全局共享实例
        self.whiteboard = whiteboard if whiteboard is not None else Whiteboard.get_instance()

    def step(self, thought: str) -> str:
        messages = [
            {"role": "system", "content": master_agent_system_prompt},
            {"role": "user", "content": master_agent_prompt.format(whiteboard=self.whiteboard)}
        ]
        response = get_llm_response_with_function_call(messages, self.mcp.functions)
        if response["function_call"]:
            function_call = response["function_call"]
            function_args = json.loads(function_call["arguments"])
            function_name = function_call["name"]
            function_response = self.mcp.call_function(function_name, function_args)
            messages.append(response)
            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_response
            })
        else:
            messages.append(response)


    def solve(self, query: str) -> str:
        while self.whiteboard.get_latest_entry().data_type is not "output":
            result = self.step()
        return result

if __name__ == "__main__":
    mcp = MCP()
    # 使用全局共享的whiteboard实例
    shared_whiteboard = Whiteboard.get_instance()
    master_agent = MasterAgent(mcp, shared_whiteboard)
    
    while True:
        query = input("用户query: ")
        if query.lower() == "exit":
            break
        
        shared_whiteboard.user_input({"content": query})

        # 这里需要实现experience_match和graph_match函数
        # experience = experience_match(query)
        # graph = graph_match(query)
        
        # shared_whiteboard.experience_nld({"content": experience})
        # shared_whiteboard.related_graph({"content": graph})

        result = master_agent.solve(query)
        print(result)
