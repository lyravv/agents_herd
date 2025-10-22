# -*- coding: utf-8 -*-
from fastmcp import FastMCP
from utils.note_board import Whiteboard


mcp = FastMCP("hgt2.0工具")

@mcp.tool(name="think")
def think_tool(whiteboard: Whiteboard) -> str:
    """
    用于思考和推理的工具，不会获取新信息或改变数据库，只是将思考记录到白板上。
    当需要复杂推理或缓存记忆时使用。

    :return: 思考的结果
    """
    from models.llm import get_llm_response_gpt_4o
    
    prompt = f"""你是一个专业的思考助手，帮助用户分析和推理复杂问题。
白板上有问题和一些相关信息，需要你根据这些信息进行思考和推理。目标是解决用户的input_query。

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
        "[] 使用销售合同查询工具，输入条件“客户名称：北京智控科技”和“签约时间：2025年3月”，查询对应的销售合同号。",
        "[] 使用销售订单查询工具，以步骤1中获得的合同号为条件，查询关联的销售订单号。",
        "[] 使用发货申请查询工具，以步骤2中获得的销售订单号为条件，查询对应的发货申请号。",
        "[] 使用确认收货查询工具，以步骤3中获得的发货申请号为条件，查询是否存在确认收货记录。",
        "[] 根据步骤4的查询结果，判断该合同是否已确认收货，并向用户反馈结论。"]
    }

## 白板信息
{whiteboard.summarize_entries_as_string()}

## 思考的输出格式：
{
    "think_process": "思考或推理过程",
    "plan": "plan的todo list"
}

## 注意：
- 计划中的每个步骤都必须使用已有的工具，不能创建新的工具。
- 仅输出json格式，不包含任何其他文本。
- 除了经验和graph中提及的工具，你还有一些通用的工具考虑可以用来规划解决问题，如
    - 自然语言计算器：用自然语言输入，执行简单的数学计算，如加法、减法、乘法、除法等。
    - 表头查询工具：查询数据库表的表头信息，包括列名、数据类型、是否主键等。
    - 数据库查询工具：根据用户输入的自然语言查询，直接查询数据库，返回符合条件的记录。
    - 子图扩展工具：根据已有的子图关系，扩展查询路径，查找更相关的节点和关系。
        
## 输出:"""

    result = get_llm_response_gpt_4o(None, prompt)
    
    try:
        result = json.loads(result)
    except json.JSONDecodeError:
        return f"思考结果解析失败: {result}"
    
    if "think_process" not in result or "plan" not in result:
        return f"思考结果格式错误: {result}"
    
    if not isinstance(result["think_process"], str) or not isinstance(result["plan"], list):
        return f"思考结果格式错误: {result}"
    
    for item in result["plan"]:
        if not isinstance(item, str):
            return f"计划项格式错误: {item}"

    whiteboard.thought_process({"content": result["think_process"]})
    
    for item in result["plan"]:
        whiteboard.plan({"content": item})
    
    return f"思考结果: {result}"

@mcp.tool(name="write")
def write_tool(whiteboard: Whiteboard) -> str:
    """
    根据系统的输入、运行轨迹、思考结果、中间过程执行结果等信息，将最终输出写给用户

    :return: 任务完成状态
    """
    from models.llm import get_llm_response_gpt_4o
    
    input_query = whiteboard.summarize_entries_as_string()

    system_prompt = """你是一个专业的助手，负责根据系统的输入、运行轨迹、思考结果、中间过程执行结果等信息，将最终输出写给用户。
    请确保输出内容准确、逻辑清晰，符合用户的需求。"""

    result = get_llm_response_gpt_4o(system_prompt, input_query)
    
    # 使用传入的Whiteboard实例写入输出结果
    whiteboard.output({"content": result})
    
    return f"任务完成状态: {result}"

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
