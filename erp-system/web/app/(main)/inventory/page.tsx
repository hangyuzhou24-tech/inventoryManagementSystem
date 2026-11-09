"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function InventoryPage() {
  const [summary, setSummary] = useState<any[]>([]);
  const [moves, setMoves] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [tab, setTab] = useState<"summary" | "moves" | "alerts">("summary");
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api("/inventory/summary"), api("/inventory/moves"), api("/inventory/alerts")])
      .then(([s, m, a]) => { setSummary(s); setMoves(m); setAlerts(a); })
      .catch((e) => setErr(e.message));
  }, []);

  const moveTypeMap: Record<string, string> = {
    PURCHASE_IN: "采购入库", SALES_OUT: "销售出库",
    SALES_RETURN: "销售退货", PURCHASE_RETURN: "采购退货", ADJUST: "盘点调整",
  };

  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">库存查询</h1>
      <div className="flex gap-2 mb-4">
        {([["summary", "库存汇总"], ["moves", "出入库流水"], ["alerts", `库存预警(${alerts.length})`]] as const).map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`btn ${tab === k ? "bg-blue-600 text-white" : "border border-gray-300 bg-white"}`}>
            {label}
          </button>
        ))}
      </div>

      {tab === "summary" && (
        <div className="card">
          <table className="w-full">
            <thead>
              <tr><th className="th">SKU</th><th className="th">商品</th><th className="th">仓库</th><th className="th">可用量</th><th className="th">锁定量</th><th className="th">安全库存</th></tr>
            </thead>
            <tbody>
              {summary.map((r, i) => (
                <tr key={i}>
                  <td className="td font-mono text-xs">{r.sku}</td>
                  <td className="td">{r.product_name}</td>
                  <td className="td">{r.warehouse_name}</td>
                  <td className={`td font-semibold ${r.qty_available < r.safety_stock ? "text-red-600" : ""}`}>{r.qty_available}</td>
                  <td className="td">{r.qty_locked}</td>
                  <td className="td text-gray-500">{r.safety_stock}</td>
                </tr>
              ))}
              {summary.length === 0 && <tr><td className="td text-gray-400" colSpan={6}>暂无库存记录（完成采购入库后显示）</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === "moves" && (
        <div className="card">
          <table className="w-full">
            <thead>
              <tr><th className="th">时间</th><th className="th">类型</th><th className="th">数量</th><th className="th">关联单号</th><th className="th">备注</th></tr>
            </thead>
            <tbody>
              {moves.map((m) => (
                <tr key={m.id}>
                  <td className="td text-gray-500">{new Date(m.created_at).toLocaleString("zh-CN")}</td>
                  <td className="td">{moveTypeMap[m.move_type] || m.move_type}</td>
                  <td className={`td font-semibold ${m.qty < 0 ? "text-red-600" : "text-green-700"}`}>{m.qty > 0 ? `+${m.qty}` : m.qty}</td>
                  <td className="td font-mono text-xs">{m.ref_no}</td>
                  <td className="td text-gray-500">{m.remark}</td>
                </tr>
              ))}
              {moves.length === 0 && <tr><td className="td text-gray-400" colSpan={5}>暂无流水</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === "alerts" && (
        <div className="card">
          <table className="w-full">
            <thead>
              <tr><th className="th">SKU</th><th className="th">商品</th><th className="th">当前可用</th><th className="th">安全库存</th><th className="th">缺口</th></tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.product_id}>
                  <td className="td font-mono text-xs">{a.sku}</td>
                  <td className="td">{a.product_name}</td>
                  <td className="td text-red-600 font-semibold">{a.qty_available}</td>
                  <td className="td">{a.safety_stock}</td>
                  <td className="td text-red-600">-{a.shortage}</td>
                </tr>
              ))}
              {alerts.length === 0 && <tr><td className="td text-gray-400" colSpan={5}>一切正常，无库存预警</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
