# -*- coding: utf-8 -*-
r"""daily-gate —— 每日流程的机器判据（2026-10-20 建；**2026-10-27 改版**：任务清单库）

为什么要有它：DEEPCODE §E 的「会话开始先判幂等」原本靠我读文件、靠我判断，
会漏。这个脚本把判断变成**文件里的答案**，会话开场只要读一行 verdict 即可。

🔴 2026-10-27 用户的改版（旧 `D:\日程规划` 库已删）：
  · 作业清单 → **任务清单**（`D:\任务清单`），下设两大**类**：`01-作业清单` / `02-教务清单`
  · **不再每天新建一篇笔记**（旧 `02-按日期\\<日期>-作业清单.md` 与 `01-日记\\<日期>.md` 全部取消）
  · 判据因此改为「今天有没有**新素材**没归档」：
      FULL = `01-课件\*\<今天>\` 有课件，或 `02-作业\作业来源\<今天>\` 存在（→ 读素材、核对、落盘）
      LITE = 没有新素材（→ 只报未完成 + 风险 + 镜像一致性）

附带情报：镜像是否一致、作业未完成 / 只剩提交条数、教务清单未完成条数、≤3（作业）/ ≤7（教务）天风险。

输出：D:\\Clearn\\_diag\\daily-gate.txt（UTF-8，覆盖写）
用法：python D:\\Clearn\\tools\\daily_gate.py [--date YYYY-MM-DD]
"""

import argparse
import glob
import os
import re
import sys
from datetime import date, datetime, timedelta

# 控制台 GBK 兜底（同 merge_and_sync.py 的坑：打印含 emoji/中文会 UnicodeEncodeError）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ---------- 路径（2026-10-27 新口径） ----------
TASK_ROOT = r"D:\任务清单"
POOL_DIR = os.path.join(TASK_ROOT, "01-作业清单")          # 6 个科目池
JIAOWU_DIR = os.path.join(TASK_ROOT, "02-教务清单")        # 考试 / 课程 / 计划 / 证明 / 其它
OVERVIEW = os.path.join(TASK_ROOT, "00-总览", "00-任务总览.md")
MIRROR = r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\92-任务清单"

COURSEWARE_ROOT = r"C:\Users\36578\Desktop\课程\01-课件"     # 01-课件\<科目>\<日期>\
SOURCE_ROOT = r"C:\Users\36578\Desktop\课程\02-作业\作业来源"  # 作业来源\<日期>\

OUT_DIR = r"D:\Clearn\_diag"
OUT_FILE = os.path.join(OUT_DIR, "daily-gate.txt")

SKIP_DIRS = {".obsidian", ".trash", "_backup", ".git", ".agents", "99-Templates", "_迁移核对"}

TASK_RE = re.compile(r"^(\s*)- \[( |x|X)\] (.*)$")
# ✅ 时间戳（半角/全角冒号都认），比对时剥掉，避免"仅时间戳格式不同"被误判成内容差异
STAMP_RE = re.compile(r"\s*✅\s*\d{4}-\d{2}-\d{2}(?:\s*\d{1,2}[:：]\d{2})?\s*$")
DUE_ISO_RE = re.compile(r"📅\s*(\d{4})-(\d{2})-(\d{2})")
DUE_MD_RE = re.compile(r"截止[：:]\s*\**[^\d\[]{0,6}(\d{2})-(\d{2})")


def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return None


def norm_line(line):
    return STAMP_RE.sub("", line).strip()


