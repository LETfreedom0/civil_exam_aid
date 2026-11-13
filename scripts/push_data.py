#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
境内抓取端一键脚本：抓取 → 导出 data/*.json → 推送到 GitHub → 触发云端导入。

用法（在项目根目录执行）：
  python scripts/push_data.py            # 抓全部启用的数据源
  python scripts/push_data.py --dry-run  # 只导出不推送

原理：境内站点（如 gxpta.com.cn）屏蔽境外 IP，抓取必须在本地执行；
     supabase.co 又被境内网络阻断，写入必须在 GitHub Actions 执行。
     中间用仓库 data/ 目录传数据文件，push 自动触发 import 工作流。
"""

import argparse
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def run(cmd, cwd=None, capture=False):
    print("+", " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, cwd=cwd or ROOT, shell=False,
                       capture_output=capture, text=True,
                       encoding="utf-8", errors="replace")
    if capture and r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        if r.stderr.strip():
            print(r.stderr.strip())
        sys.exit(f"命令失败（exit {r.returncode}）：{' '.join(str(c) for c in cmd)}")
    return r


def main():
    parser = argparse.ArgumentParser(description="抓取并推送数据到 GitHub 触发导入")
    parser.add_argument("--dry-run", action="store_true", help="只导出 JSON，不推送")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "scrape-latest.json"
    run([sys.executable, str(ROOT / "scripts" / "scrape.py"), "--export", str(out)])

    if args.dry_run:
        print("\n[dry-run] 已导出，未推送。")
        return 0

    # 用临时 worktree 把 data/ 干净地叠加到远端 main 上，再触发 import 工作流
    fetch = subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT,
                           capture_output=True, text=True)
    if fetch.returncode != 0:
        sys.exit(f"git fetch 失败: {fetch.stderr.strip()}")

    tmp = tempfile.mkdtemp(prefix="cea-data-")
    run(["git", "worktree", "add", "--detach", tmp, "origin/main"])
    try:
        dest = pathlib.Path(tmp) / "data"
        dest.mkdir(exist_ok=True)
        for f in DATA_DIR.glob("*.json"):
            (dest / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        run(["git", "add", "-A"], cwd=tmp)
        run(["git", "commit", "-m", f"data: {out.name}（本地抓取 {out.stat().st_size // 1024}KB）"], cwd=tmp)
        run(["git", "push", "origin", "HEAD:main"], cwd=tmp)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", tmp], cwd=ROOT,
                       capture_output=True, text=True)
    print("\n推送完成，GitHub Actions 的 import 工作流会自动把数据写入 Supabase。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
