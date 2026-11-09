"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getUser, getToken } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "经营看板", icon: "📊" },
  { href: "/products", label: "商品档案", icon: "📦" },
  { href: "/customers", label: "客户管理", icon: "👤" },
  { href: "/purchase", label: "采购管理", icon: "🚚" },
  { href: "/sales", label: "销售管理", icon: "💰" },
  { href: "/inventory", label: "库存查询", icon: "📋" },
];

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<{ role: string; real_name: string } | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    setUser(getUser());
  }, [router]);

  if (!user) return <div className="min-h-screen flex items-center justify-center text-gray-400">加载中...</div>;

  return (
    <div className="min-h-screen flex">
      <aside className="w-52 bg-slate-900 text-slate-200 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-slate-700">
          <div className="font-semibold">进销存系统</div>
          <div className="text-xs text-slate-400 mt-1">货 · 钱 · 客 一体化</div>
        </div>
        <nav className="flex-1 py-3">
          {NAV.map((n) => (
            <a
              key={n.href}
              href={n.href}
              className={`flex items-center gap-2.5 px-5 py-2.5 text-sm transition-colors ${
                pathname === n.href ? "bg-blue-600 text-white" : "hover:bg-slate-800"
              }`}
            >
              <span>{n.icon}</span>
              {n.label}
            </a>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-700 text-sm">
          <div className="text-slate-300">{user.real_name || "用户"}</div>
          <div className="text-xs text-slate-500 mt-0.5">角色：{user.role}</div>
          <button
            className="mt-3 text-xs text-slate-400 hover:text-white"
            onClick={() => {
              localStorage.removeItem("erp_token");
              localStorage.removeItem("erp_user");
              router.push("/login");
            }}
          >
            退出登录
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  );
}
