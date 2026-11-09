"use client";

import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";

export default function ProductsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState({ sku: "", name: "", unit: "件", purchase_price: 0, sale_price: 0, safety_stock: 0 });
  const [msg, setMsg] = useState("");

  const load = () => api("/products").then(setItems).catch((e) => setMsg(e.message));
  useEffect(() => { load(); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api("/products", { method: "POST", body: JSON.stringify(form) });
      setForm({ sku: "", name: "", unit: "件", purchase_price: 0, sale_price: 0, safety_stock: 0 });
      load();
    } catch (err: any) {
      setMsg(err.message);
    }
  }

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">商品档案</h1>
      <div className="grid grid-cols-3 gap-6">
        <div className="card col-span-2">
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">SKU</th><th className="th">名称</th><th className="th">单位</th>
                <th className="th">进价</th><th className="th">售价</th><th className="th">安全库存</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td className="td font-mono text-xs">{p.sku}</td>
                  <td className="td">{p.name}</td>
                  <td className="td">{p.unit}</td>
                  <td className="td">{fmtMoney(p.purchase_price)}</td>
                  <td className="td">{fmtMoney(p.sale_price)}</td>
                  <td className="td">{p.safety_stock}</td>
                </tr>
              ))}
              {items.length === 0 && <tr><td className="td text-gray-400" colSpan={6}>暂无商品</td></tr>}
            </tbody>
          </table>
        </div>
        <form onSubmit={submit} className="card space-y-3">
          <h2 className="text-sm font-medium">新增商品</h2>
          <input className="input" placeholder="SKU 编码" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} required />
          <input className="input" placeholder="商品名称" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <div className="grid grid-cols-2 gap-2">
            <input className="input" type="number" placeholder="进价" value={form.purchase_price} onChange={(e) => setForm({ ...form, purchase_price: +e.target.value })} />
            <input className="input" type="number" placeholder="售价" value={form.sale_price} onChange={(e) => setForm({ ...form, sale_price: +e.target.value })} />
          </div>
          <input className="input" type="number" placeholder="安全库存" value={form.safety_stock} onChange={(e) => setForm({ ...form, safety_stock: +e.target.value })} />
          {msg && <p className="text-xs text-red-600">{msg}</p>}
          <button className="btn-primary w-full">保存</button>
        </form>
      </div>
    </div>
  );
}
