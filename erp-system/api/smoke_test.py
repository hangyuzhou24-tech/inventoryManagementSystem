"""业务链路冒烟测试：采购入库 → 销售出库 → 应收核销 → 库存核对。"""
import requests

BASE = "http://127.0.0.1:8000/api/v1"
s = requests.Session()
ok, fail = 0, 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  PASS  {name}")
    else:
        fail += 1
        print(f"  FAIL  {name}  {detail}")


# 登录
r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
check("管理员登录", r.status_code == 200)
token = r.json()["access_token"]
s.headers["Authorization"] = f"Bearer {token}"

# 建基础数据
r = s.post(f"{BASE}/products", json={"sku": "SKU001", "name": "测试商品A", "unit": "件",
                                     "purchase_price": 10, "sale_price": 20, "safety_stock": 5})
check("创建商品", r.status_code == 200 and "id" in r.json(), r.text)
pid = r.json()["id"]

r = s.post(f"{BASE}/suppliers", json={"code": "S001", "name": "测试供应商"})
check("创建供应商", r.status_code == 200, r.text)
sid = r.json()["id"]

r = s.post(f"{BASE}/customers", json={"code": "C001", "name": "测试客户", "credit_limit": 5000})
check("创建客户", r.status_code == 200, r.text)
cid = r.json()["id"]

# 采购：下采购单 100 件 @10
r = s.post(f"{BASE}/purchase-orders", json={"supplier_id": sid,
            "items": [{"product_id": pid, "qty": 100, "price": 10}]})
check("创建采购单", r.status_code == 200, r.text)
po = r.json()

# 部分到货 60 件
r = s.post(f"{BASE}/purchase-orders/{po['id']}/receive",
           json={"items": [{"product_id": pid, "qty": 60, "price": 10}]})
check("部分入库 60 件", r.status_code == 200 and r.json()["status"] == "RECEIVING", r.text)

# 剩余 40 件全部入库（单据应关闭）
r = s.post(f"{BASE}/purchase-orders/{po['id']}/receive", json={})
check("全部入库后单据 CLOSED", r.status_code == 200 and r.json()["status"] == "CLOSED", r.text)

# 库存核对
r = s.get(f"{BASE}/inventory/summary")
inv = [x for x in r.json() if x["product_id"] == pid]
check("库存 = 100", inv and inv[0]["qty_available"] == 100, r.text)
check("生成应付 1000 元", s.get(f"{BASE}/payables").json()[0]["amount"] == 1000)

# 销售：下 30 件 @20 的销售单
r = s.post(f"{BASE}/sales-orders", json={"customer_id": cid,
            "items": [{"product_id": pid, "qty": 30, "price": 20}]})
check("创建销售单", r.status_code == 200, r.text)
so = r.json()
check("金额 = 600", so["total_amount"] == 600)

# 库存不足场景：下 99999 件应失败
r = s.post(f"{BASE}/sales-orders", json={"customer_id": cid,
            "items": [{"product_id": pid, "qty": 99999, "price": 20}]})
big_so = r.json()
r2 = s.post(f"{BASE}/sales-orders/{big_so['id']}/approve")
check("库存不足预占被拦截", r2.status_code == 400, r2.text)
s.post(f"{BASE}/sales-orders/{big_so['id']}/cancel")

# 审核（预占库存）→ 出库
r = s.post(f"{BASE}/sales-orders/{so['id']}/approve")
check("审核通过并预占库存", r.status_code == 200 and r.json()["status"] == "APPROVED", r.text)
r = s.get(f"{BASE}/inventory/summary")
inv = [x for x in r.json() if x["product_id"] == pid][0]
check("预占后 可用70/锁定30", inv["qty_available"] == 70 and inv["qty_locked"] == 30, str(inv))

r = s.post(f"{BASE}/sales-orders/{so['id']}/ship")
check("销售出库", r.status_code == 200 and r.json()["status"] == "SHIPPED", r.text)

r = s.get(f"{BASE}/inventory/summary")
inv = [x for x in r.json() if x["product_id"] == pid][0]
check("出库后 可用70/锁定0", inv["qty_available"] == 70 and inv["qty_locked"] == 0, str(inv))

# 生成应收并核销
r = s.get(f"{BASE}/receivables")
rec = r.json()[0]
check("生成应收 600 元", rec["amount"] == 600, r.text)
r = s.post(f"{BASE}/receivables/{rec['id']}/payment", json={"amount": 600})
check("收款核销结清", r.status_code == 200 and r.json()["status"] == "SETTLED", r.text)

# 安全库存预警（库存 70 > 安全库存 5，不应预警）
r = s.get(f"{BASE}/inventory/alerts")
check("无库存预警", len(r.json()) == 0, r.text)

# CRM 跟进
r = s.post(f"{BASE}/customers/{cid}/follow-ups",
           json={"method": "phone", "content": "电话回访，客户满意"})
check("新增跟进记录", r.status_code == 200, r.text)
r = s.get(f"{BASE}/customers/{cid}/overview")
check("360°视图含订单与跟进", len(r.json()["orders"]) >= 1 and len(r.json()["follow_ups"]) == 1)

# 看板
r = s.get(f"{BASE}/reports/dashboard")
check("看板月销售额 = 600", r.json()["month_sales"] == 600, r.text)

print(f"\n结果：{ok} 通过 / {fail} 失败")
exit(1 if fail else 0)
