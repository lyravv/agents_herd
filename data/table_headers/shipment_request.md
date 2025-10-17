# table name
发货申请表

# table description
记录销售订单的发货申请信息，包括申请日期、数量和审批状态等信息

# headers description
| header | description |
| --- | --- |
| shipment_id | 发货ID，主键，唯一标识发货申请 |
| order_id | 关联的订单ID，外键，关联到销售订单表 |
| request_date | 申请日期，发货申请的提交日期 |
| quantity | 数量，申请发货的产品数量 |
| status | 状态，发货申请的审批状态，可能的值包括：pending（待审批）、approved（已批准）、rejected（已拒绝）、completed（已完成） |

# example
| shipment_id | order_id | request_date | quantity | status |
| ----------- | -------- | ------------ | -------- | ------ |
| SH20251007 | SO20251003 | 2025-10-07 | 100 | approved |

