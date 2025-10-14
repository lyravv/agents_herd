# table name
项目变更单表

# table description
记录销售合同执行过程中的项目变更申请，包括变更原因和金额调整等信息

# headers description
| header | description |
| --- | --- |
| change_id | 变更ID，主键，唯一标识项目变更申请 |
| contract_id | 关联的销售合同ID，外键，关联到销售合同表 |
| reason | 变更原因，详细说明项目变更的原因 |
| old_amount | 原金额，变更前的合同金额 |
| new_amount | 新金额，变更后的合同金额 |
| request_date | 申请日期，项目变更申请的提交日期 |
| approval_status | 审批状态，项目变更申请的审批状态，如pending、approved等 |

# example
| change_id | contract_id | reason | old_amount | new_amount | request_date | approval_status |
| --------- | ----------- | ------ | ---------- | ---------- | ------------ | --------------- |
| PC20251005 | SC20251001 | 增加交付范围 | 500000.00 | 550000.00 | 2025-10-05 | approved |