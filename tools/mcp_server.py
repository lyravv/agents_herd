# -*- coding: utf-8 -*-
import json
import os
from fastmcp import FastMCP
from utils.whiteboard import Whiteboard
from utils.logger import setup_logger
from models.llm import get_llm_response_gpt_4o

# 初始化logger
logger = setup_logger('mcp_server')

mcp = FastMCP("hgt2.0工具")

@mcp.tool(name="think", exclude_args=["whiteboard_id"])
def think_tool(whiteboard_id: str = "123") -> str:
    """
    用于显式思考和推理的工具，将思考过程（推理）、计划记录到白板上或更新白板上已有的思考或计划。
    阅读白板上的所有记录，包括系统的用户查询输入、参考经验、业务相关节点图谱、工具执行结果、已有思考结果等信息。进行显示的思考和推理，输出其过程。如遇复杂任务，生成执行计划。
    
    think工具函数本身无需输入和输出，阅读白板信息作为思考输入，生成思考结果写到白板作为输出。
    """
    logger.info("开始执行think工具 - 思考和推理")
    
    try:
        # 获取当前whiteboard实例
        whiteboard = Whiteboard(whiteboard_id)
        
        # 获取白板信息
        whiteboard_info = whiteboard.read()
        logger.info(f"获取白板信息成功，消息数量: {len(whiteboard_info)}")
        
        # 将whiteboard信息转换为字符串格式
        whiteboard_info_str = json.dumps(whiteboard_info, ensure_ascii=False, indent=2)
        
        system_prompt = """你擅长问题推理和分析，能够清晰显示地分析用户查询问题。你需要使用白板上展示地用户问题、参考经验、业务相关节点图谱、工具执行结果、已有思考结果等信息，进行显示的思考和推理，输出其过程。如遇复杂任务，生成执行计划。
    ## 白板的字段解释
    input_query: 用户的原始查询问题
    experience_nld: 可能与用户查询问题相关的参考经验，自然语言描述
    related_graph: 可能与用户查询问题相关业务相关节点图谱，展示查询路径中涉及的节点和关系
    *_tool_results: 特定工具执行结果，展示查询路径中使用的工具和其输出结果
    think_process: 之前的显示思考结果
    plan: 之前的执行计划
    output: 关于input_query输出给用户的结果

    ## 示例
    ### whiteboard:
    input_query: 三月签的北京智控科技的合同确认收货了吗
    experience_nld: 销售合同的确认收货情况查询经验。成功的销售合同经过审批可以生成销售订单，成功审批的销售订单会生成一批发货申请，审批通过的发货会有相应的确认收货记录。查询路径是：用销售合同查询工具查询销售合同表，可以查到所需查询的合同号，在销售订单查询工具可以根据合同号查询到相关的销售订单，再在发货申请查询工具根据销售订单号查询到相关的发货申请，最后在确认收货查询工具根据发货申请号查询到确认收货记录。
    related_graph: 销售合同查询工具——查询——销售合同表
    销售合同查询工具——查询——销售订单表
    销售订单查询工具——查询——发货申请表
    发货申请查询工具——查询——确认收货记录表
    销售合同表——通过合同号关联——销售订单表
    销售订单表——通过订单号关联——发货申请表
    发货申请表——通过发货申请号关联——确认收货记录表

    ### output
    {
        "think_process": "用户想确认三月签署的北京智控科技的合同是否已完成收货。根据提供的经验知识和图谱关系，销售合同的收货确认需经过多个步骤：首先通过销售合同查询工具找到对应合同号；然后利用该合同号在销售订单查询工具中查找关联的销售订单；接着使用销售订单号在发货申请查询工具中查找对应的发货申请；最后通过发货申请号在确认收货查询工具中查看是否存在确认收货记录。因此，要回答用户问题，必须按此链路依次查询，确认是否存在最终的确认收货记录。",
        "plan": [
        "[] 使用销售合同查询工具，输入条件"客户名称：北京智控科技"和"签约时间：2025年3月"，查询对应的销售合同号。",
        "[] 使用销售订单查询工具，以步骤1中获得的合同号为条件，查询关联的销售订单号。",
        "[] 使用发货申请查询工具，以步骤2中获得的销售订单号为条件，查询对应的发货申请号。",
        "[] 使用确认收货查询工具，以步骤3中获得的发货申请号为条件，查询是否存在确认收货记录。",
        "[] 根据步骤4的查询结果，判断该合同是否已确认收货，并向用户反馈结论。"]
    }

    ## 思考的输出格式：
    {
        "think_process": "思考或推理过程",
        "plan": "plan的todo list"
    }

    ## 注意：
    - 白板上的信息是按时间顺序交互、产生或获取而来
    - 计划中的每个步骤都必须使用已有的工具，不能创建新的工具。
    - 仅输出json格式，不包含任何其他文本。
    - 除了经验和graph中提及的工具，你还有一些通用的工具考虑可以用来规划解决问题，如
        - 自然语言计算器：用自然语言输入，执行简单的数学计算，如加法、减法、乘法、除法等。
        - 表头查询工具：查询数据库表的表头信息，包括列名、数据类型、是否主键等。
        - 数据库查询工具：根据用户输入的自然语言查询，直接查询数据库，返回符合条件的记录。
        - 子图扩展工具：根据已有的子图关系，扩展查询路径，查找更相关的节点和关系。
    """

        prompt = """以下是白板上的信息，根据这些信息进行思考和推理以解决最近一轮的用户查询问题。如有必要，生成执行计划。
## 当前白板信息
{whiteboard_info}

## 输出:"""

        logger.info("whiteboard_info: %s", whiteboard_info_str)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt.format(whiteboard_info=whiteboard_info_str)}
        ]
        result = get_llm_response_gpt_4o(messages) 
        logger.info(f"LLM思考推理完成，结果长度: {len(result)}")
        
        try:
            result = json.loads(result)
            logger.info("JSON解析成功")
        except json.JSONDecodeError as e:
            logger.error("思考结果JSON解析失败: %s", str(e))
            return f"思考结果解析失败: {result}"
        
        if "think_process" not in result or "plan" not in result:
            logger.error("思考结果格式错误，缺少必要字段: %s", str(result))
            return f"思考结果格式错误: {result}"
        
        if not isinstance(result["think_process"], str) or not isinstance(result["plan"], list):
            logger.error("思考结果字段类型错误: %s", str(result))
            return f"思考结果格式错误: {result}"
        
        for item in result["plan"]:
            if not isinstance(item, str):
                logger.error("计划项格式错误: %s", str(item))
                return f"计划项格式错误: {item}"

        # 将结果写入白板
        think_message = {
            "role": "assistant",
            "content": result["think_process"],
            "type": "think_process"
        }
        whiteboard.append(think_message)
        logger.info("思考过程已写入白板")
        
        for item in result["plan"]:
            plan_message = {
                "role": "assistant", 
                "content": item,
                "type": "plan"
            }
            whiteboard.append(plan_message)
        logger.info(f"执行计划已写入白板，共{len(result['plan'])}项")
        
        logger.info("think工具执行完成")
        return f"思考结果: {result['think_process']}"
        
    except Exception as e:
        logger.error("think工具执行出错: %s", str(e))
        return f"思考工具执行失败: {str(e)}"

