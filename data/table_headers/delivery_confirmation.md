# table name
货物接单表

# table description
记录货物交付确认信息，包括接收日期、接收人和数量确认等信息

# headers description
| header | description |
| --- | --- |
| delivery_id | 交付ID，主键，唯一标识货物交付记录 |
| shipment_id | 关联的发货ID，外键，关联到发货申请表 |
| receive_date | 接收日期，货物实际接收的日期 |
| received_by | 接收人，接收货物的人员或单位名称 |
| quantity_received | 接收数量，实际接收的货物数量 |
| status | 状态，货物交付的确认状态，可能的值包括：pending（待确认）、confirmed（已确认）、rejected（已拒绝）、partial（部分接收） |

# example
| delivery_id | shipment_id | receive_date | received_by | quantity_received | status |
| ----------- | ----------- | ------------ | ----------- | ----------------- | ------ |
| DC20251010 | SH20251007 | 2025-10-10 | 上海仓储中心 | 100 | confirmed |