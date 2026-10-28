#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stamp_backfill.py —— 给历史已完成项统一补「时间标记」（用户 2026-10-19 定）

规则（只动 `- [x]` 行）：
  · 已有 `✅ YYYY-MM-DD HH:MM`            → 不动
  · 已有 `✅ YYYY-MM-DD` 或 `✅ MM-DD`     → 行尾补 `（时间未记录）`
  · 没有任何 `✅`                          → 行尾补 ` ✅ 日期未记录`

用法：
  python stamp_backfill.py           # 预演，只列改动
  python stamp_backfill.py --apply   # 写入（改前备份到 _backup\\stamp-<时间戳>\\）
"""

import argparse
import datetime
import os
import re
import shutil
import sys

TARGET_DIRS = [
    (r"D:\任务清单\01-作业清单", r"D:\任务清单\_backup"),
    (r"D:\任务清单\02-教务清单", r"D:\任务清单\_backup"),
]
SKIP_DIRS = {".obsidian", ".trash", "_backup", ".git", ".agents", "_迁移核对"}

DONE_RE = re.compile(r"^\s*- \[[xX]\] ")
FULL = re.compile(r"✅\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}")
DATE = re.compile(r"✅\s*\d{4}-\d{2}-\d{2}")
SHORT = re.compile(r"✅\s*\d{2}-\d{2}")
MARK = "（时间未记录）"


def plan(lines):
    """返回 [(行号, 原文, 新文)]"""
    out = []
    for i, line in enumerate(lines):
        if not DONE_RE.match(line):
            continue
        if FULL.search(line) or line.rstrip().endswith(MARK):
            continue
        if DATE.search(line) or SHORT.search(line):
            out.append((i, line, line.rstrip() + MARK))
        else:
            out.append((i, line, line.rstrip() + " ✅ 日期未记录"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    tag = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    total_files, total_lines = 0, 0
    for root_dir, backup_root in TARGET_DIRS:
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if not name.lower().endswith(".md"):
                    continue
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                lines = text.splitlines()
                changes = plan(lines)
                if not changes:
                    continue
                total_files += 1
                total_lines += len(changes)
                rel = os.path.relpath(path, root_dir)
                print(f"\n[{len(changes)} 条] {rel}")
                for _, old, new in changes[:60]:
                    print(f"   - {old.strip()[:110]}")
                    print(f"   + {new.strip()[:110]}")
                if args.apply:
                    dst = os.path.join(backup_root, f"stamp-{tag}", os.path.dirname(rel))
                    os.makedirs(dst, exist_ok=True)
                    shutil.copy2(path, os.path.join(dst, name))
                    for idx, _old, new in changes:
                        lines[idx] = new
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        f.write("\n".join(lines) + "\n")

    mode = "APPLY" if args.apply else "DRY-RUN（未写入）"
    print(f"\n=== stamp_backfill [{mode}] 文件 {total_files} 个 / 条目 {total_lines} 条 ===")
    if not args.apply and total_lines:
        print("（预演：加 --apply 才写）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
