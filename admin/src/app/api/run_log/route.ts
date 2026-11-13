import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";

export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const page = Math.max(1, Number(req.nextUrl.searchParams.get("page") ?? 1));
  const pageSize = Math.min(100, Math.max(1, Number(req.nextUrl.searchParams.get("pageSize") ?? 20)));

  const [countRow] = await query<{ total: string }>(
    `SELECT count(*) AS total FROM run_log`
  );
  const items = await query(
    `SELECT * FROM run_log ORDER BY created_at DESC LIMIT ${pageSize} OFFSET ${(page - 1) * pageSize}`
  );
  return NextResponse.json({
    items,
    total: Number(countRow?.total ?? 0),
    page,
    pageSize,
  });
}
