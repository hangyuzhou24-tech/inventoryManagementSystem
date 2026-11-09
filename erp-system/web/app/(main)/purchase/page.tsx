"use client";

import { useEffect, useState } from "react";
import { api, fmtMoney, statusMap } from "@/lib/api";

export default function PurchasePage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState({ supplier_id: 0, items: [{ product_id: 0, qty: 1, price: 0 }] });

  async function load() {
    const [po, sup, prod] = await Promise.all([
      api("/purchase-orders"), api("/suppliers"), api("/products"),
    ]);
    setOrders(po); setSuppliers(sup); setProducts(prod);
  }
  useEffect(() => { load().catch((e) => setMsg(e.message)); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api("/purchase-orders", { method: "POST", body: JSON.stringify(form) });
      setForm({ supplier_id: 0, items: [{ product_id: 0, qty: 1, price: 0 }] });
      load();
    } catch (err: any) { setMsg(err.message); }
  }

  async function receive(id: number) {
    setMsg("");
    try {
      await api(`/purchase-orders/${id}/receive`, { method: "POST", body: JSON.stringify({}) });
      load();
    } catch (err: any) { setMsg(err.message); }
  }

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">采购管理</h1>
      {msg && <p className="text-sm text-red-600 mb-3">{msg}</p>}
      <div className="card mb-6">
        <h2 className="text-sm font-medium mb-3">采购单列表</h2>
        <table className="w-full">
          <thead>
            <tr><th className="th">单号</th><th className="th">金额</th><th className="th">状态</th><th className="th">创建时间</th><th className="th">操作</th></tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td className="td font-mono text-xs">{o.order_no}</td>
                <td className="td">{fmtMoney(o.total_amount)}</td>
                <td className="td">{statusMap[o.status] || o.status}</td>
                <td className="td text-gray-500">{new Date(o.created_at).toLocaleString("zh-CN")}</td>
                <td className="td">
                  {(o.status === "DRAFT" || o.status === "RECEIVING") && (
                    <button className="btn-outline !py-1 !px-3 text-xs" onClick={() => receive(o.id)}>入库</button>
                  )}
                </td>
              </tr>
            ))}
            {orders.length === 0 && <tr><td className="td text-gray-400" colSpan={5}>暂无采购单</td></tr>}
          </tbody>
        </table>
      </div>

      <form onSubmit={submit} className="card">
        <h2 className="text-sm font-medium mb-3">新建采购单</h2>
        <select className="input mb-3" value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: +e.target.value })} required>
          <option value={0}>选择供应商</option>
          {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        {form.items.map((it, idx) => (
          <div key={idx} className="grid grid-cols-4 gap-2 mb-2">
            <select className="input" value={it.product_id} onChange={(e) => {
              const items = [...form.items];
              items[idx] = { ...it, product_id: +e.target.value, price: products.find((p) => p.id === +e.target.value)?.purchase_price || 0 };
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
          <button className="btn-primary">提交采购单</button>
        </div>
      </form>
    </div>
  );
}
