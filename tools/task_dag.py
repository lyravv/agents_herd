from models.llm import get_llm_response_gpt_4o
import json
"""
    [] task_0: 查询销售合同 dependency []
    level 2
    [] task_1: 查询销售合同详情 dependency [task_0]
    [] task_2: 查询销售合同相关客户 dependency [task_0]
    level 3
    [] task_3: 查询特定客户的发货详情 dependency [task_2]
    level 4
    [] task_4: 查询所发货物收货情况 dependency [task_1, task_3]
"""

task_tools=[
    {
        "type": "function",
        "function": {
            "name": "data_query",
            "description": "从关系型数据库、数据仓库或 BI 系统中获取结构化数据。",
            "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL 查询语句"
                },
                "data_source": {
                    "type": "string",
                    "description": "数据来源，例如：销售合同、销售订单物品详情、发货申请单、所发货物收货情况"
                },
                "table_name":{
                    "type": "string",
                    "description": "数据模型名称"
                },
                "metric":{
                    "type": "string",
                    "description": "可选，指标名称"
                }
            },
            "required": ["query", "data_source"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "oa_data_query",
            "description": "查询中控技术公司OA系统并返回查询结果，OA系统可查询人员信息、公司发文通知、审批流程（如报销等）；查询方式：通过关键词进行搜索",
            "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "OA系统查询语句"
                }
            },
            "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "data_insight",
            "description": "数据分析，支持基于结构化数据的预测、归因分析和异常检测",
            "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "描述要执行任务的语句"
                },
                "workspace_dir": {
                    "type": "string",
                    "description": "文件路径"
                },
                "max_retries":{
                    "type": "integer",
                    "description": "最大重试次数"
                },
                "payload":{
                    "type": "string",
                    "description": "可选的附加说明或参数"
                }
            },
            "required": ["query", "workspace_dir"]
            }
        }
    }
]

def task_dag_tool(messages: list, tools: list = task_tools)->str:
    system_prompt = """你是一个善于推理、分析的任务规划专家，你需要根据用户的查询、召回的相关业务知识图谱、系统中用于执行任务的工具来规划任务执行的DAG。你规划的任务执行DAG格式示例如下：
```json
{{
    "tasks": [
        {{
            "id": "task_0",
            "task_description": "查询销售合同",
            "asigned_subagents": "data_query",
            "hypergraph_node":"销售合同",
            "dependency": []
        }},
        {{
            "id": "task_1",
            "task_description": "根据销售合同号查询销售合同详情",
            "asigned_subagents": "data_query",
            "hypergraph_node":"销售合同详情",
            "dependency": ["task_0"]
        }},
        {{
            "id": "task_2",
            "task_description": "根据销售合同号查询销售订单物品详情",
            "asigned_subagents": "data_query",
            "hypergraph_node":"销售订单物品详情",
            "dependency": ["task_0"]
        }},
        {{
            "id": "task_3",
            "task_description": "根据销售订单物品详情查询发货申请单各物品发货情况",
            "asigned_subagents": "data_query",
            "hypergraph_node":"发货申请单",
            "dependency": ["task_2"]
        }},
        {{
            "id": "task_4",
            "task_description": "分析合同的发货确认情况",
            "asigned_subagents": "data_insight",
            "hypergraph_node":"所发货物收货情况",
            "dependency": ["task_1", "task_3"]
        }}
    ]
}}

```

    系统中用于执行任务的工具：
    {task_tools}

## 要求：
    - 任务规划DAG中每个任务的`asigned_subagents`字段必须是系统中用于执行任务的工具中的一个。
    - 任务规划DAG中每个任务的`hypergraph_node`字段必须是业务知识图谱中的一个节点，节点可能是nodes、hyperedges、events、Analysis。
    - 任务规划DAG中每个任务的`dependency`字段必须是任务规划DAG中已经规划好的任务的`id`。
    - 输出任务规划DAG的JSON字符串，不能输出任何其他内容
    
    

    
"""
    prompt = """
    上下文：{context}
"""

    llm_messages = [
        {"role": "system", "content": system_prompt.format(task_tools=json.dumps(tools, ensure_ascii=False, indent=2))},
        {"role": "user", "content": prompt.format(context=messages)}
    ]
    response = get_llm_response_gpt_4o(llm_messages)
    print(f"task_dag_tool response: {response}")
    return response


if __name__ == "__main__":
    graph_retrive_result = json.load(open("/home/wangling/projects/agents_herd/data_2/hyper_schema_workflow.json"))
    graph_retrive_result = json.dumps(graph_retrive_result, ensure_ascii=False, indent=2)

    # query = "SC20251010合同为什么还不能确认收入，帮忙看下什么情况"
    # query = "SC20251010合同还有什么物资没有处理，导致不能确认收入。"
    query = "sr20251104这个发货单的成套物资为什么还没有出库"
    # query = "SC20251010合同哪些物资、什么原因影响未出库？对应负责人是谁？"


    history_messages = [{"role": "user", "content": query},
        {
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": "graph_retrive_001",
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
        },
    ]
    task_dag_tool(history_messages, tools=task_tools)
