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
import hashlib
import json
import os
import pathlib
import re
import socket
import sys
import tempfile

import requests
import yaml

# ---------------------------------------------------------------------------
# 强制 IPv4：部分境内考试网站返回 AAAA 记录，而 GitHub Actions 服务器无 IPv6，
# 默认先试 IPv6 会报 "Network is unreachable"。过滤掉 AAAA，让请求直接走 IPv4。
# ---------------------------------------------------------------------------
_orig_getaddrinfo = socket.getaddrinfo

def _ipv4_first_getaddrinfo(*args, **kwargs):
    try:
        results = _orig_getaddrinfo(*args, **kwargs)
    except socket.gaierror:
        raise
    ipv4 = [ai for ai in results if ai[0] == socket.AF_INET]
    return ipv4 if ipv4 else results

socket.getaddrinfo = _ipv4_first_getaddrinfo

ROOT = pathlib.Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.yaml"

TIMEOUT = 30
UA = {"User-Agent": "Mozilla/5.0 (compatible; civil-exam-aid-scraper/0.1; +https://github.com/LETfreedom0/civil_exam_aid)"}

SB_URL = os.environ.get("SB_URL", "").rstrip("/")
SB_SERVICE_KEY = os.environ.get("SB_SERVICE_KEY", "")
TABLE = os.environ.get("SB_TABLE", "positions_full")
NOTICES_TABLE = "notices"
RUN_LOG_TABLE = "run_log"

ATTACH_SUFFIX = (".xlsx", ".xls", ".zip")
# sources.yaml 的 category → announcements.exam_type
EXAM_TYPES = {0: "省考", 1: "事业单位", 2: "国考", 3: "其他"}
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


def sb_post(table, rows, params=None, prefer=None):
    headers = sb_headers()
    if prefer:
        headers["Prefer"] = prefer
    r = requests.post(f"{SB_URL}/rest/v1/{table}", params=params or {},
                      json=rows, headers=headers, timeout=TIMEOUT)
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

def extract_page_title(html):
    """从页面 <title> 提取公告标题，去掉「 - 站点名」后缀。"""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    title = re.sub(r"<[^>]+>", "", m.group(1))
    title = re.sub(r"\s+", " ", title).strip()
    # 站点常写成「公告标题 - 广西人事考试网」，取主标题
    return re.split(r"\s*[-_|—]\s*", title)[0].strip() or title


def fetch_announcement_links(source):
    """下载公告页，抽取附件链接，同时返回公告页自身的 url 与标题。

    返回 (links, page)，page = {"url": 真实公告页地址, "title": 公告标题}。
    公告页 URL 会写进每条岗位的 source_url，供小程序一键直达公告；
    页面上抽到的 xlsx/xls 附件用于解析岗位数据。
    """
    import urllib.parse
    base = source["list_url"]
    text = ""
    has_explicit = bool(source.get("attachment_urls"))
    try:
        resp = requests.get(base, headers=UA, timeout=TIMEOUT)
        resp.raise_for_status()
        # requests 在响应头未标明编码时默认按 ISO-8859-1 解，中文页面会乱码
        if not resp.encoding or resp.encoding.lower() in ("iso-8859-1", "latin-1"):
            resp.encoding = resp.apparent_encoding or "utf-8"
        text = resp.text
        base = resp.url  # 跟随重定向后的真实地址
    except Exception as e:
        # 上海 2027：shacs.gov.cn 是 Vue 单页应用，详情页地址直接请求返回 404，
        # 正文与附件都走 JSON 接口。附件已用 attachment_urls 显式给出时，
        # 列表页抓不到不应中断采集——公告页地址仍保留用于 source_url 跳转。
        if not has_explicit:
            raise
        print(f"[{source['id']}] 列表页不可直连（{type(e).__name__}），"
              f"改用配置中的附件地址")

    links = []
    seen = set()  # 同一附件在页面里可能出现两次（正文 + 附件区），去重避免重复解析

    # 显式指定附件：页面把附件包成 /api-gateway/.../download?fileUrl=... 这类
    # 无扩展名链接时（浙江 2027），直接在这里写死最稳。
    explicit = source.get("attachment_urls") or []
    if explicit:
        for i, item in enumerate(explicit):
            url = item if isinstance(item, str) else item.get("url")
            title = (None if isinstance(item, str) else item.get("title")) \
                or f"{source.get('name', source['id'])}-附件{i + 1}"
            if url and url not in seen:
                seen.add(url)
                links.append({"url": url, "title": title})
    # 自定义附件链接正则：href 不以 xlsx/xls 结尾时用（如 /document/download?fileUrl=）
    patterns = [re.compile(p, re.IGNORECASE)
                for p in (source.get("attachment_patterns") or [])]

    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                         text, re.IGNORECASE | re.DOTALL):
        href, label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not (href.lower().endswith(ATTACH_SUFFIX)
                or any(p.search(href) for p in patterns)):
            continue
        url = urllib.parse.urljoin(base, href)
        if url in seen:
            continue
        seen.add(url)
        links.append({"url": url, "title": label or pathlib.Path(url).name})

    page = {
        "url": base,
        "title": source.get("announcement_title") or extract_page_title(text) or source["name"],
    }
    return links, page


