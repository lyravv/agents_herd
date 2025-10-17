# table name
销售订单表

# table description
基于销售合同生成的具体订单信息，记录订单金额、交付日期和状态等信息

# headers description
| header | description |
| --- | --- |
| order_id | 订单ID，主键，唯一标识销售订单 |
| contract_id | 关联的销售合同ID，外键，关联到销售合同表 |
| order_amount | 订单金额，该销售订单的具体金额 |
| order_date | 下单日期，销售订单的创建日期 |
| delivery_date | 交付日期，预计的产品或服务交付日期 |
| status | 状态，订单的当前处理状态，可能的值包括：pending（待处理）、in_progress（处理中）、completed（已完成）、cancelled（已取消） |

# example
| order_id | contract_id | order_amount | order_date | delivery_date | status |
| -------- | ----------- | ------------ | ---------- | ------------- | ------ |
| SO20251003 | SC20251001 | 520000.00 | 2025-10-03 | 2025-10-15 | pending |