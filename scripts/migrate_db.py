#!/usr/bin/env python3
"""
数据库迁移脚本：添加缺失的字段
"""
import sqlite3
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    conn = sqlite3.connect('instance/store.db')
    cursor = conn.cursor()
    
    print("开始数据库迁移...")
    
    # 1. 为 purchase_orders 表添加 updated_at 列
    try:
        cursor.execute("ALTER TABLE purchase_orders ADD COLUMN updated_at DATETIME")
        print("✓ 为 purchase_orders 表添加 updated_at 列")
        
        # 为现有数据设置默认值
        cursor.execute("UPDATE purchase_orders SET updated_at = created_at WHERE updated_at IS NULL")
        print("✓ 更新 purchase_orders 表的现有数据")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ purchase_orders.updated_at 列已存在")
        else:
            print(f"✗ 添加 purchase_orders.updated_at 列失败: {e}")
    
    # 2. 为 sales_orders 表添加 updated_at 列
    try:
        cursor.execute("ALTER TABLE sales_orders ADD COLUMN updated_at DATETIME")
        print("✓ 为 sales_orders 表添加 updated_at 列")
        
        # 为现有数据设置默认值
        cursor.execute("UPDATE sales_orders SET updated_at = created_at WHERE updated_at IS NULL")
        print("✓ 更新 sales_orders 表的现有数据")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ sales_orders.updated_at 列已存在")
        else:
            print(f"✗ 添加 sales_orders.updated_at 列失败: {e}")
    
    # 3. 为 stock_ins 表添加 status 列
    try:
        cursor.execute("ALTER TABLE stock_ins ADD COLUMN status VARCHAR(20)")
        print("✓ 为 stock_ins 表添加 status 列")
        
        # 为现有数据设置默认值：如果已经有库存流水记录，则标记为 completed，否则为 draft
        cursor.execute("""
            UPDATE stock_ins 
            SET status = CASE 
                WHEN EXISTS (
                    SELECT 1 FROM stock_logs 
                    WHERE reference_type = 'stock_in' AND reference_id = stock_ins.id
                ) THEN 'completed' 
                ELSE 'draft' 
            END
            WHERE status IS NULL
        """)
        print("✓ 更新 stock_ins 表的现有数据状态")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ stock_ins.status 列已存在")
        else:
            print(f"✗ 添加 stock_ins.status 列失败: {e}")
    
    # 4. 为 stock_ins 表添加 updated_at 列
    try:
        cursor.execute("ALTER TABLE stock_ins ADD COLUMN updated_at DATETIME")
        print("✓ 为 stock_ins 表添加 updated_at 列")
        
        # 为现有数据设置默认值
        cursor.execute("UPDATE stock_ins SET updated_at = created_at WHERE updated_at IS NULL")
        print("✓ 更新 stock_ins 表的现有数据")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ stock_ins.updated_at 列已存在")
        else:
            print(f"✗ 添加 stock_ins.updated_at 列失败: {e}")
    
    # 5. 为 stock_outs 表添加 status 列
    try:
        cursor.execute("ALTER TABLE stock_outs ADD COLUMN status VARCHAR(20) DEFAULT 'draft'")
        print("✓ 为 stock_outs 表添加 status 列")
        
        # 为现有数据设置默认值
        cursor.execute("""
            UPDATE stock_outs 
            SET status = CASE 
                WHEN EXISTS (
                    SELECT 1 FROM stock_logs 
                    WHERE reference_type = 'stock_out' AND reference_id = stock_outs.id
                ) THEN 'completed' 
                ELSE 'draft' 
            END
            WHERE status IS NULL
        """)
        print("✓ 更新 stock_outs 表的现有数据状态")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ stock_outs.status 列已存在")
        else:
            print(f"✗ 添加 stock_outs.status 列失败: {e}")
    
    # 6. 为 stock_outs 表添加 updated_at 列
    try:
        cursor.execute("ALTER TABLE stock_outs ADD COLUMN updated_at DATETIME")
        print("✓ 为 stock_outs 表添加 updated_at 列")
        
        # 为现有数据设置默认值
        cursor.execute("UPDATE stock_outs SET updated_at = created_at WHERE updated_at IS NULL")
        print("✓ 更新 stock_outs 表的现有数据")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ stock_outs.updated_at 列已存在")
        else:
            print(f"✗ 添加 stock_outs.updated_at 列失败: {e}")
    
    conn.commit()
    conn.close()
    print("数据库迁移完成！")

if __name__ == '__main__':
    migrate_database()