def parse_attachment(url, header_row=0, member_pattern=None):
    """下载附件并解析为原始行。

    支持多 sheet 工作簿（如广西职位表：区直 + 14 个设区市各一个 sheet），
    每个 sheet 的名字会附加到每行的 _sheet 字段，供 map_row 写入 city。
    header_row：表头所在行（0-based）。有些省份上面压着标题行（北京是第 2 行），
    由 sources.yaml 的 header_row 指定。
    v0 仅支持 Excel；PDF 解析接入 pdfplumber 后放开。
    """
    import pandas as pd

    # 不依赖 URL 后缀判断格式：不少省份的附件走 /api-gateway/...download?fileUrl=
    # 这类包装链接，路径里没有扩展名（浙江 2027 即是）。按文件头魔数识别更可靠。
    resp = requests.get(url, headers=UA, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.content
    head = data[:4]

    blobs = []  # [(后缀, 二进制)]，一个附件可能解出多个表格
    if head == b"PK\x03\x04":
        import io
        import zipfile

        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
            names = zf.namelist()
        except zipfile.BadZipFile as e:
            raise ValueError(f"附件不是有效的 zip/xlsx: {e}") from e
        if any(n.startswith("xl/") for n in names):
            blobs.append((".xlsx", data))
        else:
            # 是真的 zip 包（广东 2027：公告附件.zip 内含 5 个文件）
            for n in names:
                low = n.lower()
                if low.startswith("__macosx") or not low.endswith((".xls", ".xlsx")):
                    continue
                # 只取职位表，跳过专业目录/咨询电话等附件（由 zip_member_pattern 指定）
                if member_pattern and member_pattern not in n:
                    continue
                blobs.append((pathlib.Path(low).suffix, zf.read(n)))
        if not blobs:
            raise ValueError("zip 包内没有 xls/xlsx 文件")
    elif head == b"\xd0\xcf\x11\xe0":
        blobs.append((".xls", data))
    elif head == b"%PDF":
        raise ValueError("附件是 PDF，暂不支持解析（需接入 pdfplumber）")
    else:
        raise ValueError(f"未知附件格式，文件头={head!r}")

    rows = []
    for suffix, blob in blobs:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(blob)
            path = tmp.name
        try:
            # header=None 读原始网格，再逐 sheet 自动定位表头：
            # 同一份工作簿里不同 sheet 的表头行可能不一样（广东 2027：
            # 「县以上机关」标题占两行、其余 sheet 只占一行），写死 header_row 会错位。
            sheets = pd.read_excel(path, sheet_name=None, header=None)
            for sheet_name, df in sheets.items():
                hr = _detect_header_row(df, header_row)
                if hr is None:
                    continue
                header = [str(v).strip() for v in df.iloc[hr].tolist()]
                body = df.iloc[hr + 1:].copy()
                body.columns = header
                for raw in body.to_dict(orient="records"):
                    raw["_sheet"] = str(sheet_name).strip()
                    rows.append(raw)
        finally:
            os.unlink(path)
    return rows


# 表头识别关键词：命中任意一个即认为该行是表头
HEADER_HINTS = ("职位代码", "职位编码", "招考单位", "单位名称", "招录机关",
                "职位名称", "招考职位", "招录名额")


def _detect_header_row(df, fallback=0):
    """在前若干行里找表头行（0-based）；找不到返回 fallback。

    判据：该行至少有 2 个单元格命中表头关键词，且非空单元格不少于 4 个。
    这样能跳过「附件1」「广东省…职位表」这类合并单元格标题行。
    """
    limit = min(8, len(df))
    for i in range(limit):
        # 必须先去换行再比对：四川广元/自贡把表头排成「职位\n名称」，
        # 原样匹配「职位名称」一个都命中不了，会退化成第 0 行「附件1」。
        values = [_norm_key(v) for v in df.iloc[i].tolist()]
        non_empty = sum(1 for v in values if v and v != "nan")
        hits = sum(1 for v in values if any(h in v for h in HEADER_HINTS))
        if hits >= 2 and non_empty >= 4:
            return i
    return fallback if fallback < len(df) else None


def _norm_key(value):
    """去掉表头里的换行与空格：「职位\\n代码」→「职位代码」。

    各省表头常带 \r\n 排版换行（北京全表如此），不规范化会匹配不上字段映射。
    """
    return re.sub(r"\s+", "", str(value))


def map_row(raw, source):
    """Excel 中文表头 → positions 字段。

    field_mapping 在 sources.yaml 中按数据源配置。
    类型处理：quota 转整数；其余转字符串并去空白；空值跳过。
    """
    mapping = {_norm_key(k): v for k, v in (source.get("field_mapping") or {}).items()}
    # 表头键名统一规范化后再取值
    data = {_norm_key(k): v for k, v in raw.items() if not str(k).startswith("_")}
    row = {}
    for excel_col, field in mapping.items():
        value = data.get(excel_col)
        if value is None or (isinstance(value, float) and value != value):  # NaN
            continue
        text = str(value).strip()
        if text == "" or text.lower() == "nan":
            continue
        # 电话列常在一个单元格里塞两个号码（换行分隔），压成一行便于前端展示
        if field in ("phone1", "phone2"):
            text = re.sub(r"[\r\n]+", " / ", text)
        else:
            # 单元格内排版折行：北京整表、四川自贡/广元等把「执法\n勤务（一）」折成两行。
            # 中文行内换行纯属排版，去掉（含两侧空白），否则会原样入库。
            text = re.sub(r"[ \t]*[\r\n]+[ \t]*", "", text)
        if field == "quota":
            try:
                row[field] = int(float(text))
                continue
            except ValueError:
                pass  # 非纯数字时按原文保留
        # 同一目标字段被多列映射时用「；」拼接（广东 2027 的专业要求分研究生/本科/大专三列）
        if field in row and isinstance(row[field], str) and row[field]:
            row[field] = f"{row[field]}；{text}"
            continue
        row[field] = text
    row["province_code"] = source["province_code"]
    row["year"] = int(source.get("year", TODAY.year))
    row["position_origin"] = int(source.get("category", 0))
    # 考试类型（省考/事业单位/国考）由 sources.yaml 的 category 决定，各省表格里没有这一列
    row["exam_type"] = EXAM_TYPES.get(row["position_origin"], "其他")
    # 注意：positions.source_id 是 bigint（指向 data_sources.id），
    # 不能放字符串源 id；源信息由 notices / run_log 记录。
    sheet = raw.get("_sheet")
    if sheet and sheet != "nan":
        # sheet_as_city：广西按「区直/南宁/柳州」分 sheet，正好是城市；
        # 北京按「普通职位/面向残疾人职位」分 sheet，不是城市，要关掉。
        if source.get("sheet_as_city", True):
            row["city"] = sheet
        # sheet_identity_map：显式指定「sheet 名 → 报考身份」（上海 2027 的
        # 「残疾人」「服务基层项目」「高校毕业生退役士兵」三张表，招考对象列写的是
        # 「不限」，群体口径只体现在 sheet 名上）。优先级高于表内「招考对象」列。
        identity_map = source.get("sheet_identity_map") or {}
        if identity_map.get(sheet):
            row["candidate_identity"] = identity_map[sheet]
        # sheet_identity：北京没有「招考对象」列，群体口径写在 sheet 名上
        elif source.get("sheet_identity") and not row.get("candidate_identity"):
            row["candidate_identity"] = sheet if sheet.startswith("面向") else "不限"
    # 幂等键：默认 省份|年份|职位代码|单位|职位名 的哈希
    # （线上实测职位代码省内可能重号）。个别省份职位代码过短（江苏是 2 位，
    # 各市独立编号），需在 sources.yaml 用 key_fields 把 city 纳入键。
    key_fields = source.get("key_fields") or [
        "province_code", "year", "position_code", "recruit_unit", "position_name",
    ]
    key_src = "|".join(str(row.get(f) or "") for f in key_fields)
    row["external_key"] = hashlib.md5(key_src.encode("utf-8")).hexdigest()
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


def record_notice(url, title, source_id, kind="attachment"):
    """记录采集流水。kind=announcement 表示考试公告页，attachment 表示岗位表附件。"""
    sb_post(NOTICES_TABLE, [{
        "url": url,
        "title": title,
        "source_id": source_id,
        "kind": kind,
        "seen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }])


def upsert_positions(rows, table=None):
    """按 external_key 幂等写入（PostgREST upsert 需要 Prefer 头）。

    table 省略时写 SB_TABLE（全量库 positions_full）；
    存量库（残疾人专岗）由导入端显式传 table="positions"。

    PostgREST 要求同一批 POST 的所有对象键完全一致（PGRST102），
    所以先取所有行的键并集，缺列补 null 再发送。
    """
    if not rows:
        return
    keys, seen = [], set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    normalized = [{k: r.get(k) for k in keys} for r in rows]
    params = {"on_conflict": "external_key"}
    sb_post(table or TABLE, normalized, params, prefer="resolution=merge-duplicates")


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

def collect_source_rows(src):
    """抓取并解析一个数据源。返回 (links, rows_by_url, announcement)。

    rows_by_url[url] 是该附件解析出的岗位行列表；解析失败的附件不进字典。
    links（附件）与 announcement（公告页）供导入端写 notices 去重。
    每行的 source_url 会填成公告页地址，前端可一键直达。
    境内考试网站屏蔽境外 IP（gxpta 实测），抓取必须在境内网络执行——
    GitHub Actions 只负责导入，见 --export 与 scripts/import_data.py。
    """
    links, announcement = fetch_announcement_links(src)
    print(f"[{src['id']}] 发现 {len(links)} 个附件，公告页 {announcement['url']}")
    rows_by_url = {}
    header_row = int(src.get("header_row", 0))
    for link in links:
        try:
            rows = []
            for raw in parse_attachment(link["url"], header_row=header_row,
                                        member_pattern=src.get("zip_member_pattern")):
                row = map_row(raw, src)
                code = str(row.get("position_code") or "")
                # 表尾常有「说明：除特别注明外，职位表中的专业均为…」整段注释，
                # 会被当成一条岗位（四川法院/监狱各 1 条）。编码不会是长句，据此剔除。
                if code and (len(code) > 24 or code.startswith(("说明", "注："))):
                    continue
                if row.get("position_name") or code:
                    # 公告页链接随行走：小程序查一条岗位即可直达公告
                    row["source_url"] = announcement["url"]
                    rows.append(row)
            rows_by_url[link["url"]] = rows
        except Exception as e:  # 单个附件失败不中断整省
            print(f"[{src['id']}] 附件处理失败 {link['url']}: {e}")
    return links, rows_by_url, announcement


def export_sources(enabled, out_path):
    """只抓取并导出 JSON（不连 Supabase）。导入由 GitHub Actions 完成。"""
    sources_payload = []
    for src in enabled:
        if src["kind"] == "manual":
            continue
        links, rows_by_url, announcement = collect_source_rows(src)
        rows = [r for rows in rows_by_url.values() for r in rows]
        # 同键去重：部分省份会把同一职位按「多个区各招若干人」拆成多行，
        # 各字段完全一致（江苏 2027 有 200+ 组），入库会撞唯一索引，这里保留最后一条。
        deduped = {r["external_key"]: r for r in rows}
        if len(deduped) != len(rows):
            print(f"[{src['id']}] 同键合并 {len(rows) - len(deduped)} 行 → {len(deduped)} 条")
        sources_payload.append({
            "id": src["id"],
            # name 必须带出去：导入端写 data_sources.source_name 时优先用它，
            # 缺失会回落成 id（如 bj-rsks-2027），后台来源列就会显示成英文代号。
            "name": src.get("name"),
            "province_code": src["province_code"],
            "year": int(src.get("year", TODAY.year)),
            "exam_type": EXAM_TYPES.get(int(src.get("category", 0)), "其他"),
            "list_url": src.get("list_url"),
            "announcement": announcement,
            "attachments": [{"url": l["url"], "title": l["title"]} for l in links],
            "rows": list(deduped.values()),
        })
    payload = {
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": sources_payload,
    }
    pathlib.Path(out_path).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    total = sum(len(s["rows"]) for s in sources_payload)
    print(f"\n[export] 已导出 {total} 条到 {out_path}，接下来执行 scripts/push_data.py 推送导入。")
    return 0


def main():
    parser = argparse.ArgumentParser(description="残疾人公考岗位采集")
    parser.add_argument("--dry-run", action="store_true",
                        help="只校验配置与数据源连通性，不写 Supabase")
    parser.add_argument("--export", metavar="PATH",
                        help="只抓取并导出 JSON（不连 Supabase），境内网络抓取用")
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

    # 导出模式：境内抓取端使用，不需要 Supabase 凭据
    if args.export:
        return export_sources(enabled, args.export)

    if not SB_URL or not SB_SERVICE_KEY:
        print("缺少环境变量 SB_URL / SB_SERVICE_KEY（在仓库 Settings → Secrets 配置）。")
        return 1

    total = 0
    for src in enabled:
        if src["kind"] == "manual":
            print(f"[{src['id']}] manual 数据源，跳过自动抓取。")
            continue
        try:
            links, rows_by_url, announcement = collect_source_rows(src)
            new_rows = []
            for link in links:
                if is_notice_seen(link["url"]):
                    continue
                new_rows.extend(rows_by_url.get(link["url"], []))
                record_notice(link["url"], link["title"], src["id"], kind="attachment")
            if new_rows:
                upsert_positions(new_rows)
            if not is_notice_seen(announcement["url"]):
                record_notice(announcement["url"], announcement["title"], src["id"], kind="announcement")
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
