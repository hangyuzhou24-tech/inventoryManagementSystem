"use client";

import { useEffect, useState } from "react";
import { api, fmtMoney, statusMap } from "@/lib/api";

export default function SalesPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState({ customer_id: 0, items: [{ product_id: 0, qty: 1, price: 0 }] });

  async function load() {
    const [so, cust, prod] = await Promise.all([
      api("/sales-orders"), api("/customers"), api("/products"),
    ]);
    setOrders(so); setCustomers(cust); setProducts(prod);
  }
  useEffect(() => { load().catch((e) => setMsg(e.message)); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      const res = await api("/sales-orders", { method: "POST", body: JSON.stringify(form) });
      if (res.credit_warning) setMsg(`注意：${res.pending_reason}，订单已转入待审批`);
      setForm({ customer_id: 0, items: [{ product_id: 0, qty: 1, price: 0 }] });
      load();
    } catch (err: any) { setMsg(err.message); }
  }

  async function act(id: number, action: string) {
    setMsg("");
    try {
      await api(`/sales-orders/${id}/${action}`, { method: "POST" });
      load();
    } catch (err: any) { setMsg(err.message); }
  }

  const statusColor: Record<string, string> = {
    DRAFT: "bg-gray-100 text-gray-600",
    PENDING_APPROVAL: "bg-amber-100 text-amber-700",
    APPROVED: "bg-blue-100 text-blue-700",
    SHIPPED: "bg-green-100 text-green-700",
    CLOSED: "bg-slate-100 text-slate-500",
    CANCELLED: "bg-red-100 text-red-600",
  };

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">销售管理</h1>
      {msg && <p className="text-sm text-red-600 mb-3">{msg}</p>}
      <div className="card mb-6">
        <h2 className="text-sm font-medium mb-3">销售单列表</h2>
        <table className="w-full">
          <thead>
            <tr><th className="th">单号</th><th className="th">金额</th><th className="th">状态</th><th className="th">创建时间</th><th className="th">操作</th></tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td className="td font-mono text-xs">{o.order_no}</td>
                <td className="td">{fmtMoney(o.total_amount)}</td>
                <td className="td"><span className={`badge ${statusColor[o.status]}`}>{statusMap[o.status] || o.status}</span></td>
                <td className="td text-gray-500">{new Date(o.created_at).toLocaleString("zh-CN")}</td>
                <td className="td space-x-1">
                  {(o.status === "DRAFT" || o.status === "PENDING_APPROVAL") && (
                    <button className="btn-outline !py-1 !px-3 text-xs" onClick={() => act(o.id, "approve")}>审核</button>
                  )}
                  {o.status === "APPROVED" && (
                    <button className="btn-primary !py-1 !px-3 text-xs" onClick={() => act(o.id, "ship")}>出库</button>
                  )}
                  {["DRAFT", "PENDING_APPROVAL", "APPROVED"].includes(o.status) && (
                    <button className="btn-outline !py-1 !px-3 text-xs !text-red-600" onClick={() => act(o.id, "cancel")}>取消</button>
                  )}
                </td>
              </tr>
            ))}
            {orders.length === 0 && <tr><td className="td text-gray-400" colSpan={5}>暂无销售单</td></tr>}
          </tbody>
        </table>
      </div>

      <form onSubmit={submit} className="card">
        <h2 className="text-sm font-medium mb-3">新建销售单</h2>
        <select className="input mb-3" value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: +e.target.value })} required>
          <option value={0}>选择客户</option>
          {customers.map((c) => <option key={c.id} value={c.id}>{c.name}（额度 {fmtMoney(c.credit_limit)}）</option>)}
        </select>
        {form.items.map((it, idx) => (
          <div key={idx} className="grid grid-cols-4 gap-2 mb-2">
            <select className="input" value={it.product_id} onChange={(e) => {
              const items = [...form.items];
              items[idx] = { ...it, product_id: +e.target.value, price: products.find((p) => p.id === +e.target.value)?.sale_price || 0 };
              setForm({ ...form, items });
            }} required>
              <option value={0}>选择商品</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <input className="input" type="number" min={1} value={it.qty} onChange={(e) => {
              const items = [...form.items]; items[idx] = { ...it, qty: +e.target.value };
              setForm({ ...form, items });
            }} />
            <input className="input" type="number" min={0} step="0.01" value={it.price} onChange={(e) => {
              const items = [...form.items]; items[idx] = { ...it, price: +e.target.value };
              setForm({ ...form, items });
            }} />
            <button type="button" className="btn-outline" onClick={() => setForm({ ...form, items: form.items.filter((_, i) => i !== idx) })} disabled={form.items.length === 1}>删除行</button>
          </div>
        ))}
        <div className="flex gap-2 mt-2">
          <button type="button" className="btn-outline" onClick={() => setForm({ ...form, items: [...form.items, { product_id: 0, qty: 1, price: 0 }] })}>+ 添加商品行</button>
          <button className="btn-primary">提交销售单</button>
        </div>
        <p className="text-xs text-gray-400 mt-2">提交后需「审核」（预占库存）→「出库」（扣减库存并生成应收）</p>
      </form>
    </div>
  );
}
