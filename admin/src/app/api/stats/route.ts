import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";

type Summary = {
  total: string;
  active: string;
  disability_only: string;
  remote_area: string;
  linked: string;
  latest: string | null;
};

async function summarize(table: string): Promise<Summary> {
  const [row] = await query<Summary>(`
    SELECT count(*) AS total,
           count(*) FILTER (WHERE is_active) AS active,
           count(*) FILTER (WHERE is_disability_only) AS disability_only,
           count(*) FILTER (WHERE remote_area) AS remote_area,
           count(*) FILTER (WHERE source_url IS NOT NULL) AS linked,
           max(updated_at) AS latest
    FROM ${table}
  `);
  return row;
}

/**
 * 概览：全量库（主）与存量库（历史）分开统计，互不混淆。
 */
export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const full = await summarize("positions_full");
  const legacy = await summarize("positions");

  const fullGroups = await query<{
    year: number | null;
    province_code: string | null;
    province_name: string | null;
    n: string;
    dis: string;
  }>(`
    SELECT t.year, t.province_code,
           COALESCE(pr.name, t.province_code) AS province_name,
           count(*) AS n,
           count(*) FILTER (WHERE t.is_disability_only) AS dis
    FROM positions_full t
    LEFT JOIN provinces pr ON pr.code = t.province_code
    GROUP BY t.year, t.province_code, pr.name
    ORDER BY t.year DESC NULLS LAST, count(*) DESC
  `);

  const fullYears = await query<{ year: number; n: string }>(`
    SELECT year, count(*) AS n FROM positions_full GROUP BY year ORDER BY year DESC NULLS LAST
  `);

  const legacyByProvince = await query<{
    province_code: string | null;
    province_name: string | null;
    n: string;
    dis: string;
  }>(`
    SELECT p.province_code, COALESCE(pr.name, p.province_code) AS province_name,
           count(*) AS n,
           count(*) FILTER (WHERE p.is_disability_only) AS dis
    FROM positions p
    LEFT JOIN provinces pr ON pr.code = p.province_code
    GROUP BY p.province_code, pr.name
    ORDER BY count(*) DESC
  `);

  const sources = await query<{
    id: number;
    source_name: string | null;
    province_code: string | null;
    n: string;
    full_n: string;
  }>(`
    SELECT ds.id, ds.source_name, ds.province_code,
           (SELECT count(*) FROM positions p WHERE p.source_id = ds.id) AS n,
           (SELECT count(*) FROM positions_full f WHERE f.source_id = ds.id) AS full_n
    FROM data_sources ds
    ORDER BY full_n DESC
  `);

  const [notices] = await query<{ total: string }>(`SELECT count(*) AS total FROM notices`);
  const [noSource] = await query<{ legacy_n: string; full_n: string }>(`
    SELECT (SELECT count(*) FROM positions WHERE source_id IS NULL) AS legacy_n,
           (SELECT count(*) FROM positions_full WHERE source_id IS NULL) AS full_n
  `);

  // 公告：每条公告挂了多少岗位，前端可直接点开公告页
  const announcements = await query<{
    id: number;
    province_code: string | null;
    province_name: string | null;
    year: number | null;
    title: string | null;
    url: string | null;
    exam_type: string | null;
    n: string;
  }>(`
    SELECT a.id, a.province_code,
           COALESCE(pr.name, a.province_code) AS province_name,
           a.year, a.title, a.url, a.exam_type,
           (SELECT count(*) FROM positions_full f WHERE f.announcement_id = a.id) AS n
    FROM announcements a
    LEFT JOIN provinces pr ON pr.code = a.province_code
    ORDER BY a.year DESC NULLS LAST, a.id
  `);

  const [noticeStats] = await query<{ announcement: string; attachment: string }>(`
    SELECT count(*) FILTER (WHERE kind = 'announcement') AS announcement,
           count(*) FILTER (WHERE kind = 'attachment') AS attachment
    FROM notices
  `);

  return NextResponse.json({
    full: {
      total: Number(full?.total ?? 0),
      active: Number(full?.active ?? 0),
      disability_only: Number(full?.disability_only ?? 0),
      remote_area: Number(full?.remote_area ?? 0),
      linked: Number(full?.linked ?? 0),
      latest: full?.latest ?? null,
      groups: fullGroups.map((g) => ({
        year: g.year,
        province_code: g.province_code,
        province_name: g.province_name,
        total: Number(g.n),
        disability_only: Number(g.dis),
      })),
      years: fullYears.map((y) => ({ year: y.year, total: Number(y.n) })),
    },
    legacy: {
      total: Number(legacy?.total ?? 0),
      active: Number(legacy?.active ?? 0),
      disability_only: Number(legacy?.disability_only ?? 0),
      linked: Number(legacy?.linked ?? 0),
      latest: legacy?.latest ?? null,
      byProvince: legacyByProvince.map((p) => ({
        province_code: p.province_code,
        province_name: p.province_name,
        total: Number(p.n),
        disability_only: Number(p.dis),
      })),
    },
    sources: {
      items: sources.map((s) => ({
        id: s.id,
        source_name: s.source_name ?? `来源 #${s.id}`,
        province_code: s.province_code,
        count: Number(s.n),
        full_count: Number(s.full_n),
      })),
      unassigned_legacy: Number(noSource?.legacy_n ?? 0),
      unassigned_full: Number(noSource?.full_n ?? 0),
    },
    announcements: announcements.map((a) => ({
      id: a.id,
      province_code: a.province_code,
      province_name: a.province_name,
      year: a.year,
      title: a.title,
      url: a.url,
      exam_type: a.exam_type,
      count: Number(a.n),
    })),
    notices: {
      total: Number(notices?.total ?? 0),
      announcement: Number(noticeStats?.announcement ?? 0),
      attachment: Number(noticeStats?.attachment ?? 0),
    },
  });
}
