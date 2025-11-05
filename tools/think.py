from models.llm import get_llm_response_gpt_4o
def think_tool(reason: str, messages: list):
    system_prompt = """你是一个善于推理、分析的的思考者，是分析问答系统中的一环。你不直接与用户对话，也不负责最终回答。你的任务是根据上下文（包括用户问题、系统召回、系统工具、系统执行记录）、系统给你的思考理由，进行深度推理和分析。
当系统认为碰到到复杂问题，没有信心直接生成答案或工具调用时，会给你提供完整的上下文信息，并调用你来进行显式地思考和推理。系统会根据你的思考和推理采取后续措施。
你觉得有必要时需要为系统提供后续的任务规划。
    系统有一些系统级的工具，如think_tool(你就是think_tool)、todo_write(用来创建和管理todo_list的)、graph_explore(当召回的数据管理不足以分析问题时可能会扩展召回图来探索解决)
    系统还配备一些任务执行工具，如search_database(用来根据自然语言生成sql，然后查询获取对应数据)、calculate(用自然语言描述对某些数据进行处理，如累加、相乘、求同环比等等)、knowledge_retrive、web_search等。
    你规划任务时考虑用执行工具来完成任务。
"""
    prompt = """
    上下文：{context}
    思考理由：{reason}
"""
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt.format(context=messages, reason=reason)}]
    response = get_llm_response_gpt_4o(messages)
    print(response)
    return {"think": response}


