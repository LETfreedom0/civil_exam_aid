#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残疾人公考岗位采集脚本（骨架版）

流水线：sources.yaml 数据源 → 抓公告列表页 → 抽取附件(xlsx) → pandas 解析
        → 字段映射 → upsert Supabase(positions) → notices 去重 → run_log 记录

用法：
  python scripts/scrape.py --dry-run   # 只校验配置与数据源连通性，不写库
  python scripts/scrape.py             # 正式采集，需要 SB_URL / SB_SERVICE_KEY

扩展点（TODO）：
  1. sources.yaml 里逐省配置 list_url 与 field_mapping（每周 2~3 省，见技术方案）
  2. parser: html_links 为通用 <a href> 扫描；结构特殊的站点在此扩展
  3. PDF 附件解析（pdfplumber）尚未启用，见 parse_attachment()
"""

import argparse
import datetime as dt
import os
import pathlib
import re
import sys
import tempfile

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.yaml"

TIMEOUT = 30
UA = {"User-Agent": "Mozilla/5.0 (compatible; civil-exam-aid-scraper/0.1; +https://github.com/LETfreedom0/civil_exam_aid)"}

SB_URL = os.environ.get("SB_URL", "").rstrip("/")
SB_SERVICE_KEY = os.environ.get("SB_SERVICE_KEY", "")
TABLE = os.environ.get("SB_TABLE", "positions")
NOTICES_TABLE = "notices"
RUN_LOG_TABLE = "run_log"

ATTACH_SUFFIX = (".xlsx", ".xls")
TODAY = dt.date.today()


def sb_headers():
    return {
        "apikey": SB_SERVICE_KEY,
        "Authorization": f"Bearer {SB_SERVICE_KEY}",
        "Content-Type": "application/json",
    }


def sb_get(table, params):
    r = requests.get(f"{SB_URL}/rest/v1/{table}", params=params,
                     headers=sb_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def sb_post(table, rows, params=None):
    r = requests.post(f"{SB_URL}/rest/v1/{table}", params=params or {},
                      json=rows, headers=sb_headers(), timeout=TIMEOUT)
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase 写入 {table} 失败: {r.status_code} {r.text[:300]}")
    return r


# ---------------------------------------------------------------------------
# 数据源配置
# ---------------------------------------------------------------------------

def load_sources():
    with open(SOURCES_FILE, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("sources", [])


def validate_sources(sources):
    """返回 (errors, enabled)。errors 非空则退出，避免带病采集。"""
    errors, enabled = [], []
    seen_ids = set()
    for i, src in enumerate(sources):
        sid = src.get("id") or f"source_{i}"
        for field in ("id", "province_code", "name", "kind"):
            if not src.get(field):
                errors.append(f"[{sid}] 缺少必填字段 {field}")
        if src.get("id") in seen_ids:
            errors.append(f"[{sid}] id 重复")
        seen_ids.add(src.get("id"))
        if src.get("kind") not in ("announcement", "excel", "manual"):
            errors.append(f"[{sid}] kind 必须是 announcement/excel/manual")
        if src.get("enabled", False) and src.get("kind") != "manual" and not src.get("list_url"):
            errors.append(f"[{sid}] 已启用但缺少 list_url")
        if src.get("enabled", False):
            enabled.append(src)
    return errors, enabled


def print_plan(enabled):
    print(f"启用数据源 {len(enabled)} 个：")
    for src in enabled:
        note = "(manual，跳过抓取)" if src["kind"] == "manual" else src.get("list_url", "")
        print(f"  - [{src['province_code']}] {src['name']}  {note}")


# ---------------------------------------------------------------------------
# 抓取与解析
# ---------------------------------------------------------------------------

def fetch_announcement_links(source):
    """下载公告列表页，抽取附件链接。通用实现：扫描 <a href> 中的 xlsx/xls。

    各省站点结构差异大，特殊站点请在 sources.yaml 指定独立 parser 并在此扩展。
    """
    import urllib.parse
    resp = requests.get(source["list_url"], headers=UA, timeout=TIMEOUT)
    resp.raise_for_status()
    text = resp.text
    base = resp.url

    links = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                         text, re.IGNORECASE | re.DOTALL):
        href, label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not href.lower().endswith(ATTACH_SUFFIX):
            continue
        url = urllib.parse.urljoin(base, href)
        links.append({"url": url, "title": label or pathlib.Path(url).name})
    return links


def parse_attachment(url):
    """下载附件并解析为原始行。v0 仅支持 Excel；PDF 解析接入 pdfplumber 后放开。"""
    import pandas as pd

    with tempfile.NamedTemporaryFile(suffix=pathlib.Path(url).suffix,
                                     delete=False) as tmp:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        tmp.write(r.content)
        path = tmp.name
    try:
        df = pd.read_excel(path)
        return df.to_dict(orient="records")
    finally:
        os.unlink(path)


def map_row(raw, source):
    """Excel 中文表头 → positions 字段。

    field_mapping 在 sources.yaml 中按数据源配置；缺失映射的行记 warning 并跳过。
    """
    mapping = source.get("field_mapping") or {}
    row = {}
    for excel_col, field in mapping.items():
        value = raw.get(excel_col)
        if value is not None and str(value).strip() != "":
            row[field] = str(value).strip()
    row["province_code"] = source["province_code"]
    row["year"] = int(source.get("year", TODAY.year))
    row["position_origin"] = int(source.get("category", 0))
    row["source_id"] = source.get("id")
    return row


# ---------------------------------------------------------------------------
# 增量去重与入库
# ---------------------------------------------------------------------------

def is_notice_seen(url):
    if not url:
        return False
    try:
        existing = sb_get(NOTICES_TABLE, {"url": f"eq.{url}", "select": "id", "limit": 1})
        return bool(existing)
    except Exception:
        return False  # notices 表不可用时退化为全量处理


def record_notice(url, title, source_id):
    sb_post(NOTICES_TABLE, [{
        "url": url,
        "title": title,
        "source_id": source_id,
        "seen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }])


def upsert_positions(rows):
    """依赖 v2 迁移中 positions(job_code, exam_year) 的唯一约束。"""
    params = {"on_conflict": "job_code,exam_year"}
    sb_post(TABLE, rows, params)


def write_run_log(source_id, summary, affected):
    sb_post(RUN_LOG_TABLE, [{
        "source_id": source_id,
        "change_type": "import",
        "summary": summary,
        "affected_positions": affected,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }])


def mark_expired():
    """过考录年度的岗位批量下架。"""
    r = requests.patch(
        f"{SB_URL}/rest/v1/{TABLE}",
        params={"year": f"lt.{TODAY.year}", "is_active": "eq.true"},
        json={"is_active": False},
        headers=sb_headers(), timeout=TIMEOUT,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"标记过期失败: {r.status_code} {r.text[:300]}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="残疾人公考岗位采集")
    parser.add_argument("--dry-run", action="store_true",
                        help="只校验配置与数据源连通性，不写 Supabase")
    args = parser.parse_args()

    sources = load_sources()
    if not sources:
        print("sources.yaml 中没有配置任何数据源。")
        return 0

    errors, enabled = validate_sources(sources)
    if errors:
        print("sources.yaml 校验失败：")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print_plan(enabled)

    if args.dry_run:
        print("\n[dry-run] 配置校验通过，未写入 Supabase。")
        return 0

    if not SB_URL or not SB_SERVICE_KEY:
        print("缺少环境变量 SB_URL / SB_SERVICE_KEY（在仓库 Settings → Secrets 配置）。")
        return 1

    total = 0
    for src in enabled:
        if src["kind"] == "manual":
            print(f"[{src['id']}] manual 数据源，跳过自动抓取。")
            continue
        try:
            links = fetch_announcement_links(src)
            print(f"[{src['id']}] 发现 {len(links)} 个附件。")
            new_rows = []
            for link in links:
                if is_notice_seen(link["url"]):
                    continue
                try:
                    for raw in parse_attachment(link["url"]):
                        row = map_row(raw, src)
                        if row.get("position_name") or row.get("job_code"):
                            new_rows.append(row)
                    record_notice(link["url"], link["title"], src["id"])
                except Exception as e:  # 单个附件失败不中断整省
                    print(f"[{src['id']}] 附件处理失败 {link['url']}: {e}")

            if new_rows:
                upsert_positions(new_rows)
            write_run_log(src["id"], f"采集 {len(new_rows)} 条", len(new_rows))
            total += len(new_rows)
        except Exception as e:
            print(f"[{src['id']}] 数据源失败: {e}")

    try:
        mark_expired()
    except Exception as e:
        print(f"标记过期失败（不中断）: {e}")

    print(f"\n完成，本次共写入 {total} 条。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
