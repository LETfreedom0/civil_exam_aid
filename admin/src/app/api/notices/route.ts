import { NextRequest, NextResponse } from "next/server";
import { checkAuth } from "@/lib/auth";
import { query } from "@/lib/db";

export async function GET(req: NextRequest) {
  const denied = checkAuth(req);
  if (denied) return denied;

  const sp = req.nextUrl.searchParams;
  const q = sp.get("q")?.trim();
  const kind = sp.get("kind")?.trim();
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const pageSize = Math.min(100, Math.max(1, Number(sp.get("pageSize") ?? 20)));

  const params: unknown[] = [];
  const where: string[] = [];
  if (q) {
    params.push(`%${q}%`);
    where.push(`(title ILIKE $${params.length} OR url ILIKE $${params.length} OR source_id ILIKE $${params.length})`);
  }
  if (kind === "announcement" || kind === "attachment") {
    params.push(kind);
    where.push(`kind = $${params.length}`);
  }
  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";

  const [countRow] = await query<{ total: string }>(
    `SELECT count(*) AS total FROM notices ${whereSql}`,
    params
  );
  const items = await query(
    `SELECT id, url, title, source_id, kind, seen_at
       FROM notices ${whereSql}
      ORDER BY kind = 'announcement' DESC, seen_at DESC
      LIMIT ${pageSize} OFFSET ${(page - 1) * pageSize}`,
    params
  );
  const [stats] = await query<{ announcement: string; attachment: string }>(
    `SELECT count(*) FILTER (WHERE kind = 'announcement') AS announcement,
            count(*) FILTER (WHERE kind = 'attachment') AS attachment
       FROM notices`
  );

  return NextResponse.json({
    items,
    total: Number(countRow?.total ?? 0),
    page,
    pageSize,
    stats: {
      announcement: Number(stats?.announcement ?? 0),
      attachment: Number(stats?.attachment ?? 0),
    },
  });
}