@mcp.tool(name="write")
def write_tool() -> str:
    """
    用于正式生成对用户的回复。根据系统的输入、运行轨迹、思考结果、中间过程执行结果等信息，将最终输出写给用户
    
    write工具函数本身无需输入和输出，阅读白板信息作为信息输入，生成最终输出写到白板作为输出，作为对用户查询query的回答。

    """
    logger.info("开始执行write工具 - 生成正式回复")
    
    try:
        # 获取当前whiteboard实例
        whiteboard = get_current_whiteboard()
        
        # 获取白板信息
        whiteboard_info = whiteboard.read()
        logger.info(f"获取白板信息成功，消息数量: {len(whiteboard_info)}")
        
        # 将whiteboard信息转换为字符串格式
        whiteboard_info_str = json.dumps(whiteboard_info, ensure_ascii=False, indent=2)
        
        system_prompt = """你是一个专业生成正式回复的助手，根据你需要使用白板上展示地用户问题、参考经验、业务相关节点图谱、工具执行结果、已有思考结果等信息，将最终输出正式输出给用户。
        请确保输出内容准确、逻辑清晰，符合用户的需求。
        
        ## 白板的字段解释
        input_query: 用户的原始查询问题
        experience_nld: 可能与用户查询问题相关的参考经验，自然语言描述
        related_graph: 可能与用户查询问题相关业务相关节点图谱，展示查询路径中涉及的节点和关系
        *_tool_results: 特定工具执行结果，展示查询路径中使用的工具和其输出结果
        think_process: 之前的显示思考结果
        plan: 之前的执行计划
        output: 关于input_query输出给用户的结果 （即上一轮的正式回复）

        """

        prompt = f"""以下是白板上的信息，根据这些信息生成正式回复。
        
        ## 当前白板信息
        {whiteboard_info_str}

        ## 输出：
        """

        logger.info("开始调用LLM生成正式回复")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        result = get_llm_response_gpt_4o(messages)
        logger.info(f"LLM回复生成完成，结果长度: {len(result)}")
        
        # 将结果写入白板
        output_message = {
            "role": "assistant",
            "content": result,
            "type": "output"
        }
        whiteboard.append(output_message)
        logger.info("正式回复已写入白板")
        
        logger.info("write工具执行完成")
        return f"任务完成状态: {result}"
        
    except Exception as e:
        logger.error(f"write工具执行出错: {e}")
        return f"回复生成失败: {str(e)}"

