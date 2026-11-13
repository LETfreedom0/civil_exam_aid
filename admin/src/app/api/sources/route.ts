import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";

/** 数据来源字典 + 各表挂载岗位数 */
export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const sources = await query<{
    id: number;
    source_name: string | null;
    province_code: string | null;
    source_url: string | null;
    announcement_title: string | null;
    crawled_at: string | null;
    full_n: string;
    legacy_n: string;
  }>(`
    SELECT ds.id, ds.source_name, ds.province_code, ds.source_url,
           ds.announcement_title, ds.crawled_at,
           (SELECT count(*) FROM positions_full p WHERE p.source_id = ds.id) AS full_n,
           (SELECT count(*) FROM positions p WHERE p.source_id = ds.id) AS legacy_n
    FROM data_sources ds
    ORDER BY ds.id
  `);

  const orphans = await query<{ full_n: string; legacy_n: string }>(`
    SELECT (SELECT count(*) FROM positions_full WHERE source_id IS NULL) AS full_n,
           (SELECT count(*) FROM positions WHERE source_id IS NULL) AS legacy_n
  `);

  return NextResponse.json({
    items: sources.map((s) => ({
      id: s.id,
      source_name: s.source_name ?? `来源 #${s.id}`,
      province_code: s.province_code,
      source_url: s.source_url,
      announcement_title: s.announcement_title,
      crawled_at: s.crawled_at,
      full_count: Number(s.full_n),
      legacy_count: Number(s.legacy_n),
    })),
    unassigned: {
      full_count: Number(orphans[0]?.full_n ?? 0),
      legacy_count: Number(orphans[0]?.legacy_n ?? 0),
    },
  });
}
