import { NextRequest, NextResponse } from "next/server";

export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD ?? "";

export function checkAuth(req: NextRequest): NextResponse | null {
  // 未配置口令时直接放行（仅限本地开发）
  if (!ADMIN_PASSWORD) return null;
  const token = req.headers.get("x-admin-token") ?? "";
  if (token === ADMIN_PASSWORD) return null;
  return NextResponse.json({ error: "未授权" }, { status: 401 });
}
