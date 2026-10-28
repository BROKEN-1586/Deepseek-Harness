#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_and_sync.py —— 合并「真身」与「Obsidian 镜像」的勾选状态，并把真身同步到镜像。

背景（用户 2026-10-19 定）：
  · 勾选可能在 Obsidian 镜像里做，也可能在真身（作业清单 / 日程规划）里做 → 两边都要读，取并集。
  · 每一项勾选要带时间：`- [x] 完成 ✅ 2026-10-19 10:20`。
    Obsidian 原生勾选框**不产生时间戳**，所以镜像里的勾只能在「检测到差异的那一刻」打时间，
    属于「检测时间」而非「真实点击时间」——脚本会把这些条目标出来，供人工核对 / 改时间。

规则：
  1. 勾选：双向取并集。镜像已勾、真身未勾 → 回写进真身并补时间戳。
  2. 内容 / 截止 / 新增 / 删除：只认真身；镜像里多出来的条目只报告，不自动合并。
  3. 改前备份真身与镜像到 `_backup\\merge-<时间戳>\\`。
  4. 最后把真身覆盖到镜像（robocopy 等价），两侧归一。

用法：
  python D:\\Clearn\\tools\\merge_and_sync.py            # 预演（dry-run），只报告不写
  python D:\\Clearn\\tools\\merge_and_sync.py --apply    # 真正写入 + 同步
  python D:\\Clearn\\tools\\merge_and_sync.py --apply --stamp "2026-10-19 09:30"
                                                       # 指定回写用时间（用户报的实际勾选时间）
