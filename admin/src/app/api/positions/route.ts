import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";
import { resolveTable, tableName } from "@/lib/tables";

export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const sp = req.nextUrl.searchParams;
  const t = resolveTable(sp.get("table"));
  const table = tableName(t);

  const q = sp.get("q")?.trim();
  const province = sp.get("province")?.trim();
  const year = sp.get("year")?.trim();
  const source = sp.get("source")?.trim();
  const disability = sp.get("disability");
  const remote = sp.get("remote");
  const active = sp.get("active");
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const pageSize = Math.min(100, Math.max(1, Number(sp.get("pageSize") ?? 20)));

  const where: string[] = [];
  const params: unknown[] = [];
  const add = (v: unknown) => {
    params.push(v);
    return `$${params.length}`;
  };

  if (q) {
    const p = add(`%${q}%`);
    where.push(`(t.position_name ILIKE ${p} OR t.recruit_unit ILIKE ${p} OR t.position_code ILIKE ${p} OR t.region_dept ILIKE ${p})`);
  }
  if (province) where.push(`t.province_code = ${add(province)}`);
  if (year) where.push(`t.year = ${add(Number(year))}`);
  if (source === "none") where.push(`t.source_id IS NULL`);
  else if (source) where.push(`t.source_id = ${add(Number(source))}`);
  if (disability === "1") where.push(`t.is_disability_only = true`);
  if (remote === "1") where.push(`t.remote_area = true`);
  if (active === "1") where.push(`t.is_active = true`);
  if (active === "0") where.push(`t.is_active = false`);

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";

  const [countRow] = await query<{ total: string }>(
    `SELECT count(*) AS total FROM ${table} t ${whereSql}`,
    params
  );
  const items = await query(
    `SELECT t.id, t.region_dept, t.recruit_unit, t.position_name,
            t.position_code, t.position_nature, t.quota, t.position_type,
            t.education, t.major, t.year, t.city, t.province_code,
            t.is_disability_only, t.remote_area, t.is_active,
            t.audience_tags, t.source_id, ds.source_name,
            t.announcement_id, t.source_url,
            a.title AS announcement_title, a.exam_type AS announcement_exam_type,
            t.updated_at
     FROM ${table} t
     LEFT JOIN data_sources ds ON ds.id = t.source_id
     LEFT JOIN announcements a ON a.id = t.announcement_id
     ${whereSql}
     ORDER BY t.year DESC NULLS LAST, t.province_code, t.id ASC
     LIMIT ${pageSize} OFFSET ${(page - 1) * pageSize}`,
    params
  );

  return NextResponse.json({
    table: t,
    items,
    total: Number(countRow?.total ?? 0),
    page,
    pageSize,
  });
}
