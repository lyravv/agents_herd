# 库存表 (Inventory)

## 描述
库存表用于记录和跟踪公司仓库中的产品库存情况，包括产品信息、库存数量、库存位置等。

## 表结构
| 字段名 | 类型 | 描述 |
| ------ | ---- | ---- |
| inventory_id | string | 库存记录ID，主键 |
| product_id | string | 产品ID |
| product_name | string | 产品名称 |
| quantity | integer | 当前库存数量 |
| location | string | 库存位置/仓库位置 |
| status | string | 库存状态（可用、预留、损坏等） |
| last_updated | date | 最近更新日期 |
| min_stock_level | integer | 最低库存水平 |
| max_stock_level | integer | 最高库存水平 |
| supplier_id | string | 供应商ID |
| supplier_name | string | 供应商名称 |

## 示例
```
inventory_id,product_id,product_name,quantity,location,status,last_updated,min_stock_level,max_stock_level,supplier_id,supplier_name
INV001,P001,高性能服务器,120,A区-01架,available,2025-01-15,50,200,SUP001,服务器供应商A
INV002,P002,网络存储设备,85,A区-02架,available,2025-01-20,30,100,SUP002,网络设备供应商A
```

## 关联关系
- 与发货交接单关联：当发货来源为"库存发货"时，库存表中对应产品的数量会相应减少
- 与产品表关联：通过product_id关联到产品详细信息
- 与供应商表关联：通过supplier_id关联到供应商详细信息