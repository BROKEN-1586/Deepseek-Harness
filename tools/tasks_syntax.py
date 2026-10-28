#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tasks_syntax.py —— 给任务行补 Obsidian **Tasks 插件** 语法（📅 到期日）

背景（用户 2026-10-19 定：操作文件时结合已安装的插件）：
  · Tasks 插件装在根库 `Obsidian\\`（92-作业清单 / 93-日程规划 是它的子文件夹，插件生效）
  · 插件只认任务行上的 emoji 语法：到期 `📅 YYYY-MM-DD`、完成 `✅ YYYY-MM-DD`
  · 我们的「截止：🔴 **10-21（还剩 2 天）**」是**给人看的**，插件不解析 →
    在任务行末尾再补一个 `📅 2026-10-21`，两边各司其职

做法：
  1. 作业清单（四行式）：任务行下面的 `- 截止：…` 里有日期 → 任务行末尾补 `📅`
  2. 日程规划：任务行里出现 `截止 MM-DD` / `（MM-DD …）` / `｜**MM-DD** 前` → 任务行末尾补 `📅`
  3. 只处理未完成 `- [ ]`；`待确认`、无日期的一律跳过

用法：
  python tasks_syntax.py           # 预演
  python tasks_syntax.py --apply   # 写入（改前备份到 _backup\\tasks-<时间戳>\\）
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

OPEN_TASK = re.compile(r"^(\s*)- \[ \] (.*)$")
DUE_LINE = re.compile(r"^\s*- 截止：")
HAVE_DATE = re.compile(r"📅\s*\d{4}-\d{2}-\d{2}")
MD = re.compile(r"(?<!\d)(\d{2})-(\d{2})(?!\d)")
DEADLINE_KW = re.compile(r"截止|｜\s*\*{0,2}\d{2}-\d{2}\*{0,2}\s*前")
TODAY = datetime.date.today()


def infer_year(mm, dd):
    """MM-DD → 年份：跨年规则（8 月起算新学年；1–7 月算下一年）。"""
    m, d = int(mm), int(dd)
    year = TODAY.year if m >= 8 or TODAY.month < 8 else TODAY.year + 1
    return year


def find_iso(text):
    """从一段文字里取第一个有效 MM-DD → ISO 日期；取不到返回 None。"""
    for mm, dd in MD.findall(text):
        try:
            return datetime.date(infer_year(mm, dd), int(mm), int(dd)).isoformat()
        except ValueError:
            continue
    return None


def process(lines):
    """返回 [(行号, 原文, 新文)]；只处理**顶层**任务行（缩进 0），子项（完成 / 提交 / ①②③）不加。"""
    out = []
    for i, line in enumerate(lines):
        m = OPEN_TASK.match(line)
        if not m or HAVE_DATE.search(line):
            continue
        if m.group(1):  # 有缩进 = 子项，跳过
            continue
        iso = None
        # ① 作业清单四行式：往下找本条的「截止：」行（跨过若干子步骤），遇到下一条顶层任务就停
        for j in range(i + 1, min(i + 16, len(lines))):
            nxt = lines[j]
            if DUE_LINE.match(nxt):
                iso = find_iso(nxt)
                break
            if nxt.startswith("#"):
                break
            mm2 = OPEN_TASK.match(nxt)
            if mm2 and not mm2.group(1):  # 下一条顶层任务 → 本条结束
                break
        # ② 日程规划：日期直接写在任务行里（须带截止语义，避免把「10-15 起」当截止）
        if not iso and DEADLINE_KW.search(line):
            iso = find_iso(line)
        if iso:
            out.append((i, line, line.rstrip() + f" 📅 {iso}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    tag = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    files, total = 0, 0
    for root_dir, backup_root in TARGET_DIRS:
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, fnames in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(fnames):
                if not name.lower().endswith(".md"):
                    continue
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                changes = process(lines)
                if not changes:
                    continue
                files += 1
                total += len(changes)
                rel = os.path.relpath(path, root_dir)
                print(f"\n[{len(changes)} 条] {rel}")
                for _, old, new in changes[:40]:
                    print(f"   - {old.strip()[:100]}")
                    print(f"   + {new.strip()[:120]}")
                if args.apply:
                    dst = os.path.join(backup_root, f"tasks-{tag}", os.path.dirname(rel))
                    os.makedirs(dst, exist_ok=True)
                    shutil.copy2(path, os.path.join(dst, name))
                    for idx, _o, new in changes:
                        lines[idx] = new
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        f.write("\n".join(lines) + "\n")

    mode = "APPLY" if args.apply else "DRY-RUN（未写入）"
    print(f"\n=== tasks_syntax [{mode}] 文件 {files} 个 / 条目 {total} 条 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
