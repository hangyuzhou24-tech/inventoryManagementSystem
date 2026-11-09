"""SQLite → MySQL 一次性数据迁移脚本。

用法：确保 MySQL 已启动且后端建过表（启动一次即可），然后运行：
    python migrate_sqlite_to_mysql.py
"""
import os

import pymysql
import sqlite3

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "erp.db")
MYSQL_CONF = dict(host="127.0.0.1", port=3306, user="erp",
                  password="erp123456", database="erp", charset="utf8mb4")

TABLES = [  # 顺序考虑外键依赖：主数据在前，业务数据在后
    ("users", "id, username, hashed_password, real_name, role, is_active, created_at"),
    ("warehouses", "id, name, is_default"),
    ("products", "id, sku, name, unit, barcode, purchase_price, sale_price, safety_stock, is_active, created_at"),
    ("suppliers", "id, code, name, contact, phone, payment_terms_days, created_at"),
    ("customers", "id, code, name, contact, phone, address, level, credit_limit, owner_id, public_at, total_sales, created_at"),
    ("inventory", "id, product_id, warehouse_id, qty_available, qty_locked"),
    ("stock_moves", "id, move_type, product_id, warehouse_id, qty, ref_no, remark, created_by, created_at"),
    ("purchase_orders", "id, order_no, supplier_id, status, total_amount, remark, created_by, created_at"),
    ("purchase_order_items", "id, order_id, product_id, qty, received_qty, price"),
    ("sales_orders", "id, order_no, customer_id, status, total_amount, pending_reason, remark, created_by, created_at, shipped_at"),
    ("sales_order_items", "id, order_id, product_id, qty, shipped_qty, price"),
    ("receivables", "id, order_no, customer_id, amount, paid_amount, status, due_date, created_at"),
    ("payables", "id, order_no, supplier_id, amount, paid_amount, status, due_date, created_at"),
    ("follow_ups", "id, customer_id, method, content, next_follow_at, created_by, created_at"),
]


def main():
    lite = sqlite3.connect(SQLITE_PATH)
    my = pymysql.connect(**MYSQL_CONF)
    total = 0
    with my.cursor() as cur:
        for table, cols in TABLES:
            # 清空目标表（保留结构），避免主键冲突
            cur.execute(f"DELETE FROM {table}")
            rows = lite.execute(f"SELECT {cols} FROM {table}").fetchall()
            if not rows:
                print(f"  {table}: 0 行，跳过")
                continue
            placeholders = ",".join(["%s"] * len(cols.split(",")))
            cur.executemany(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                [tuple(r) for r in rows],
            )
            total += len(rows)
            print(f"  {table}: {len(rows)} 行已迁移")
    my.commit()
    my.close()
    lite.close()
    print(f"\n迁移完成，共 {total} 行")


if __name__ == "__main__":
    main()