if __name__ == "__main__":
    graph_retrive_result = """
{
    "tables": [
        {
            "table_name": "货物接单表",
            "table_description": "记录货物交付确认信息，包括接收日期、接收人和数量确认等信息",
            "primary_key": "delivery_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "delivery_id",
                    "description": "交付ID，主键，唯一标识货物交付记录"
                },
                {
                    "name": "shipment_id",
                    "description": "关联的发货ID，外键，关联到发货申请表"
                },
                {
                    "name": "receive_date",
                    "description": "接收日期，货物实际接收的日期"
                },
                {
                    "name": "received_by",
                    "description": "接收人，接收货物的人员或单位名称"
                },
                {
                    "name": "quantity_received",
                    "description": "接收数量，实际接收的货物数量"
                },
                {
                    "name": "status",
                    "description": "状态，货物交付的确认状态，可能的值包括：pending（待确认）、confirmed（已确认）、rejected（已拒绝）、partial（部分接收）"
                }
            ],
            "header_ref": "data/table_headers_simulation/delivery_confirmation.json",
            "table_dir":"data/table_headers_simulation/delivery_confirmation.csv"
        },
        {
            "table_name": "销售订单货品表",
            "table_description": "记录销售订单中包含的具体货品信息，包括货品名称、数量等详细信息",
            "primary_key": "item_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "item_id",
                    "description": "货品ID，主键，唯一标识订单中的货品项"
                },
                {
                    "name": "order_id",
                    "description": "关联的订单ID，外键，关联到销售订单表"
                },
                {
                    "name": "product_name",
                    "description": "货品名称，订单中货品的具体名称"
                },
                {
                    "name": "quantity",
                    "description": "数量，订单中该货品的数量"
                },
                {
                    "name": "unit_price",
                    "description": "单价，该货品的单位价格"
                },
                {
                    "name": "total_price",
                    "description": "总价，该货品的总价值（数量×单价）"
                }
            ],
            "header_ref": "data/table_headers_simulation/order_items.json",
            "table_dir":"data/table_headers_simulation/order_items.csv"
        },
        {
            "table_name": "发货申请表",
            "table_description": "记录销售订单的发货申请信息，包括申请日期、货品信息和审批状态等信息",
            "primary_key": "shipment_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "shipment_id",
                    "description": "发货ID，主键，唯一标识发货申请"
                },
                {
                    "name": "order_id",
                    "description": "关联的订单ID，外键，关联到销售订单表"
                },
                {
                    "name": "line_number",
                    "description": "订单物品行号，手动选择的订单物品子表中的行号，对应\"销售订单货品表\"的行号"
                },
                {
                    "name": "product_name",
                    "description": "货品名称，申请发货的产品名称"
                },
                {
                    "name": "request_date",
                    "description": "申请日期，发货申请的提交日期"
                },
                {
                    "name": "quantity",
                    "description": "数量，申请发货的产品数量"
                },
                {
                    "name": "status",
                    "description": "状态，发货申请的审批状态，可能的值包括：pending（待审批）、approved（已批准）、rejected（已拒绝）、completed（已完成）"
                }
            ],
            "header_ref": "data/table_headers_simulation/shipment_request.json",
            "table_dir":"data/table_headers_simulation/shipment_request.csv"
        },
        {
            "table_name": "发货交接单",
            "table_description": "记录销售订单的发货交接信息，包括发货来源、交接日期和交接状态等信息",
            "primary_key": "handover_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "handover_id",
                    "description": "交接ID，主键，唯一标识发货交接单"
                },
                {
                    "name": "shipment_id",
                    "description": "关联的发货申请ID，外键，关联到发货申请表"
                },
                {
                    "name": "order_id",
                    "description": "关联的订单ID，外键，关联到销售订单表"
                },
                {
                    "name": "product_name",
                    "description": "货品名称，交接发货的产品名称"
                },
                {
                    "name": "quantity",
                    "description": "数量，交接发货的产品数量"
                },
                {
                    "name": "delivery_source",
                    "description": "发货来源，表示货品的发货方式，可能的值包括：inventory（库存发货）、supplier_direct（供应商直发）"
                },
                {
                    "name": "supplier_name",
                    "description": "供应商名称，当发货来源为供应商直发时的供应商信息"
                },
                {
                    "name": "handover_date",
                    "description": "交接日期，发货交接的实际日期"
                },
                {
                    "name": "status",
                    "description": "状态，发货交接的状态，可能的值包括：pending（待交接）、completed（已完成）、cancelled（已取消）"
                }
            ],
            "header_ref": "data/table_headers_simulation/delivery_handover.json",
            "table_dir":"data/table_headers_simulation/delivery_handover.csv"
        },
        {
            "table_name": "销售合同表",
            "table_description": "对客户签订的正式销售合同，记录销售合同的相关信息",
            "primary_key": "contract_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "contract_id",
                    "description": "合同ID，主键，唯一标识销售合同"
                },
                {
                    "name": "customer_name",
                    "description": "客户名称，销售合同签订的客户"
                },
                {
                    "name": "total_amount",
                    "description": "合同总金额，销售合同的金额总和"
                },
                {
                    "name": "sign_date",
                    "description": "签订日期，销售合同签订的日期"
                },
                {
                    "name": "status",
                    "description": "状态，销售合同的当前状态，可能的值包括：active（有效）、expired（已过期）、pending（待处理）、cancelled（已取消）"
                },
                {
                    "name": "version",
                    "description": "版本号，销售合同的版本号，用于跟踪更新"
                },
                {
                    "name": "is_active",
                    "description": "是否有效，标识销售合同是否当前有效"
                }
            ],
            "header_ref": "data/table_headers_simulation/sales_contract.json",
            "table_dir":"data/table_headers_simulation/sales_contract.csv"
        },
        {
            "table_name": "补充合同表",
            "table_description": "记录对现有销售合同的补充协议，包括变更内容和金额调整等信息",
            "primary_key": "addendum_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "addendum_id",
                    "description": "补充合同ID，主键，唯一标识补充合同"
                },
                {
                    "name": "contract_id",
                    "description": "关联的销售合同ID，外键，关联到销售合同表"
                },
                {
                    "name": "change_desc",
                    "description": "变更描述，详细说明补充合同的变更内容"
                },
                {
                    "name": "change_amount",
                    "description": "变更金额，补充合同涉及的金额调整"
                },
                {
                    "name": "created_at",
                    "description": "创建日期，补充合同的创建时间"
                },
                {
                    "name": "status",
                    "description": "状态，补充合同的处理状态，可能的值包括：approved（已批准）、pending（待处理）、rejected（已拒绝）、cancelled（已取消）"
                }
            ],
            "header_ref": "data/table_headers_simulation/sales_contract_addendum.json",
            "table_dir":"data/table_headers_simulation/sales_contract_addendum.csv"
        },
        {
            "table_name": "内调表",
            "table_description": "记录公司内部对销售订单的调整审批信息，包括调整原因和相关部门等信息",
            "primary_key": "adjust_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "adjust_id",
                    "description": "调整ID，主键，唯一标识内部调整记录"
                },
                {
                    "name": "related_order_id",
                    "description": "关联的订单ID，外键，关联到销售订单表"
                },
                {
                    "name": "department",
                    "description": "部门，发起内部调整的部门名称"
                },
                {
                    "name": "adjust_reason",
                    "description": "调整原因，详细说明内部调整的原因"
                },
                {
                    "name": "status",
                    "description": "状态，内部调整的处理状态，如pending、completed等"
                },
                {
                    "name": "created_at",
                    "description": "创建日期，内部调整记录的创建时间"
                }
            ],
            "header_ref": "data/table_headers_simulation/internal_adjustment.json",
            "table_dir":"data/table_headers_simulation/internal_adjustment.csv"
        },
        {
            "table_name": "项目变更单表",
            "table_description": "记录销售合同执行过程中的项目变更申请，包括变更原因和金额调整等信息",
            "primary_key": "change_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "change_id",
                    "description": "变更ID，主键，唯一标识项目变更申请"
                },
                {
                    "name": "contract_id",
                    "description": "关联的销售合同ID，外键，关联到销售合同表"
                },
                {
                    "name": "reason",
                    "description": "变更原因，详细说明项目变更的原因"
                },
                {
                    "name": "old_amount",
                    "description": "原金额，变更前的合同金额"
                },
                {
                    "name": "new_amount",
                    "description": "新金额，变更后的合同金额"
                },
                {
                    "name": "request_date",
                    "description": "申请日期，项目变更申请的提交日期"
                },
                {
                    "name": "approval_status",
                    "description": "审批状态，项目变更申请的审批状态，如pending、approved等"
                }
            ],
            "header_ref": "data/table_headers_simulation/project_change_request.json",
            "table_dir":"data/table_headers_simulation/project_change_request.csv"
        },
        {
            "table_name": "销售订单表",
            "table_description": "基于销售合同生成的具体订单信息，记录订单金额、交付日期和状态等信息",
            "primary_key": "order_id",
            "system": "bpm",
            "fields": [
                {
                    "name": "order_id",
                    "description": "订单ID，主键，唯一标识销售订单"
                },
                {
                    "name": "contract_id",
                    "description": "关联的销售合同ID，外键，关联到销售合同表"
                },
                {
                    "name": "order_amount",
                    "description": "订单金额，该销售订单的具体金额"
                },
                {
                    "name": "order_date",
                    "description": "下单日期，销售订单的创建日期"
                },
                {
                    "name": "delivery_date",
                    "description": "交付日期，预计的产品或服务交付日期"
                },
                {
                    "name": "status",
                    "description": "状态，订单的当前处理状态，可能的值包括：pending（待处理）、in_progress（处理中）、completed（已完成）、cancelled（已取消）"
                }
            ],
            "header_ref": "data/table_headers_simulation/sales_order.json",
            "table_dir":"data/table_headers_simulation/sales_order.csv"
        }
    ]
    "relation": [
        {
        "source": "销售合同表",
        "target": "销售订单表",
        "relation": "has_order",
        "join_key": [
            "contract_id"
        ]
        },
        {
        "source": "销售订单表",
        "target": "销售订单货品表",
        "relation": "contains_item",
        "join_key": [
            "order_id"
        ]
        },
        {
        "source": "销售订单表",
        "target": "发货申请表",
        "relation": "creates_shipment",
        "join_key": [
            "order_id"
        ]
        },
        {
        "source": "发货申请表",
        "target": "货物接单表",
        "relation": "confirmed_by_delivery",
        "join_key": [
            "shipment_id"
        ]
        },
        {
        "source": "发货申请表",
        "target": "发货交接单",
        "relation": "has_handover",
        "join_key": [
            "shipment_id"
        ]
        },
        {
        "source": "销售订单表",
        "target": "发货交接单",
        "relation": "has_delivery",
        "join_key": [
            "order_id"
        ]
        },
        {
        "source": "销售合同表",
        "target": "补充合同表",
        "relation": "has_addendum",
        "join_key": [
            "contract_id"
        ]
        },
        {
        "source": "销售订单表",
        "target": "内调表",
        "relation": "has_adjustment",
        "join_key": [
            "order_id",
            "related_order_id"
        ]
        },
        {
        "source": "销售合同表",
        "target": "项目变更单表",
        "relation": "has_change_request",
        "join_key": [
            "contract_id"
        ]
        }
    ]
}
    """
    history_messages = [{"role": "user", "content": "北京智控科技的合同为什么还没有POD？"},
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
    think_tool("如何进行POD异常分析，任务规划", history_messages)
