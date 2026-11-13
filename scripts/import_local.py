#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地导入：psycopg2 直连 Postgres，把 data/*.json 写入 Supabase。

为什么需要这个脚本
    本机访问 supabase.co 的 REST(443) 被阻断，只有 pooler 5432 通道可用；
    而 scripts/import_data.py 走 PostgREST，只能跑在 GitHub Actions（境外）。
    本脚本是它的等价实现：同一套打标与分流规则，直连数据库执行。

落库规则（与 import_data.py 一致）
    1. 全部岗位     → positions_full（全量库）
    2. 残疾人专岗   → 同时写一份到 positions（残疾人专岗库）
    3. 公告与来源   → announcements / data_sources 幂等登记，回填 announcement_id + source_url
    4. 采集流水     → notices（公告页 / 附件）+ run_log

用法
    python scripts/import_local.py                  # 导入 data/*.json 全部
    python scripts/import_local.py data/bj.json     # 只导入指定文件
    DATABASE_URL=postgresql://... python scripts/import_local.py
"""

import glob
import json
import os
import pathlib
import sys

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from import_data import FULL_ONLY_COLS, enrich_row  # 复用同一套打标规则

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHUNK = 500


def load_dsn():
    """优先环境变量，其次 admin/.env.local（已被 gitignore）。"""
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn.strip()
    env_file = ROOT / "admin" / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "缺少数据库连接串：请设置环境变量 DATABASE_URL，或在 admin/.env.local 中配置。"
    )


def table_columns(cur, table):
    cur.execute(
        """SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position""",
        (table,),
    )
    return {r[0] for r in cur.fetchall()}


def _normalize(value):
    """空数组保持为 []：audience_tags 是 NOT NULL DEFAULT '{}'，
    而 psycopg2 会按目标列类型把 [] 适配成 '{}'，转成 NULL 反而会违反约束。
    """
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return []
    return value


def upsert_rows(cur, table, rows, allowed):
    """按 external_key 幂等写入；列取本批出现的并集（缺失列写 NULL）。"""
    if not rows:
        return 0
    cols = []
    for row in rows:
        for key in row:
            if key in allowed and key != "id" and key not in cols:
                cols.append(key)
    if not cols:
        return 0
    tuples = [tuple(_normalize(row.get(c)) for c in cols) for row in rows]
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "external_key")
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s "
        f"ON CONFLICT (external_key) DO UPDATE SET {updates}"
    )
    for i in range(0, len(tuples), CHUNK):
        execute_values(cur, sql, tuples[i:i + CHUNK], page_size=200)
    return len(rows)


def _source_display_name(src):
    """来源显示名：优先 sources.yaml 的 name，其次公告标题，最后才回落到源 id。

    早期直接回落到 id，会把 'bj-rsks-2027' 这类代号写进 data_sources.source_name，
    后台来源列就显示成英文代号了，故按语义逐级兜底。
    """
    name = (src.get("name") or "").strip()
    if name:
        return name
    title = ((src.get("announcement") or {}).get("title") or "").strip()
    if title:
        return title
    return src.get("id")


def ensure_source(cur, src):
    """登记数据源，返回 data_sources.id（按 source_url 去重）。"""
    url = src.get("list_url") or None
    if url:
        cur.execute(
            "SELECT id FROM data_sources WHERE source_url = %s ORDER BY id DESC LIMIT 1",
            (url,),
        )
        found = cur.fetchone()
        if found:
            return found[0]
    attachments = src.get("attachments") or []
    cur.execute(
        """INSERT INTO data_sources
             (province_code, source_name, source_url, announcement_title,
              attachment_filename, crawled_at, data_hash)
           VALUES (%s, %s, %s, %s, %s, now(), %s)
           RETURNING id""",
        (
            src.get("province_code"),
            _source_display_name(src),
            url,
            (src.get("announcement") or {}).get("title") or src.get("name"),
            attachments[0].get("title") if attachments else None,
            f"sha256:{src.get('id')}",
        ),
    )
    return cur.fetchone()[0]


def ensure_announcement(cur, src):
    """登记考试公告，返回 announcements.id（按 url 幂等）。"""
    ann = src.get("announcement") or {}
    url = ann.get("url") or src.get("list_url")
    if not url:
        return None
    cur.execute(
        """INSERT INTO announcements (province_code, year, title, url, exam_type)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (url) DO UPDATE
              SET title = EXCLUDED.title,
                  exam_type = EXCLUDED.exam_type,
                  year = EXCLUDED.year
           RETURNING id""",
        (
            src.get("province_code"),
            int(src.get("year") or 0) or None,
            ann.get("title") or src.get("name") or "考试公告",
            url,
            src.get("exam_type") or "其他",
        ),
    )
    return cur.fetchone()[0]


def record_notices(cur, src, ann_url, ann_title):
    for att in src.get("attachments") or []:
        if not att.get("url"):
            continue
        cur.execute(
            """INSERT INTO notices (url, title, source_id, kind)
               VALUES (%s, %s, %s, 'attachment')
               ON CONFLICT (url) DO NOTHING""",
            (att["url"], att.get("title"), src.get("id")),
        )
    if ann_url:
        cur.execute(
            """INSERT INTO notices (url, title, source_id, kind)
               VALUES (%s, %s, %s, 'announcement')
               ON CONFLICT (url) DO UPDATE
                  SET kind = 'announcement',
                      title = COALESCE(notices.title, EXCLUDED.title)""",
            (ann_url, ann_title, src.get("id")),
        )


def import_file(cur, path, full_cols, legacy_cols):
    payload = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for src in payload.get("sources", []):
        rows = [enrich_row(dict(r)) for r in src.get("rows", [])]
        if not rows:
            continue

        ds_id = ensure_source(cur, src)
        ann_id = ensure_announcement(cur, src)
        ann = src.get("announcement") or {}
        ann_url = ann.get("url") or src.get("list_url")
        ann_title = ann.get("title") or src.get("name")

        for row in rows:
            if ds_id:
                row["source_id"] = ds_id
            if ann_id:
                row["announcement_id"] = ann_id
            if ann_url and not row.get("source_url"):
                row["source_url"] = ann_url

        n_full = upsert_rows(cur, "positions_full", rows, full_cols)

        picked = [
            {k: v for k, v in r.items() if k not in FULL_ONLY_COLS}
            for r in rows
            if r.get("is_disability_only")
        ]
        n_dis = upsert_rows(cur, "positions", picked, legacy_cols)

        record_notices(cur, src, ann_url, ann_title)
        cur.execute(
            """INSERT INTO run_log (source_id, change_type, summary, affected_positions)
               VALUES (%s, 'import', %s, %s)""",
            (
                src.get("id"),
                f"导入 {n_full} 条（残疾专岗 {n_dis} 条，本地直连）",
                n_full,
            ),
        )
        print(f"[{src.get('id')}] 全量库 {n_full} 条，专岗库 {n_dis} 条")


def main():
    paths = sys.argv[1:] or sorted(glob.glob(str(ROOT / "data" / "*.json")))
    if not paths:
        print("data/ 目录下没有待导入的 JSON 文件。")
        return 0

    conn = psycopg2.connect(load_dsn(), connect_timeout=20)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            full_cols = table_columns(cur, "positions_full")
            legacy_cols = table_columns(cur, "positions")
            for path in paths:
                print(f"→ {path}")
                import_file(cur, path, full_cols, legacy_cols)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print("\n导入完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
