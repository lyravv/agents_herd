# table name
销售合同表

# table description
对客户签订的正式销售合同，记录销售合同的相关信息

# headers description
| header | description |
| --- | --- |
| contract_id | 合同ID，主键，唯一标识销售合同 |
| customer_name | 客户名称，销售合同签订的客户 |
| total_amount | 合同总金额，销售合同的金额总和 |
| sign_date | 签订日期，销售合同签订的日期 |
| status | 状态，销售合同的当前状态，如active、expired等 |
| version | 版本号，销售合同的版本号，用于跟踪更新 |
| is_active | 是否有效，标识销售合同是否当前有效 |

# example
| contract_id | customer_name | total_amount | sign_date | status | version | is_active |
|--------------|----------------|---------------|------------|----------|-----------|
| SC20251001 | 北京智控科技 | 500000.00 | 2025-10-01 | active | 1 | TRUE |