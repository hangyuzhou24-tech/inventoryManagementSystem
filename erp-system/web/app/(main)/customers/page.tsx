"use client";

import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";

export default function CustomersPage() {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState({ code: "", name: "", contact: "", phone: "", credit_limit: 0 });
  const [msg, setMsg] = useState("");

  const load = () => api("/customers").then(setItems).catch((e) => setMsg(e.message));
  useEffect(() => { load(); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api("/customers", { method: "POST", body: JSON.stringify(form) });
      setForm({ code: "", name: "", contact: "", phone: "", credit_limit: 0 });
      load();
    } catch (err: any) {
      setMsg(err.message);
    }
  }

  const levelColor: Record<string, string> = {
    A: "bg-green-100 text-green-700",
    B: "bg-blue-100 text-blue-700",
    C: "bg-gray-100 text-gray-600",
  };

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">客户管理</h1>
      <div className="grid grid-cols-3 gap-6">
        <div className="card col-span-2">
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">编码</th><th className="th">名称</th><th className="th">联系人</th>
                <th className="th">等级</th><th className="th">信用额度</th><th className="th">累计销售</th>
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.id}>
                  <td className="td font-mono text-xs">{c.code}</td>
                  <td className="td">{c.name}</td>
                  <td className="td">{c.contact || "-"}</td>
                  <td className="td"><span className={`badge ${levelColor[c.level]}`}>{c.level}</span></td>
                  <td className="td">{fmtMoney(c.credit_limit)}</td>
                  <td className="td">{fmtMoney(c.total_sales)}</td>
                </tr>
              ))}
              {items.length === 0 && <tr><td className="td text-gray-400" colSpan={6}>暂无客户</td></tr>}
            </tbody>
          </table>
        </div>
        <form onSubmit={submit} className="card space-y-3">
          <h2 className="text-sm font-medium">新增客户</h2>
          <input className="input" placeholder="客户编码" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
          <input className="input" placeholder="客户名称" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="input" placeholder="联系人" value={form.contact} onChange={(e) => setForm({ ...form, contact: e.target.value })} />
          <input className="input" placeholder="电话" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="input" type="number" placeholder="信用额度" value={form.credit_limit} onChange={(e) => setForm({ ...form, credit_limit: +e.target.value })} />
          {msg && <p className="text-xs text-red-600">{msg}</p>}
          <button className="btn-primary w-full">保存</button>
        </form>
      </div>
    </div>
  );
}
