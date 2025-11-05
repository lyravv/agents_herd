#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
import sqlite3
import glob
from pathlib import Path

def create_table_from_json(cursor, json_file):
    """根据JSON文件创建数据库表"""
    with open(json_file, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    table_name = Path(json_file).stem  # 使用文件名作为表名
    
    # 检查JSON文件是否包含字段定义
    if not schema.get('fields'):
        print(f"警告: {json_file} 没有字段定义，跳过创建表")
        return None, None
    
    # 构建创建表的SQL语句
    fields = []
    primary_key = schema.get('primary_key', '')
    field_names = []
    
    for field in schema['fields']:
        field_name = field['name']
        field_names.append(field_name)
        # 根据字段名称推断类型
        field_type = 'TEXT'
        if 'date' in field_name.lower():
            field_type = 'DATE'
        elif 'amount' in field_name.lower() or 'quantity' in field_name.lower() or 'number' in field_name.lower():
            field_type = 'NUMERIC'
        
        # 不在字段定义中添加PRIMARY KEY约束，而是在最后单独添加
        fields.append(f"{field_name} {field_type}")
    
    # 如果没有字段，跳过创建表
    if not fields:
        print(f"警告: {json_file} 没有有效字段，跳过创建表")
        return None, None
    
    # 如果有主键，添加PRIMARY KEY约束
    if primary_key:
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)}, PRIMARY KEY ({primary_key}))"
    else:
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
    
    print(f"执行SQL: {create_sql}")
    cursor.execute(create_sql)
    
    return table_name, field_names

def import_csv_to_table(cursor, csv_file, table_name, fields):
    """将CSV文件数据导入到表中"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # 读取CSV的标题行
        
        # 检查CSV标题行与JSON字段是否匹配
        if len(header) != len(fields):
            print(f"警告: {csv_file} 的列数({len(header)})与表定义的字段数({len(fields)})不匹配")
            print(f"CSV标题: {header}")
            print(f"表字段: {fields}")
            
            # 使用CSV标题作为实际字段
            actual_fields = header
        else:
            actual_fields = fields
        
        # 构建插入数据的SQL语句
        placeholders = ', '.join(['?' for _ in actual_fields])
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(actual_fields)}) VALUES ({placeholders})"
        
        # 批量插入数据
        rows = []
        for row in reader:
            # 确保行数据与字段数量匹配
            if len(row) != len(actual_fields):
                print(f"跳过不匹配的行: {row}")
                continue
            rows.append(row)
        
        if rows:
            cursor.executemany(insert_sql, rows)
            print(f"已导入 {len(rows)} 行数据到表 {table_name}")

def main():
    # 数据目录
    data_dir = os.path.dirname(os.path.abspath(__file__)) + '/table_headers_simulation'
    
    # 创建SQLite数据库
    db_path = os.path.join(os.path.dirname(data_dir), 'tables.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"创建数据库: {db_path}")
    
    # 获取所有CSV文件
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    for csv_file in csv_files:
        # 检查是否有对应的JSON文件
        json_file = csv_file.replace('.csv', '.json')
        if not os.path.exists(json_file):
            print(f"警告: {json_file} 不存在，跳过导入")
            continue
        
        # 创建表并导入数据
        result = create_table_from_json(cursor, json_file)
        if result[0] is None or result[1] is None:
            print(f"跳过导入: {json_file}")
            continue
            
        table_name, fields = result
        import_csv_to_table(cursor, csv_file, table_name, fields)
        
        print(f"已导入表: {table_name}")
    
    # 提交事务并关闭连接
    conn.commit()
    conn.close()
    
    print("所有CSV文件已成功导入SQLite数据库")

if __name__ == "__main__":
    main()