
def graph_match(query: str) -> str:
    if query == "POD异常分析":
        return ""
    elif "订单未生成POD的原因" in query:
        return f"""
        销售订单查询工具——查询——销售订单
        POD查询工具——查询——订单POD状态
        POD异常分析节点——查询——货品比对
        POD异常分析节点——查询——缺料分析
        POD异常分析节点——查询——直发确认
        POD异常分析节点——查询——货品签收
       """
    else:
        return ""