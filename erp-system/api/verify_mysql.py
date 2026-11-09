"""MySQL 切换后的端到端验证：登录 → 采购入库 → 销售出库 → 核销。"""
import time
import requests

BASE = "http://127.0.0.1:8000/api/v1"
uid = str(int(time.time()))[-6:]  # 唯一后缀避免编码冲突
s = requests.Session()
ok, fail = 0, 0


def check(name, cond, detail=""):
    global ok, fail
    ok += 1 if cond else 0
    fail += 0 if cond else 1
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {'' if cond else detail}")


r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
check("登录", r.status_code == 200)
s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

r = s.post(f"{BASE}/products", json={"sku": f"MYSQL{uid}", "name": "MySQL验证商品",
                                     "purchase_price": 5, "sale_price": 12, "safety_stock": 2})
check("创建商品", r.status_code == 200, r.text)
pid = r.json()["id"]

r = s.post(f"{BASE}/suppliers", json={"code": f"MS{uid}", "name": "MySQL验证供应商"})
sid = r.json()["id"]
r = s.post(f"{BASE}/customers", json={"code": f"MC{uid}", "name": "MySQL验证客户", "credit_limit": 9999})
cid = r.json()["id"]

r = s.post(f"{BASE}/purchase-orders", json={"supplier_id": sid,
            "items": [{"product_id": pid, "qty": 50, "price": 5}]})
po = r.json()
check("创建采购单", r.status_code == 200, r.text)
r = s.post(f"{BASE}/purchase-orders/{po['id']}/receive", json={})
check("采购入库(关闭)", r.json().get("status") == "CLOSED", r.text)

r = s.post(f"{BASE}/sales-orders", json={"customer_id": cid,
            "items": [{"product_id": pid, "qty": 10, "price": 12}]})
so = r.json()
s.post(f"{BASE}/sales-orders/{so['id']}/approve")
r = s.post(f"{BASE}/sales-orders/{so['id']}/ship")
check("审核+出库", r.json().get("status") == "SHIPPED", r.text)

r = s.get(f"{BASE}/inventory/summary")
inv = [x for x in r.json() if x["product_id"] == pid][0]
check("库存核对 可用40/锁定0", inv["qty_available"] == 40 and inv["qty_locked"] == 0, str(inv))

r = s.get(f"{BASE}/receivables")
rec = [x for x in r.json() if x["order_no"] == so["order_no"]][0]
r = s.post(f"{BASE}/receivables/{rec['id']}/payment", json={"amount": 120})
check("收款核销 120 元", r.json().get("status") == "SETTLED", r.text)

# 验证数据确实落在 MySQL
import pymysql
con = pymysql.connect(host="127.0.0.1", user="erp", password="erp123456",
                      database="erp", charset="utf8mb4")
n = con.execute = None
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM stock_moves")
moves = cur.fetchone()[0]
check(f"MySQL 中 stock_moves 共 {moves} 条流水", moves >= 5)
cur.execute("SELECT qty_available FROM inventory WHERE product_id=%s", (pid,))
check("MySQL inventory 数据正确", cur.fetchone()[0] == 40)
con.close()

print(f"\n结果：{ok} 通过 / {fail} 失败")
exit(1 if fail else 0)