"""

import argparse
import datetime
import difflib
import os
import re
import shutil
import sys

# ---------- 控制台编码兜底（2026-10-19 修） ----------
# Windows 控制台默认 GBK，打印汇总行里的 📅 会 UnicodeEncodeError 直接崩（看着像同步失败，
# 其实写入早已完成）。强制 stdout/stderr 走 UTF-8 并容错，避免「假失败」。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ---------- 路径（真身 / 镜像） ----------
TASK_ROOT = r"D:\任务清单"                                  # 2026-10-27 新库（旧 日程规划 + 作业清单 合并）
MIRROR_ROOT = r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\92-任务清单"
HOMEWORK_TRUTH_DIR = os.path.join(TASK_ROOT, "01-作业清单")
HOMEWORK_TRUTH_OVERVIEW = os.path.join(TASK_ROOT, "00-总览", "00-作业总览.md")
HOMEWORK_BACKUP_DIR = os.path.join(TASK_ROOT, "_backup")
HOMEWORK_MIRROR_DIR = os.path.join(MIRROR_ROOT, "01-作业清单")

PLAN_TRUTH_DIR = os.path.join(TASK_ROOT, "02-教务清单")      # 旧 日程规划 → 教务清单
PLAN_BACKUP_DIR = os.path.join(TASK_ROOT, "_backup")
PLAN_MIRROR_DIR = os.path.join(MIRROR_ROOT, "02-教务清单")

SKIP_DIRS = {".obsidian", ".trash", "_backup", ".git", ".agents"}

TASK_RE = re.compile(r"^(\s*)- \[( |x|X)\] (.*)$")
# 时间戳：日期 + 可选「时:分」。冒号**半角 / 全角都认**——用户在 Obsidian 里常打「：」（2026-10-19 用户要求加兼容）
STAMP_RE = re.compile(r"\s*✅\s*\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}[:：]\d{2})?\s*$")
# 只动 ✅ 时间戳里的全角冒号，不碰正文里的「：」
FULLWIDTH_STAMP_RE = re.compile(r"(✅\s*\d{4}-\d{2}-\d{2}\s+\d{1,2})：(\d{2})")


def normalize_stamps(lines):
    """把 ✅ 时间戳里的全角冒号改写成半角，返回新列表（2026-10-19）。"""
    return [FULLWIDTH_STAMP_RE.sub(r"\1:\2", ln) for ln in lines]


def norm(text: str) -> str:
    """比对用的键：去掉行尾 ✅ 时间戳，去掉首尾空白。"""
    return STAMP_RE.sub("", text).strip()


def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def backup(path, backup_root, tag, suffix=""):
    r"""备份到 `_backup\merge-<tag>\<文件名><suffix>.md`。
    suffix 用来区分真身 / 镜像——否则两个同名副本互相覆盖，
    改前的真身会被镜像冲掉（2026-10-19 修）。"""
    if not os.path.exists(path):
        return
    dst_dir = os.path.join(backup_root, f"merge-{tag}")
    os.makedirs(dst_dir, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(path))
    shutil.copy2(path, os.path.join(dst_dir, base + suffix + ext))


def post_check(truth_path, mirror_path):
    """复制后复核：两侧是否真的一致——避免报告里残留「镜像独有」的假象（2026-10-19 用户要求）。"""
    try:
        t = read_lines(truth_path)
        m = read_lines(mirror_path)
    except OSError as exc:
        return f"复核失败：{exc}"
    if t == m:
        return "两侧一致 ✅"
    diff = sum(1 for a, b in zip(t, m) if a != b) + abs(len(t) - len(m))
    return f"仍有 {diff} 行不同 ⚠️"


def merge_pair(truth_path, mirror_path, stamp, apply_changes, tag):
    """返回 (合并的勾选条目列表, 镜像独有条目列表, 其他差异行数)。"""
    result = {"merged": [], "mirror_only": [], "other_diff": 0, "status": "",
              "normalized": 0, "post": ""}

    if not os.path.exists(mirror_path):
        result["status"] = "镜像缺失 → 直接生成"
        if apply_changes:
            os.makedirs(os.path.dirname(mirror_path), exist_ok=True)
            shutil.copy2(truth_path, mirror_path)
        return result

    truth_raw = read_lines(truth_path)
    truth = normalize_stamps(truth_raw)
    mirror_raw = read_lines(mirror_path)
    mirror = normalize_stamps(mirror_raw)
    result["normalized"] = (sum(1 for a, b in zip(truth_raw, truth) if a != b)
                            + sum(1 for a, b in zip(mirror_raw, mirror) if a != b))

    def stamp_of(line):
        m = STAMP_RE.search(line)
        return m.group(0).strip() if m else ""

    def task_entries(lines):
        """[(key, checked, stamp, idx)]；key=(父条目文本, 本条文本, 缩进)。
        带上父条目是为了避免各条作业下的「完成 / 提交」撞键。"""
        ents, parent = [], None
        for i, line in enumerate(lines):
            m = TASK_RE.match(line)
            if not m:
                continue
            indent = len(m.group(1))
            body = m.group(3)
            if indent == 0:
                parent = norm(body)
            ents.append(((parent, norm(body), indent), m.group(2) in "xX", stamp_of(line), i))
        return ents

    m_ents = {e[0]: (e[1], e[2]) for e in task_entries(mirror)}
    t_ents = task_entries(truth)

    out = list(truth)
    changed = False
    for key, checked, _st, idx in t_ents:
        if checked:
            continue
        hit = m_ents.get(key)
        if hit and hit[0]:
            m = TASK_RE.match(truth[idx])
            indent, body = m.group(1), m.group(3)
            stamp_text = hit[1] or f"✅ {stamp}"
            out[idx] = f"{indent}- [x] {body.rstrip()} {stamp_text}"
            result["merged"].append(key[1])
            changed = True

    # 真身里不存在、镜像里有的任务条目（不自动合并，只报告）
    truth_keys = {e[0] for e in t_ents}
    result["mirror_only"] = [k[1] for k in m_ents.keys() if k not in truth_keys]

    # 非任务行差异（文字 / 截止被改）
    t_plain = [l for l in truth if not TASK_RE.match(l)]
    m_plain = [l for l in mirror if not TASK_RE.match(l)]
    if t_plain != m_plain:
        diff = list(difflib.unified_diff(t_plain, m_plain, lineterm="", n=0))
        result["other_diff"] = sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))

    if changed or result["normalized"]:
        result["status"] = "已回写勾选" if changed else "已规范时间（全角→半角）"
        if apply_changes:
            root = _backup_root_for(truth_path)
            backup(truth_path, root, tag)
            backup(mirror_path, root, tag, suffix="-镜像")
            write_lines(truth_path, out)
            shutil.copy2(truth_path, mirror_path)
            result["post"] = post_check(truth_path, mirror_path)
    else:
        result["status"] = "无需回写（或镜像里没有新勾）"
        if apply_changes and (result["normalized"] or read_lines(truth_path) != mirror):
            root = _backup_root_for(truth_path)
            backup(truth_path, root, tag)
            backup(mirror_path, root, tag, suffix="-镜像")
            write_lines(truth_path, truth)
            shutil.copy2(truth_path, mirror_path)
            result["post"] = post_check(truth_path, mirror_path)

    return result


def _backup_root_for(truth_path):
    return PLAN_BACKUP_DIR if truth_path.startswith(PLAN_TRUTH_DIR) else HOMEWORK_BACKUP_DIR


def collect_pairs():
    pairs = []  # (truth, mirror)
    if os.path.isdir(HOMEWORK_TRUTH_DIR):
        for name in sorted(os.listdir(HOMEWORK_TRUTH_DIR)):
            if name.lower().endswith(".md"):
                pairs.append((os.path.join(HOMEWORK_TRUTH_DIR, name),
                              os.path.join(HOMEWORK_MIRROR_DIR, name)))
    if os.path.exists(HOMEWORK_TRUTH_OVERVIEW):
        pairs.append((HOMEWORK_TRUTH_OVERVIEW,
                      os.path.join(MIRROR_ROOT, "00-总览", "00-作业总览.md")))
    _ov = os.path.join(TASK_ROOT, "00-总览", "00-任务总览.md")
    if os.path.exists(_ov):
        pairs.append((_ov, os.path.join(MIRROR_ROOT, "00-总览", "00-任务总览.md")))

    if os.path.isdir(PLAN_TRUTH_DIR):
        for root, dirs, files in os.walk(PLAN_TRUTH_DIR):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                if not name.lower().endswith(".md"):
                    continue
                tp = os.path.join(root, name)
                rel = os.path.relpath(tp, PLAN_TRUTH_DIR)
                pairs.append((tp, os.path.join(PLAN_MIRROR_DIR, rel)))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正写入并同步（默认只预演）")
    ap.add_argument("--stamp", default=None, help='回写用的时间戳，默认 "YYYY-MM-DD"（只到天，2026-10-20 用户定的口径）')
    args = ap.parse_args()

    stamp = args.stamp or datetime.datetime.now().strftime("%Y-%m-%d")
    tag = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    pairs = collect_pairs()
    total_merged, total_mirror_only, total_other, total_norm = 0, 0, 0, 0
    lines_out = []

    for truth, mirror in pairs:
        if not os.path.exists(truth):
            continue
        r = merge_pair(truth, mirror, stamp, args.apply, tag)
        rel = os.path.basename(truth)
        if r["merged"]:
            total_merged += len(r["merged"])
            lines_out.append(f"[勾选回写 {len(r['merged'])}] {rel}  ← 来自镜像（时间用 {stamp}，若不符请告知实际时间）")
            for k in r["merged"]:
                lines_out.append(f"    · {k[:70]}")
        if r["mirror_only"]:
            total_mirror_only += len(r["mirror_only"])
            lines_out.append(f"[镜像独有 {len(r['mirror_only'])}] {rel}  ← 需人工判断，未合并")
            for k in r["mirror_only"]:
                lines_out.append(f"    ? {k[:70]}")
        if r["other_diff"]:
            total_other += r["other_diff"]
            lines_out.append(f"[内容差异 {r['other_diff']} 行] {rel}  ← 只认真身，未合并")
        if r["normalized"]:
            total_norm += r["normalized"]
            lines_out.append(f"[时间规范化 {r['normalized']} 行] {rel}  ← 全角「：」→ 半角「:」")
        if r["post"]:
            lines_out.append(f"    [复制后复核] {r['post']}")
        if r["status"] == "镜像缺失 → 直接生成":
            lines_out.append(f"[新建镜像] {rel}")

    mode = "APPLY" if args.apply else "DRY-RUN（未写入）"
    print(f"=== merge_and_sync [{mode}] 时间基准 {stamp} ===")
    print(f"比对文件 {len(pairs)} 对")
    if lines_out:
        print("\n".join(lines_out))
    else:
        print("两侧一致，无需处理。")
    print(f"\n合计：勾选回写 {total_merged} 条｜镜像独有 {total_mirror_only} 条｜内容差异 {total_other} 行｜时间规范化 {total_norm} 行")
    if not args.apply and (total_merged or total_other or total_mirror_only):
        print("（预演模式：加 --apply 才会写入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
