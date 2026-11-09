"use client";

import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/reports/dashboard").then(setData).catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;
  if (!data) return <p className="text-gray-400">加载中...</p>;

  const cards = [
    { label: "今日销售额", value: fmtMoney(data.today_sales), color: "bg-blue-50 text-blue-700" },
    { label: "本月销售额", value: fmtMoney(data.month_sales), color: "bg-indigo-50 text-indigo-700" },
    { label: "应收余额", value: fmtMoney(data.receivable_open), color: "bg-amber-50 text-amber-700" },
    { label: "应付余额", value: fmtMoney(data.payable_open), color: "bg-orange-50 text-orange-700" },
    { label: "客户数", value: data.customer_count, color: "bg-emerald-50 text-emerald-700" },
    { label: "商品数", value: data.product_count, color: "bg-teal-50 text-teal-700" },
    { label: "库存预警", value: data.low_stock_count, color: data.low_stock_count > 0 ? "bg-red-50 text-red-700" : "bg-gray-50 text-gray-600" },
  ];

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">经营看板</h1>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {cards.map((c) => (
          <div key={c.label} className="card">
            <div className="text-xs text-gray-500">{c.label}</div>
            <div className={`inline-block mt-2 px-3 py-1.5 rounded-lg text-lg font-semibold ${c.color}`}>
              {c.value}
            </div>
          </div>
        ))}
      </div>
      <div className="card">
        <h2 className="text-sm font-medium mb-3">最近销售订单</h2>
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">单号</th>
              <th className="th">客户</th>
              <th className="th">金额</th>
              <th className="th">状态</th>
              <th className="th">创建时间</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_orders.map((o: any) => (
              <tr key={o.order_no}>
                <td className="td font-mono text-xs">{o.order_no}</td>
                <td className="td">{o.customer}</td>
                <td className="td">{fmtMoney(o.total_amount)}</td>
                <td className="td">{o.status}</td>
                <td className="td text-gray-500">{new Date(o.created_at).toLocaleString("zh-CN")}</td>
              </tr>
            ))}
            {data.recent_orders.length === 0 && (
              <tr><td className="td text-gray-400" colSpan={5}>暂无订单</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
