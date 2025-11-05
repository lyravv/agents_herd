# -*- coding: utf-8 -*-
import json
import os
from fastmcp import FastMCP
from typing import Annotated, Optional, Literal
from pydantic import Field
from utils.whiteboard import Whiteboard
from utils.logger import setup_logger
from models.llm import get_llm_response_gpt_4o

# 初始化logger
logger = setup_logger('mcp_server')

mcp = FastMCP("hgt2.0工具")


@mcp.tool()
def database_search(query: Annotated[str, Field(description="用户查询")],
            data_source: Annotated[Optional[str], Field(description="数据来源")],
            table_name: Annotated[Optional[str], Field(description="数据模型名称")],
            metric: Annotated[Optional[str], Field(description="指标名称")],
            ) -> str:
    """
    从关系型数据库、数据仓库或 BI 系统中获取结构化数据。
    """
    logger.info("开始执行data_query工具 - 查询数据")
    return f"查询数据: {query}"

@mcp.tool()
def oa_search(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    查询中控技术公司OA系统并返回查询结果，OA系统可查询人员信息、公司发文通知、审批流程（如报销等）；查询方式：通过关键词进行搜索
    """
    logger.info("开始执行oa_data_query工具 - 查询OA数据")
    return f"查询OA数据: {query}"

@mcp.tool()
def kms_search(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    查询中控技术公司KMS知识库并返回查询结果，kms是中控所有知识汇聚平台。kms包含公司战略品牌（包括企业文化、公司品牌管理、宣传、战略规划等文档、视频素材知识）、产品（工业软件、控制系统、仪器仪表、配置模板、生态产品等产品知识）、解决方案（包括解决方案专家标准动作、解决方案图谱、行业解决方案、通用解决方案、行业知识沉淀、多元生态融合等解决方案相关知识）、工程服务、管理（文件管理、人力资源、数字化流程、专利、软著、质量运营、荣誉、资质、供应链、办公、读书会等管理相关知识）、百科（产品、技术、行业、管理、营销等概念知识）、营销（合同模板、投标资料、客户案例、营销培训、产品行业解决方案宣传资料等）、数字化（IT、AI、crm、srm、sap、mes、erp、bpm等数字化相关知识）等各方面知识库；查询方式：kms知识库的数据已通过向量化存入库中，可以通过语义匹配进行查询，因此搜索时可以保留问题语义意图等

    """
    logger.info("开始执行search_database工具 - 搜索数据库")
    return f"搜索数据库: {query}"

@mcp.tool()
def bpm_search(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    查询中控技术公司BPM业务系统的流程单据，bpm是公司客户管理、CRM、销售管理、物料主数据、工程业务管理、售后服务管理、固定资产管理、辅助办公管理、人员绩效管理的业务系统，流转的是流程、单据；查询方式：通过关键词进行搜索
    """
    logger.info("开始执行bpm_data_query工具 - 查询BPM数据")
    return f"查询BPM数据: {query}"

@mcp.tool()
def web_search(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    从互联网上搜索相关信息并返回查询结果。
    """
    logger.info("开始执行web_search工具 - 搜索互联网")
    return f"搜索互联网: {query}"

@mcp.tool()
def org_qa(query: Annotated[str, Field(description="用户查询")]) -> str:
    """
    查询精确的员工个人信息、组织架构信息，查询范围如下：[\"张三是谁\",\"张三的部门\",\"张三的直接上级\",\"张三的直接下级\",\"**部门有哪些子部门\", \"**部门的领导是谁\"]；查询方式：org_qa是一个问答系统，可通过自然语言查询员工信息，组织架构信息等
    """
    logger.info("开始执行org_qa工具 - 查询组织架构")
    return f"查询组织架构: {query}"


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
        {"role": "user", "content": prompt.format(whiteboard_info=whiteboard_info_str)}
    ]
    result = get_llm_response_gpt_4o(messages) 
    logger.info(f"LLM思考结果: {result}")
    logger.info(f"LLM思考推理完成，结果长度: {len(result)}")
    
    return result["content"]

@mcp.tool(name="search_database")
def search_database_tool(tables: Annotated[list[str], Field(description="要查询的数据库表名")], query: Annotated[str, Field(description="自然语言查询语句")]) -> str:
    """
    根据自然语言在指定表上进行数据库搜索。可接受一个或多个表名作为输入，内部会自动定位对应数据库和schema，并生成SQL执行查询。
    
    Args:
        query (str): 自然语言查询语句
        table_name (str): 要查询的数据库表名
        
    Returns:
        str: 数据库查询结果的JSON字符串
    """
    from tools.search_database import search_database

    result = search_database(tables, query)
    logger.info(f"数据库查询结果: {result}")
    return result

@mcp.tool(name="todo_write")
def todo_write_tool(action: Annotated[Literal["todo_create", "todo_complete", "todo_failure", "todo_show"], Field(description="要执行的操作类型：\n"
                    "- todo_create: 创建一个新的 todo DAG\n"
                    "- todo_complete: 将某个任务标记为完成\n"
                    "- todo_failure: 将某个任务标记为失败\n"
                    "- todo_show: 查看当前 DAG")],
    todo_text: Annotated[Optional[str], Field(description="当 action=todo_create 时提供，"
                    "LLM 输出的任务描述文本，格式为：\n"
                    "任务描述：<任务描述>\n"
                    "依赖任务：<依赖任务1>, <依赖任务2>, ...\n"
                    "示例：\n"
                    "任务描述：完成项目文档\n"
                    "依赖任务：项目计划, 项目需求")]=None,
    task_id: Annotated[Optional[str], Field(description="当 action=todo_complete, todo_failure 时提供，"
                    "要操作的任务 ID")]=None):
    """
    管理一个带有依赖关系（DAG）的任务清单。
    支持创建、完成、标记失败、查看等操作。
    可用于LLM自主规划和追踪任务执行状态。
    """
    from tools.todo import todo_write
    result = todo_write(action, todo_text, task_id)
    logger.info(f"todo_write操作结果: {result}")
    return result


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
    mcp.run(transport="http", port=3458)
