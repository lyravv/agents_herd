from utils.whiteboard import Whiteboard
from models.llm import get_llm_response_gpt_4o_with_tools
# from graph.graph_match import graph_match
# from memory.long_term_memory import experience_match
import json
import asyncio
from models import llm_openai
from tools.mcp_client import get_available_tools_async, convert_mcp_tool_to_openai, call_tool
from utils.logger import setup_logger


logger = setup_logger('master_tracer')

# master_agent_system_prompt = f"""
# 你是一个严谨的智能助手，你会通过工具调用来思考、规划、获取足够的信息来解决用户的问题。
# 为了让你解决问题时有所参考（提高效率，避免过多的不确定尝试），已经使用预设流程对用户问题进行了预分析，包括相似问题匹配召回，业务图谱匹配召回等。如果有召回，在graph_retrive_tool和retrieve_experience_tool的召回中会呈现。
# 你必须解决问题，而不能只给出解决问题的步骤或建议。计划、思考、步骤...你都必须用think输出。你一旦输出content就代表你已经完成任务。
# 你想调用search_database之前最好think一下，在让think工具复述相关表格节点和其连接关系（不同表格之间的连接键名称可能不一致，相似的字段可能有不同的值，比如合同ID和合同编号甚至SAP系统中的合同ID这样的字段。需要弄清楚是怎么连接的），因为search_database只能根据连接键来查询，它并没有思考能力。

# 召回信息说明：
# - 数据表：各个表名称、描述、主键、表字段、表所属系统的罗列
# - 表格链接键：各个表之间的连接键名称。尤其需要注意2个表联合查询时候，连接键的名称可能不一致。如果查询单个表，而查询prompt中没有指定连接键，很有可能查不出
# - 流程图表：展示了业务流程的可视化图表，包括流程节点、流程线、条件分支等。
# - 人类经验：包含了业务人员在实际操作中遇到的问题、解决方案、经验教训等。

# 注意事项：
# - 如果问题比较复杂，或者在解决问题的过程中执行结果跟预想的有偏差，你必须使用思考工具显示推理，并制定计划的任务执行图。
# - 如果你拿到了任务执行图，你必须使用todo_write工具对其进行管理，包括创建、更新、删除任务。
# - 你需要兼顾计划和各步骤的执行结果，如果发现计划不可行或执行失败，你需要使用思考工具及时调整计划。
# - 即时不需要更新计划，你仍可以调用思考工具显示推理。
# - 召回经验不一定对解决问题有帮助。
# """

# gpt-5-medium
master_agent_system_prompt = """
你是一个严谨的智能助手，竭尽全力解决用户的问题。你所需要的信息都可以通过工具调用来获取。你如果需要思考也是调用think工具来思考。你直接输出内容仅在你已经解决问题了才被允许。你不要输出规划步骤之类的内容，你如果觉得难以解决，就调用think工具来思考。

已经为你预调用了retrive工具，召回了与你的问题相关的内容。如下所示。
- 数据表：各个表名称、描述、主键、表字段、表所属系统的罗列
- 库表链接键：各个表之间的连接键名称。尤其需要注意2个表联合查询时候，连接键的名称可能不一致。如果查询单个表，而查询prompt中没有指定连接键，很有可能查不出
- 流程图表：展示了业务流程的可视化图表，包括流程节点、流程线、条件分支等。
- 人类经验：包含了业务人员在实际操作中遇到的问题、解决方案、经验教训等。

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

        messages = [{"role": "system", "content": master_agent_system_prompt}] + messages
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
        while turn < 50:
            llm_result = self.llm_step()
            # 如果response不是工具调用，跳出循环
            if llm_result.get("role") == "assistant" and llm_result.get("content") is not None:
                final_response = llm_result
                break
           
            logger.info(f"messages append: {llm_result}")
            self.whiteboard.append(llm_result)
            tool_execution_results = self.execute_tool_calls(llm_result)
            print(f"工具调用结果: {tool_execution_results}")
            for result in tool_execution_results:
                self.whiteboard.append(result)
                logger.info(f"messages append: {result}")
            turn += 1

        logger.info(f"turn: {turn}")
        if final_response is None:
            return "我无法解决这个问题。"
        # 将最终助手消息写回whiteboard，保证多轮会话上下文完整
        logger.info(f"messages append: {final_response}")
        try:
            self.whiteboard.append(final_response)
        except Exception as e:
            logger.info(f"append final_response failed: {e}")
        return final_response["content"]

def _build_priori_knowledge_payload() -> list[dict]:
    """构造预召回数据的tool消息，自动选择可用数据源，返回两条消息。"""
    import os
    payload_parts = []
    # 优先尝试data_2目录
    base1 = "/home/wangling/projects/agents_herd/data_2"
    tables_json1 = os.path.join(base1, "tables.json")
    relations_json1 = os.path.join(base1, "relations.json")
    flow_md1 = os.path.join(base1, "flowchat.md")
    human_md1 = os.path.join(base1, "human_experience.md")

    # 备用：table_ontology_simulation目录
    base2 = "/home/wangling/projects/agents_herd/data/table_ontology_simulation"
    tables_json2 = os.path.join(base2, "tables.json")
    relations_json2 = os.path.join(base2, "relation.json")

    def _safe_json(path):
        try:
            if os.path.exists(path):
                return json.dumps(json.load(open(path, encoding="utf-8")), ensure_ascii=False, indent=2)
        except Exception:
            return None
        return None

    def _safe_text(path):
        try:
            if os.path.exists(path):
                return open(path, encoding="utf-8").read()
        except Exception:
            return None
        return None

    # 尝试加载
    graph_retrive_result = _safe_json(tables_json1) or _safe_json(tables_json2) or ""
    relations_result = _safe_json(relations_json1) or _safe_json(relations_json2) or ""
    flowchart = _safe_text(flow_md1) or ""
    human_experience = _safe_text(human_md1) or ""

    if not any([graph_retrive_result, relations_result, flowchart, human_experience]):
        return []

    priori_knowlege_retrive_result = (
        (f"数据表:\n{graph_retrive_result}\n\n" if graph_retrive_result else "") +
        (f"表格链接键:\n{relations_result}\n\n" if relations_result else "") +
        (f"流程图表:\n{flowchart}\n\n" if flowchart else "") +
        (f"人类经验:\n{human_experience}" if human_experience else "")
    ).strip()

    tool_call_id = "call_priori_knowlege_retrive_tool_auto"
    return [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "priori_knowlege_retrive_tool",
                        "arguments": ""
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": priori_knowlege_retrive_result
        }
    ]


if __name__ == "__main__":
    # 交互式多轮会话
    whiteboard = Whiteboard("interactive_session")
    master_agent = MasterAgent(whiteboard)
    # whiteboard.clear()

    print("输入你的问题，或输入 :clear 清空、:recall 注入召回、:exit 退出")
    while True:
        try:
            query = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出")
            break

        if not query:
            continue

        if query.lower() in (":exit", "exit", ":quit", "quit"):
            print("Bye")
            break
        if query.lower() in (":clear", "clear"):
            whiteboard.clear()
            print("上下文已清空")
            continue
        if query.lower() in (":recall", "recall"):
            payload = _build_priori_knowledge_payload()
            if payload:
                logger.info(f"messages append: {payload}")
                whiteboard.append(payload[0])
                whiteboard.append(payload[1])
                print("已注入预召回数据")
            else:
                print("未找到可用的预召回数据文件")
            continue

        # 正常问答
        whiteboard.append({"role": "user", "content": query})
        logger.info(f"messages append: {{'role': 'user', 'content': '{query}'}}")
        result = master_agent.solve()
        print(result)