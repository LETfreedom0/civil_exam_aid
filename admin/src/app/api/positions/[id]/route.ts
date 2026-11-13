import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";
import { EDITABLE, resolveTable, tableName } from "@/lib/tables";

type Ctx = { params: Promise<{ id: string }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const { id } = await ctx.params;
  const table = tableName(req.nextUrl.searchParams.get("table"));
  const rows = await query(
    `SELECT t.*, ds.source_name
     FROM ${table} t
     LEFT JOIN data_sources ds ON ds.id = t.source_id
     WHERE t.id = $1`,
    [Number(id)]
  );
  if (!rows.length) {
    return NextResponse.json({ error: "未找到该岗位" }, { status: 404 });
  }
  return NextResponse.json({ item: rows[0] });
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const { id } = await ctx.params;
  const table = tableName(req.nextUrl.searchParams.get("table"));
  const body = (await req.json()) as Record<string, unknown>;

  const sets: string[] = [];
  const params: unknown[] = [];
  for (const [key, value] of Object.entries(body)) {
    if (!EDITABLE.has(key)) continue;
    params.push(value);
    sets.push(`${key} = $${params.length}`);
  }
  if (!sets.length) {
    return NextResponse.json({ error: "没有可更新字段" }, { status: 400 });
  }
  params.push(Number(id));
  const rows = await query(
    `UPDATE ${table} SET ${sets.join(", ")}, updated_at = now()
     WHERE id = $${params.length}
     RETURNING id, is_active, is_disability_only, remote_area, audience_tags`,
    params
  );
  if (!rows.length) {
    return NextResponse.json({ error: "未找到该岗位" }, { status: 404 });
  }
  return NextResponse.json({ item: rows[0] });
}
