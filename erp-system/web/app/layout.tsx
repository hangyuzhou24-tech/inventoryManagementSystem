import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "进销存管理系统",
  description: "进销存 + 客户管理一体化系统",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