def _collect_dates(line, bucket, year):
    """从一行里抓截止日期（ISO 2026-11-15 与 简写 10-31 两种）。"""
    for m in DUE_ISO_RE.finditer(line):
        try:
            bucket.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass
    for m in DUE_MD_RE.finditer(line):
        try:
            bucket.append(date(year, int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass


def parse_blocks(lines, year=None):
    """把「四行式」条目解析成块，避免父行/完成/提交被重复计数。

    块 = 一个顶层任务行 ＋ 其后的缩进子行 / `截止：` 行，直到下一个顶层任务行或 `##` 标题。
    返回 [{"checked": bool, "text": str, "children": [(bool, str)], "dates": [date]}]
    """
    year = year or date.today().year
    blocks, cur = [], None
    for ln in lines:
        if ln.startswith("#"):
            if cur:
                blocks.append(cur)
            cur = None
            continue
        m = TASK_RE.match(ln)
        if m and len(m.group(1)) == 0:
            if cur:
                blocks.append(cur)
            cur = {"checked": m.group(2) in "xX",
                   "text": norm_line(m.group(3))[:90],
                   "children": [], "dates": []}
            _collect_dates(ln, cur["dates"], year)
            continue
        if cur is None:
            continue
        if m:  # 缩进子项：完成 / 提交（或考试类的 准备 / 赴考）
            cur["children"].append((m.group(2) in "xX", norm_line(m.group(3))[:12]))
        _collect_dates(ln, cur["dates"], year)
    if cur:
        blocks.append(cur)
    return blocks


def summarize(blocks):
    """→ (未完成块, 只剩提交块)。

    只剩提交 = 父行仍未勾，但子项里的「完成」已勾、「提交」未勾
    （四行式里父行要等两项都勾才算完，所以不能只看父行状态）。
    """
    pending = [b for b in blocks if not b["checked"]]
    only_submit = []
    for b in pending:
        done = [ok for ok, lbl in b["children"] if "完成" in lbl]
        submit = [ok for ok, lbl in b["children"] if "提交" in lbl]
        if done and all(done) and submit and not all(submit):
            only_submit.append(b)
    return pending, only_submit


def compare_pair(truth, mirror):
    """比较真身/镜像内容；只认内容差异，忽略 ✅ 时间戳格式差异。"""
    t, m = read_lines(truth), read_lines(mirror)
    if t is None or m is None:
        return None
    return [norm_line(x) for x in t] == [norm_line(x) for x in m]


def mirror_diffs():
    """返回不一致的文件（相对路径）列表。"""
    diffs = []
    for root, dirs, files in os.walk(TASK_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            tp = os.path.join(root, name)
            rel = os.path.relpath(tp, TASK_ROOT)
            ok = compare_pair(tp, os.path.join(MIRROR, rel))
            if ok is False:
                diffs.append(rel)
    return diffs


def new_material(today):
    """今天有没有还没归档的素材 → (bool, 说明列表)。"""
    notes = []
    d = today.isoformat()
    for p in glob.glob(os.path.join(COURSEWARE_ROOT, "*", d)):
        if os.path.isdir(p):
            notes.append("课件：" + os.path.relpath(p, COURSEWARE_ROOT))
    for p in glob.glob(os.path.join(SOURCE_ROOT, d)) + glob.glob(os.path.join(SOURCE_ROOT, d[5:])):
        if os.path.isdir(p):
            notes.append("作业来源：" + p)
    return bool(notes), notes


def collect_risks(today, horizon, pool_dir):
    """扫池：**只看未完成**的块，返回 ≤horizon 天或已逾期 的条目。"""
    risks = []
    if not os.path.isdir(pool_dir):
        return risks
    for name in sorted(os.listdir(pool_dir)):
        if not name.endswith(".md"):
            continue
        blocks = parse_blocks(read_lines(os.path.join(pool_dir, name)) or [], year=today.year)
        pending, _ = summarize(blocks)
        for b in pending:
            for dd in b["dates"]:
                left = (dd - today).days
                if left > horizon:
                    continue
                tag = (f"已逾期 {abs(left)} 天" if left < 0
                       else "今天到期" if left == 0 else f"还剩 {left} 天")
                risks.append(f"{name[:-3]}｜{b['text'][:60]}｜{dd.isoformat()}（{tag}）")
    seen, out = set(), []
    for r in risks:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="基准日期 YYYY-MM-DD，默认今天")
    args = ap.parse_args()

    today = (datetime.strptime(args.date, "%Y-%m-%d").date()
             if args.date else date.today())

    has_mat, mat_notes = new_material(today)
    verdict = "FULL" if has_mat else "LITE"

    # ---------- 作业池 ----------
    hw_pending, hw_submit_only, hw_total = [], [], 0
    if os.path.isdir(POOL_DIR):
        for name in sorted(os.listdir(POOL_DIR)):
            if not name.endswith(".md"):
                continue
            blocks = parse_blocks(read_lines(os.path.join(POOL_DIR, name)) or [], year=today.year)
            pending, only = summarize(blocks)
            for b in pending:
                hw_pending.append(dict(b, src=name[:-3]))
            for b in only:
                hw_submit_only.append(dict(b, src=name[:-3]))
            hw_total += len(pending)

    # ---------- 教务清单 ----------
    jw_pending = []
    if os.path.isdir(JIAOWU_DIR):
        for name in sorted(os.listdir(JIAOWU_DIR)):
            if not name.endswith(".md"):
                continue
            blocks = parse_blocks(read_lines(os.path.join(JIAOWU_DIR, name)) or [], year=today.year)
            pending, _ = summarize(blocks)
            for b in pending:
                jw_pending.append(dict(b, src=name[:-3]))

    diffs = mirror_diffs()
    hw_risks = collect_risks(today, 3, POOL_DIR)
    jw_risks = collect_risks(today, 7, JIAOWU_DIR)

    # ---------- 组装输出 ----------
    L = []
    L.append(f"=== daily-gate {today.isoformat()} {datetime.now().strftime('%H:%M')} ===")
    L.append("")
    L.append(f"VERDICT: {verdict}"
             + ("   → 有新素材：跑完整版（合并预演 → 读素材 → 核对 → 落盘）" if verdict == "FULL"
                else "   → 无新素材：只报未完成 + 风险（**不重读课件/截图**）"))
    L.append(f"今天的素材: {'🆕 ' + str(len(mat_notes)) + ' 处' if mat_notes else '— 无（今天没有新课件 / 作业来源目录）'}")
    for x in mat_notes:
        L.append(f"    · {x}")
    L.append("")
    L.append(f"镜像（真身 D:\\任务清单 ↔ Obsidian\\92-任务清单）: "
             + ("✅ 两侧一致" if not diffs else f"⚠️ {len(diffs)} 处不一致（先跑 merge-sync 预演）"))
    for x in diffs[:8]:
        L.append(f"    · {x}")
    if len(diffs) > 8:
        L.append(f"    · …另有 {len(diffs) - 8} 处")
    L.append("")
    L.append(f"作业清单: 未完成 {len(hw_pending)} 条（其中只剩提交 {len(hw_submit_only)} 条）")
    for b in hw_pending[:12]:
        L.append(f"    - [{b['src']}] {b['text'][:80]}")
    if len(hw_pending) > 12:
        L.append(f"    …另有 {len(hw_pending) - 12} 条")
    L.append(f"教务清单: 未完成 {len(jw_pending)} 条")
    for b in jw_pending[:12]:
        L.append(f"    - [{b['src']}] {b['text'][:80]}")
    if len(jw_pending) > 12:
        L.append(f"    …另有 {len(jw_pending) - 12} 条")
    L.append("")
    L.append(f"风险 · 作业（≤3 天或逾期）: {len(hw_risks)} 条")
    for x in hw_risks[:8]:
        L.append(f"    🔴 {x}")
    L.append(f"风险 · 教务（≤7 天）: {len(jw_risks)} 条")
    for x in jw_risks[:10]:
        L.append(f"    ⚠️ {x}")
    L.append("")
    L.append("下一步建议：")
    steps = []
    if diffs:
        steps.append("先 `python D:\\Clearn\\tools\\merge_and_sync.py` 预演；有「镜像独有/内容差异」逐条列给用户")
    if verdict == "FULL":
        steps.append("`delegate(source=\"read-the-night\")` 读当天素材（子代理跑，图不进主上下文）")
        steps.append("新作业 / 教务节点（科目/任务/截止/出处）列给用户核对，**点头才写进 01-作业清单 或 02-教务清单**")
    else:
        steps.append("只报未完成 + 风险 + ≤7 天节点，**不重读素材、不新建笔记**（新口径：不再每天建一篇）")
    steps.append("收尾按 §D 逐项过（同步镜像 / 记问题汇总 / 落 DEEPCODE / 备案）")
    for i, s in enumerate(steps, 1):
        L.append(f"  {i}) {s}")

    text = "\n".join(L) + "\n"
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    # 2026-10-28 新增：把「流程跑过的日子」留痕 —— followup【2】素材缺口靠它判「那天跑没跑」
    try:
        flow = os.path.join(OUT_DIR, "flow-log.tsv")
        old = open(flow, encoding="utf-8", errors="replace").read() if os.path.exists(flow) else ""
        if today.isoformat() not in old:
            with open(flow, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("%s\t%s\t%s\n" % (today.isoformat(), verdict,
                                            datetime.now().strftime("%H:%M:%S")))
    except OSError:
        pass

    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
