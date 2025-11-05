#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import pandas as pd
from tabulate import tabulate

def connect_db():
    """连接到SQLite数据库"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tables.db')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

def execute_query(conn, query, params=None):
    """执行SQL查询并返回结果"""
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    rows = cursor.fetchall()
    return rows

def print_results(rows, title=None):
    """格式化打印查询结果"""
    if not rows:
        print("查询结果为空")
        return
    
    if title:
        print(f"\n=== {title} ===")
    
    # 将结果转换为DataFrame以便美观打印
    df = pd.DataFrame([dict(row) for row in rows])
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
    print(f"共 {len(rows)} 条记录\n")

def example_1_basic_query(conn):
    """示例1: 基本查询 - 查询所有待处理的发货申请"""
    query = """
    SELECT shipment_id, order_id, product_name, request_date, quantity
    FROM shipment_request
    WHERE status = 'pending'
    ORDER BY request_date
    """
    rows = execute_query(conn, query)
    print_results(rows, "待处理的发货申请")

def example_2_count_and_group(conn):
    """示例2: 分组统计 - 按状态统计发货申请数量"""
    query = """
    SELECT status, COUNT(*) as count
    FROM shipment_request
    GROUP BY status
    ORDER BY count DESC
    """
    rows = execute_query(conn, query)
    print_results(rows, "发货申请状态统计")

def example_3_join_query(conn):
    """示例3: 连接查询 - 查询销售订单及其对应的合同信息"""
    query = """
    SELECT so.order_id, so.order_date, so.order_amount, 
           sc.contract_id, sc.customer_name, sc.sign_date
    FROM sales_order so
    JOIN sales_contract sc ON so.contract_id = sc.contract_id
    ORDER BY so.order_date DESC
    """
    rows = execute_query(conn, query)
    print_results(rows, "销售订单及对应合同信息")

def example_4_complex_join(conn):
    """示例4: 复杂连接查询 - 查询每个订单的发货情况"""
    query = """
    SELECT so.order_id, so.order_date, so.status as order_status,
           sr.shipment_id, sr.product_name, sr.quantity, sr.status as shipment_status
    FROM sales_order so
    LEFT JOIN shipment_request sr ON so.order_id = sr.order_id
    ORDER BY so.order_date DESC, sr.request_date
    """
    rows = execute_query(conn, query)
    print_results(rows, "订单发货情况")

def example_5_subquery(conn):
    """示例5: 子查询 - 查询高于平均数量的发货申请"""
    query = """
    SELECT shipment_id, product_name, quantity, request_date
    FROM shipment_request
    WHERE quantity > (SELECT AVG(quantity) FROM shipment_request)
    ORDER BY quantity DESC
    """
    rows = execute_query(conn, query)
    print_results(rows, "高于平均数量的发货申请")

def main():
    try:
        conn = connect_db()
        
        # 执行查询示例
        example_1_basic_query(conn)
        example_2_count_and_group(conn)
        example_3_join_query(conn)
        example_4_complex_join(conn)
        example_5_subquery(conn)
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()