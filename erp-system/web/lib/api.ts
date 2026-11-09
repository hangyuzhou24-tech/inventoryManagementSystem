const API = "http://127.0.0.1:8000/api/v1";

export type Token = { access_token: string; role: string; real_name: string };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("erp_token");
}

export function getUser(): { role: string; real_name: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("erp_user");
  return raw ? JSON.parse(raw) : null;
}

export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (res.status === 401) {
    localStorage.removeItem("erp_token");
    localStorage.removeItem("erp_user");
    window.location.href = "/login";
    throw new Error("未登录");
  }
  if (!res.ok) {
    throw new Error(body.detail || `请求失败 (${res.status})`);
  }
  return body as T;
}

export async function login(username: string, password: string): Promise<Token> {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "登录失败");
  localStorage.setItem("erp_token", body.access_token);
  localStorage.setItem("erp_user", JSON.stringify({ role: body.role, real_name: body.real_name }));
  return body;
}

export const fmtMoney = (n: number) => `¥${n.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const statusMap: Record<string, string> = {
  DRAFT: "草稿",
  PENDING_APPROVAL: "待审批",
  APPROVED: "已审核",
  SHIPPED: "已出库",
  CLOSED: "已关闭",
  CANCELLED: "已取消",
  RECEIVING: "入库中",
  OPEN: "未结清",
  PARTIAL: "部分核销",
  SETTLED: "已结清",
};