@mcp.tool(name="natural_language_sum")
def sum_with_nl_tool(query: str) -> float:
    """
    从文本中提取所有用于求和的数值，计算它们的总和。
    
    :param query: 包含多个数字和加法操作的自然语言字符串，例如 "5加3加2"
    :return: 多个数字的和
    """
    logger.info(f"开始处理自然语言求和请求: {query[:100]}...")  # 只记录前100个字符避免日志过长
    
    system_prompt = """你是一个智能求和助手。你的任务是：**仅当用户明确表达"对某些数值求和"的意图时**，才从输入中提取那些**待求和的具体数值项**，并转换为标准数字列表。
支持的数值形式包括：
- 阿拉伯数字：如 5, 9800, 3.14, -20
- 中文数字：如 五、十二、三百、一万二（=12000）、三点五（=3.5）
- 带单位缩写：如 10k（=10000）、5w（=50000）、2.5万（=25000）
- 混合表达：如 "共买了三次，分别是2件、五件和10件" → 提取 [2, 5, 10]

处理规则：
1. **只提取明确作为"数值量"的数字**，忽略日期、编号、序号、电话号码等非统计性数字。
2. 中文数字需正确转换为阿拉伯数字（注意："一万二" = 12000，"三千五" = 3500）。
3. 单位如"k"=1000，"w"或"万"=10000，"亿"=100000000。
4. 输出必须是严格有效的 JSON 对象，仅包含一个字段 "numbers"，其值为数字列表（按出现顺序）。

示例输入：
"10月份有5笔订单，分别是9800，10w，一万二，90000，5k，他们的总金额是多少"

期望输出：
{"numbers": [9800, 100000, 12000, 90000, 5000]}
"""
    
    prompt = f"""以下是用户输入的自然语言查询：{query}
    
    ## 输出：
    """
    
    logger.info("正在调用LLM进行数值提取...")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    result = get_llm_response_gpt_4o(messages)
    logger.info(f"LLM返回结果: {result}")
    
    try:
        result = json.loads(result)
        logger.info("JSON解析成功")
    except json.JSONDecodeError as e:
        error_msg = f"数值提取结果解析失败: {result}"
        logger.error(f"JSON解析失败: {e}, 原始结果: {result}")
        return error_msg

    if not isinstance(result, dict) or "numbers" not in result:
        error_msg = f"数值提取结果格式错误: {result}"
        logger.error(f"结果格式错误: {error_msg}")
        return error_msg

    numbers_raw = result["numbers"]
    logger.info(f"提取到的原始数字列表: {numbers_raw}")
    
    if not isinstance(numbers_raw, list):
        error_msg = f"numbers字段应为列表: {numbers_raw}"
        logger.error(f"numbers字段类型错误: {error_msg}")
        return error_msg

    numbers = []
    for idx, n in enumerate(numbers_raw):
        try:
            num = float(n)
            numbers.append(num)
            logger.debug(f"成功转换第{idx + 1}个数字: {n} -> {num}")
        except (ValueError, TypeError) as e:
            error_msg = f"numbers列表中第{idx + 1}项无法转为数字: {n}"
            logger.error(f"数字转换失败: {error_msg}, 错误: {e}")
            return error_msg

    final_sum = sum(numbers)
    logger.info(f"计算完成: {numbers} 的总和为 {final_sum}")
    return final_sum

# @mcp.tool(name="销售合同查询工具")
# def sales_contract_search_tool(query: str, whiteboard: Whiteboard) -> str:
#     """
#     通过自然语言查询满足描述的销售合同。返回符合条件的销售合同列表。
#     合同元数据描述如下：
#         ### table name
#         销售合同表

#         ### table description
#         对客户签订的正式销售合同，记录销售合同的相关信息

#         ### headers description
#         | header | description |
#         | --- | --- |
#         | contract_id | 合同ID，主键，唯一标识销售合同 |
#         | customer_name | 客户名称，销售合同签订的客户 |
#         | total_amount | 合同总金额，销售合同的金额总和 |
#         | sign_date | 签订日期，销售合同签订的日期 |
#         | status | 状态，销售合同的当前状态，可能的值包括：active（有效）、expired（已过期）、pending（待处理）、cancelled（已取消） |
#         | version | 版本号，销售合同的版本号，用于跟踪更新 |
#         | is_active | 是否有效，标识销售合同是否当前有效 |
#     """
#     search_results = sales_contract_search(query)
    

# @mcp.tool(name="通用CSV查询工具")
# def general_csv_search_tool(query: str, csv_file_path: str, csv_headers: str) -> str:
#     """
#     用于返回输入的原文。
#     当需要简单地将用户输入回显时使用。
    
#     :param query: 查询字符串
#     :param csv_file_path: CSV文件路径
#     :param csv_headers: CSV文件头，逗号分隔
#     :return: 回显的文本
#     """
#     return f"Echo: {query}"


if __name__ == "__main__":
    mcp.run(transport="http", port=3458)
