# table name
补充合同表

# table description
记录对现有销售合同的补充协议，包括变更内容和金额调整等信息

# headers description
| header | description |
| --- | --- |
| addendum_id | 补充合同ID，主键，唯一标识补充合同 |
| contract_id | 关联的销售合同ID，外键，关联到销售合同表 |
| change_desc | 变更描述，详细说明补充合同的变更内容 |
| change_amount | 变更金额，补充合同涉及的金额调整 |
| created_at | 创建日期，补充合同的创建时间 |
| status | 状态，补充合同的处理状态，可能的值包括：approved（已批准）、pending（待处理）、rejected（已拒绝）、cancelled（已取消） |

# example
| addendum_id | contract_id | change_desc | change_amount | created_at |
| ----------- | ----------- | ----------- | ------------- | ---------- |
| AD20251002 | SC20251001 | 增加售后技术支持 | 20000.00 | 2025-10-02 |