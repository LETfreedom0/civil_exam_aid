#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入端：把 data/*.json 里导出的岗位数据写入 Supabase。

运行在 GitHub Actions（境外网络，可访问 supabase.co）。
数据文件由境内抓取端生成：python scripts/scrape.py --export data/xxx.json
"""

import glob
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scrape  # 复用 sb_get/sb_post/upsert_positions/record_notice/write_run_log/mark_expired

CHUNK = 500  # 每批 upsert 条数，避免单次 POST 过大


def import_file(path):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    for src in payload.get("sources", []):
        rows = src.get("rows", [])
        for i in range(0, len(rows), CHUNK):
            scrape.upsert_positions(rows[i:i + CHUNK])
        for att in src.get("attachments", []):
            if not scrape.is_notice_seen(att.get("url")):
                scrape.record_notice(att["url"], att.get("title", ""), src["id"])
        scrape.write_run_log(src["id"], f"导入 {len(rows)} 条（{pathlib.Path(path).name}）", len(rows))
        print(f"[{src['id']}] 导入 {len(rows)} 条")


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
