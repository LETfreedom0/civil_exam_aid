#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入端：把 data/*.json 里导出的岗位数据写入 Supabase。

运行在 GitHub Actions（境外网络，可访问 supabase.co）。
数据文件由境内抓取端生成：python scripts/scrape.py --export data/xxx.json

数据落库规则：
  1. 全部岗位     → positions_full（全量库，主数据）
  2. 残疾人专岗   → 同时写一份到 positions（存量库 = 残疾人专岗库）
     识别依据：其他要求 / 报考对象 / 职位简介 中出现「残疾人证 / 限残疾人 / 残疾人」
"""

import datetime as dt
import glob
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scrape  # 复用 sb_get/sb_post/upsert_positions/record_notice/write_run_log/mark_expired

CHUNK = 500  # 每批 upsert 条数，避免单次 POST 过大
DATA_SOURCES_TABLE = "data_sources"
ANNOUNCEMENTS_TABLE = "announcements"   # 考试公告主表（岗位一键直达的落点）
FULL_TABLE = "positions_full"     # 全量库（主数据）
LEGACY_TABLE = "positions"        # 存量库 = 残疾人专岗库
# 仅全量库有的扁平残疾列，写存量库时要剔除（存量库用 position_disability 表）
FULL_ONLY_COLS = {"disability_types", "allowed_levels", "disability_source_text"}

# 与 supabase/migrations/20261109160000_audience_disability.sql 的回填口径一致。
# 注意：不能只匹配裸「残疾人」——「残疾人联合会」「从事残疾人服务工作」这类表述
# 会把普通职位误标成专岗（浙江 2027 实测有 5 条这种）。故分强弱两级：
#   强信号：明确限定残疾人报考的表述，直接判定
#   弱信号：仅出现「残疾」，必须与招录意图词同现才判定
DISABILITY_STRONG_RE = re.compile(
    r"残疾人证|限残疾人|残疾人专岗|残疾人专项|面向残疾人|残疾人报考|"
    r"残疾人定向|招录残疾人|残疾人考生|残疾人职位|残疾人岗位|残疾人可报"
)
DISABILITY_WEAK_RE = re.compile(r"残疾")
# 报考资格口径：出现这些词才算「限制报考」，避免把「从事残疾人服务工作」算成专岗。
# 注意不能放裸「限」——浙江残联岗位的「最低服务年限为5年」会误命中。
ELIGIBILITY_RE = re.compile(
    r"报考|招录|考录|招聘|定向|专项|面向|持有|持证|须持|需持|仅限|限残|残疾人证"
)


def is_disability_job(text):
    """判断一段条件文本是否描述「残疾人专岗」。"""
    if not text:
        return False
    if DISABILITY_STRONG_RE.search(text):
        return True
    # 「肢体或听力残疾四级」这种极简写法：残疾 + 等级 + 类型同现，就是专岗要求
    # （天津 2027 的定向岗只写这一句，没有任何「报考/招录」字样）
    if (DISABILITY_WEAK_RE.search(text) and LEVEL_RE.search(text)
            and re.search(r"肢体|视力|听力|言语|智力|精神", text)):
        return True
    # 弱信号必须紧邻资格口径才算数。整段「职位简介」里提一句「残疾人管理服务」
    # 是工作内容，不是报考限制（上海 2027 宝山社区岗实测误标）。
    for m in DISABILITY_WEAK_RE.finditer(text):
        window = text[max(0, m.start() - 25): m.end() + 25]
        if ELIGIBILITY_RE.search(window):
            return True
    return False


REMOTE_RE = re.compile(r"艰苦边远地区[:：]\s*是")
# 残疾等级：必须紧邻「级」且后面不是职级词，避免把「一级主任科员」误当成残疾一级
LEVEL_RE = re.compile(
    r"([一二三四])\s*级(?!\s*(?:主任科员|科员|调研员|巡视员|督办|主办|主管|"
    r"警长|法官|检察官|行政执法员|主任|调研员))"
)


def extract_levels(text):
    """只在「残疾」附近的语境里取等级，避免职级/学历等级串味。

    「三、四级」这类缩写先展开成「三级、四级」，否则只会识别到「四级」。
    """
    if not text:
        return []
    text = re.sub(r"([一二三四])\s*[、和,]\s*(?=[一二三四]\s*级)", r"\1级、", text)
    levels = set()
    for m in re.finditer(r"残疾", text):
        window = text[max(0, m.start() - 40): m.end() + 40]
        for k in LEVEL_RE.findall(window):
            levels.add(LEVEL_MAP[k])
    return sorted(levels)
TYPE_MAP = {
    "肢体": "physical",
    "听力": "hearing",
    "视力": "vision",
    "言语": "speech",
    "智力": "intellectual",
    "精神": "mental",
    "多重": "multiple",
}
LEVEL_MAP = {"一": 1, "二": 2, "三": 3, "四": 4}


def enrich_row(row):
    """补残疾/边远/群体标签，供全量库筛选；存量库同步依赖 is_disability_only。"""
    text = " ".join(
        str(row.get(k) or "")
        for k in ("other_requirements", "candidate_identity", "description")
    )
    tags = set(row.get("audience_tags") or [])

    if is_disability_job(text):
        row["is_disability_only"] = True
        tags.add("disabled")
        row["disability_source_text"] = text.strip()[:500]
        types = [v for k, v in TYPE_MAP.items() if k in text]
        row["disability_types"] = types or ["unspecified"]
        row["allowed_levels"] = extract_levels(text)
    else:
        row.setdefault("is_disability_only", False)

    if "应届" in str(row.get("candidate_identity") or "") or row.get("fresh_grad") == "是":
        tags.add("fresh_grad")
    if REMOTE_RE.search(str(row.get("other_requirements") or "")):
        row["remote_area"] = True

    row["audience_tags"] = sorted(tags)
    return row


def _source_display_name(src):
    """来源显示名：优先 sources.yaml 的 name，其次公告标题，最后才回落到源 id。"""
    name = (src.get("name") or "").strip()
    if name:
        return name
    title = ((src.get("announcement") or {}).get("title") or "").strip()
    if title:
        return title
    return src.get("id")


def ensure_data_source(src):
    """登记数据源并返回 data_sources.id。

    positions.source_id 是 bigint，指向 data_sources.id；
    采集端在境内运行、写不了库，所以来源在这里补。
    以 source_url（无则 source_name）作为去重依据。
    """
    url = src.get("list_url") or ""
    try:
        if url:
            rows = scrape.sb_get(DATA_SOURCES_TABLE, {
                "source_url": f"eq.{url}", "select": "id", "limit": 1,
            })
            if rows:
                return rows[0]["id"]
        payload = {
            "province_code": src.get("province_code"),
            "source_name": _source_display_name(src),
            "source_url": url or None,
            "announcement_title": (src.get("announcement") or {}).get("title") or src.get("name"),
            "attachment_filename": src.get("attachment_filename"),
            "crawled_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "data_hash": f"sha256:{src.get('id')}",
        }
        r = scrape.sb_post(DATA_SOURCES_TABLE, [payload], prefer="return=representation")
        created = r.json()
        return created[0]["id"] if created else None
    except Exception as e:
        print(f"[{src.get('id')}] 数据源登记失败（不中断）: {e}")
        return None


def sync_disability_rows(rows):
    """残疾人专岗同步进存量库（positions），供小程序独立筛选使用。"""
    picked = [
        {k: v for k, v in r.items() if k not in FULL_ONLY_COLS}
        for r in rows
        if r.get("is_disability_only")
    ]
    for i in range(0, len(picked), CHUNK):
        scrape.upsert_positions(picked[i:i + CHUNK], table=LEGACY_TABLE)
    return len(picked)


def ensure_announcement(src):
    """登记考试公告并返回 announcements.id。

    采集端在境内运行、写不了库，所以公告主表也在这里补。
    以 url 作为幂等键（announcements_url_uidx），重复导入不会产生多条。
    """
    ann = src.get("announcement") or {}
    url = ann.get("url") or src.get("list_url")
    if not url:
        return None
    payload = {
        "province_code": src.get("province_code"),
        "year": int(src.get("year") or dt.date.today().year),
        "title": ann.get("title") or src.get("name") or "考试公告",
        "url": url,
        "exam_type": src.get("exam_type") or "其他",
    }
    try:
        r = scrape.sb_post(
            ANNOUNCEMENTS_TABLE, [payload],
            {"on_conflict": "url"},
            prefer="resolution=merge-duplicates,return=representation",
        )
        created = r.json()
        return created[0]["id"] if created else None
    except Exception as e:
        print(f"[{src.get('id')}] 公告登记失败（不中断）: {e}")
        return None


def import_file(path):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    for src in payload.get("sources", []):
        rows = [enrich_row(dict(r)) for r in src.get("rows", [])]

        ds_id = ensure_data_source(src)
        ann_id = ensure_announcement(src)
        ann = src.get("announcement") or {}
        ann_url = ann.get("url") or src.get("list_url")
        ann_title = ann.get("title") or src.get("name")

        for row in rows:
            if ds_id and not row.get("source_id"):
                row["source_id"] = ds_id
            # 公告链接随行走：一条岗位即可跳转到对应考试公告
            if ann_id:
                row["announcement_id"] = ann_id
            if ann_url and not row.get("source_url"):
                row["source_url"] = ann_url

        # 1) 全量库：所有岗位
        for i in range(0, len(rows), CHUNK):
            scrape.upsert_positions(rows[i:i + CHUNK], table=FULL_TABLE)

        # 2) 存量库：仅残疾人专岗
        n_dis = sync_disability_rows(rows)

        for att in src.get("attachments", []):
            if not scrape.is_notice_seen(att.get("url")):
                scrape.record_notice(att["url"], att.get("title", ""), src["id"], kind="attachment")
        if ann_url and not scrape.is_notice_seen(ann_url):
            scrape.record_notice(ann_url, ann_title, src["id"], kind="announcement")

        summary = f"导入 {len(rows)} 条（残疾专岗 {n_dis} 条）"
        scrape.write_run_log(src["id"], f"{summary}（{pathlib.Path(path).name}）", len(rows))
        print(f"[{src['id']}] {summary}")


def main():
    files = sorted(glob.glob("data/*.json"))
    if not files:
        print("data/ 目录下没有待导入的 JSON 文件。")
        return 0
    if not scrape.SB_URL or not scrape.SB_SERVICE_KEY:
        print("缺少环境变量 SB_URL / SB_SERVICE_KEY。")
        return 1
    for path in files:
        try:
            import_file(path)
        except Exception as e:
            print(f"导入 {path} 失败: {e}")
            return 1
    try:
        scrape.mark_expired()
    except Exception as e:
        print(f"标记过期失败（不中断）: {e}")
    print("\n导入完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
