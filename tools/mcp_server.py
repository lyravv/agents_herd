# -*- coding: utf-8 -*-
import json
import os
from fastmcp import FastMCP
from typing import Annotated, Optional, Literal
from pydantic import Field
from utils.whiteboard import Whiteboard
from utils.logger import setup_logger
from models.llm import get_llm_response_gpt_4o

logger = setup_logger('mcp_server')

mcp = FastMCP("hgt2.0工具")

@mcp.tool()
def web_search(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    从互联网上搜索相关信息并返回查询结果。
    """
    logger.info("开始执行web_search工具 - 搜索互联网")
    return f"搜索互联网: {query}"


@mcp.tool(name="think", exclude_args=["whiteboard_id"])
def think_tool(reason: Annotated[str, Field(description="思考和推理的原因")], whiteboard_id: str = "123") -> str:
    """
    当模型遇到复杂、模糊、多步骤或需要推理整合的问题时，可主动调用此工具。该工具用于让模型进行显式思考（深度推理），系统会自动将完整对话上下文传入思考模块。模型只需说明调用原因。
    """
    logger.info("开始执行think工具 - 思考和推理")
    
    # 获取当前whiteboard实例
    whiteboard = Whiteboard(whiteboard_id)
    
    # 获取白板信息
    whiteboard_info = whiteboard.read()
    logger.info(f"获取白板信息成功，消息数量: {len(whiteboard_info)}")
    
    # 将whiteboard信息转换为字符串格式
    whiteboard_info_str = json.dumps(whiteboard_info, ensure_ascii=False, indent=2)
    
    system_prompt = """你是一个善于推理、分析的的思考者，是分析问答系统中的一环。你不直接与用户对话，也不负责最终回答。你的任务是根据上下文（包括用户问题、系统召回、系统工具、系统执行记录）、系统给你的思考理由，进行深度推理和分析。
当系统认为碰到到复杂问题，没有信心直接生成答案或工具调用时，会给你提供完整的上下文信息，并调用你来进行显式地思考和推理。系统会根据你的思考和推理采取后续措施。
你觉得有必要时需要为系统提供后续的任务规划。
"""

    prompt = """上下文：{whiteboard_info}
思考理由：{reason}
"""

    logger.info("whiteboard_info: %s", whiteboard_info_str)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt.format(whiteboard_info=whiteboard_info_str, reason=reason)}
    ]
    result = get_llm_response_gpt_4o(messages) 
    logger.info(f"LLM思考结果: {result}")
    logger.info(f"LLM思考推理完成，结果长度: {len(result)}")
    
    return result

@mcp.tool(name="search_database")
def search_database_tool(tables: Annotated[list[str], Field(description="要查询的数据库表名")], query: Annotated[str, Field(description="自然语言查询语句")]) -> str:
    """
    根据自然语言在指定表上进行数据库搜索。可接受一个或多个表名作为输入，内部会自动定位对应数据库和schema，并生成SQL执行查询。该工具只擅长具体字段与表的查询，不擅长推理或解释。请 master 生成清晰、具体、可查询的 query。
    
    instructions_for_master:
    请确保 query 明确包含：查询对象（如合同、订单、出库单、发货申请等）、限定条件（如编号、时间、客户等）以及要返回的具体字段。",
    "不要在 query 中使用模糊的词语，如“原因”、“异常”、“状态不对”等抽象表达。请改写成具体查询，例如：",
    " ❌查询合同编号为 X 的合同状态和原因",
    " ✅查询合同编号为 X 的最新合同状态字段，以及合同状态变更日志中的最新一条记录",
    " ✅查询销售订单编号为 X 的发货申请审批状态字段",
    " ✅查询发货申请编号为 X 的出库单是否已生成及过账状态",
    "如需分析异常，请将问题分解成多个清晰的数据库查询，分别查询状态、审批记录、物流单据、入库单、签收单等表。",
    "如果一个字段含义不明确（如 '状态' 可能指审批状态或发货状态），请在 query 中指明业务上下文（如 '审批状态' 或 '收货状态'）。

    Args:
        query (str): 自然语言查询语句
        table_name (str): 要查询的数据库表名
        
    Returns:
        str: 数据库查询结果的JSON字符串
    """
    from tools.search_database import search_database

    result = search_database(tables, query)
    logger.info(f"数据库查询结果: {result}")
    # 工具返回类型声明为字符串，这里将结果转为JSON字符串以通过输出校验
    return json.dumps(result, ensure_ascii=False)

@mcp.tool(name="todo_write")
def todo_write_tool(action: Annotated[Literal["todo_create", "todo_complete", "todo_failure", "todo_show"], Field(description="要执行的操作类型：\n"
                    "- todo_create: 创建一个新的 todo DAG\n"
                    "- todo_complete: 将某个任务标记为完成\n"
                    "- todo_failure: 将某个任务标记为失败\n"
                    "- todo_show: 查看当前 DAG")],
    todo_text: Annotated[Optional[str], Field(description="当 action=todo_create 时提供，"
                    "LLM 输出的任务描述文本，格式为：\n"
                    "level 1\n[] task_0: *** dependency []\n"
                    "level 2\n[] task_1: *** dependency [task_0]\n[] task_2: *** dependency [task_0]\n"
                    "level 3\n[] task_3: *** dependency [task_2]\n"
                    "level 4\n[] task_4: *** dependency [task_1, task_3]\n")]=None,
    task_id: Annotated[Optional[str], Field(description="当 action=todo_complete, todo_failure 时提供，"
                    "要操作的任务 ID")]=None) -> str:
    """
    管理一个带有依赖关系（DAG）的任务清单。
    支持创建、完成、标记失败、查看等操作。
    可用于LLM自主规划和追踪任务执行状态。

    无论创建、完成、标记失败等动作，tool执行后都会返回完整的任务DAG及状态。
    """
    from tools.todo import todo_tool
    result = todo_tool(action, todo_text, task_id)
    logger.info(f"todo_write操作结果: {result}")
    # 统一返回字符串，避免输出校验错误
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(name="natural_language_sum")
def sum_with_nl_tool(query: Annotated[str, Field(description="自然语言求和语句，有求和意图以及所需求和的数值")]) -> float:
    """
    从文本中提取所有用于求和的数值，计算它们的总和。
    
    :param query: 包含多个数字和加法操作的自然语言字符串，例如 "5加3加2"
    :return: 多个数字的和
    """
    logger.info(f"开始处理自然语言求和请求: {query[:100]}...")  # 只记录前100个字符避免日志过长
    from tools.calculate import nl_sum
    result = nl_sum(query)
    logger.info(f"自然语言求和结果: {result}")

    return result
    

if __name__ == "__main__":
    # 支持通过环境变量配置端口，便于并行验证与热重启
    port = int(os.getenv("MCP_PORT", "3459"))
    mcp.run(transport="http", port=port)
