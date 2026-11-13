import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";
import { resolveTable, tableName } from "@/lib/tables";

/**
 * 按考试年度 × 省份 汇总，供分组浏览与筛选下拉使用。
 */
export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const t = resolveTable(req.nextUrl.searchParams.get("table"));
  const table = tableName(t);

  const groups = await query<{
    year: number | null;
    province_code: string | null;
    province_name: string | null;
    total: string;
    disability_only: string;
  }>(`
    SELECT t.year, t.province_code,
           COALESCE(pr.name, t.province_code) AS province_name,
           count(*) AS total,
           count(*) FILTER (WHERE t.is_disability_only) AS disability_only
    FROM ${table} t
    LEFT JOIN provinces pr ON pr.code = t.province_code
    GROUP BY t.year, t.province_code, pr.name
    ORDER BY t.year DESC NULLS LAST, count(*) DESC
  `);

  const years = await query<{ year: number; total: string }>(`
    SELECT year, count(*) AS total FROM ${table}
    GROUP BY year ORDER BY year DESC NULLS LAST
  `);

  const provinces = await query<{ province_code: string; province_name: string; total: string }>(`
    SELECT t.province_code,
           COALESCE(pr.name, t.province_code) AS province_name,
           count(*) AS total
    FROM ${table} t
    LEFT JOIN provinces pr ON pr.code = t.province_code
    GROUP BY t.province_code, pr.name
    ORDER BY count(*) DESC
  `);

  return NextResponse.json({
    table: t,
    groups: groups.map((g) => ({
      year: g.year,
      province_code: g.province_code,
      province_name: g.province_name,
      total: Number(g.total),
      disability_only: Number(g.disability_only),
    })),
    years: years.map((y) => ({ year: y.year, total: Number(y.total) })),
    provinces: provinces.map((p) => ({
      province_code: p.province_code,
      province_name: p.province_name,
      total: Number(p.total),
    })),
  });
}
