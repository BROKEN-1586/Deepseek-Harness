# -*- coding: utf-8 -*-
"""followup.py —— 同步跟进体检（纯只读，不改任何文件）
用法: python D:\\Clearn\\tools\\followup.py [--days 21]
覆盖：作业 / 素材缺口 / 镜像一致性 / 四级 / 索引新旧 / 备份 / 时间基准自检
"""
import os, re, io, sys, glob, json, subprocess, datetime

TODAY = datetime.date.today()
DAYS = 21
if "--days" in sys.argv:
    DAYS = int(sys.argv[sys.argv.index("--days") + 1])

HW = r"D:\任务清单"
POOL = os.path.join(HW, "01-作业清单")
SNAP = os.path.join(HW, "_已取消-每日快照")  # 2026-10-27 起不再建每日快照
KEJIAN = r"C:\Users\36578\Desktop\课程\01-课件"
CET = r"C:\Users\36578\Desktop\英语四级\四级备考"
BACKUP = r"D:\backup"
OUT = r"D:\Clearn\_diag\followup.txt"
lines = []

def p(s=""):
    print(s)
    lines.append(s)

def days_of(mmdd):
    try:
        mm, dd = [int(x) for x in mmdd.split("-")]
        return (datetime.date(TODAY.year, mm, dd) - TODAY).days
    except Exception:
        return None

def label(n):
    if n is None:
        return "待确认"
    if n < 0:
        return "🔴 已逾期 %d 天" % -n
    if n == 0:
        return "🔴 今天截止"
    if n <= 3:
        return "🔴 还剩 %d 天" % n
    if n <= 13:
        return "⚠️ 还剩 %d 天" % n
    return "还剩 %d 天" % n

ROW = re.compile(r"^(\s*)- \[([ x])\] (.*)$")
DUE = re.compile(r"(\d{1,2})-(\d{1,2})")

p("=" * 68)
p("📋 同步跟进 · %s（只读体检，不改任何文件）" % TODAY.isoformat())
p("=" * 68)

# ---------- 1. 作业 ----------
p("\n【1】作业（以 01-作业清单 为准，剩余天数按今天重算）")
overdue, soon, waiting_submit = [], [], []
stale = []
for f in sorted(glob.glob(os.path.join(POOL, "*.md"))):
    subj = os.path.basename(f).replace("-作业汇总.md", "")
    ls = io.open(f, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(ls):
        m = ROW.match(ls[i])
        if not m:
            i += 1
            continue
        blk = [ls[i]]
        j = i + 1
        while j < len(ls) and (re.match(r"^\s+- \[[ x]\]", ls[j]) or ls[j].strip().startswith("- 截止")):
            blk.append(ls[j]); j += 1
        head = m.group(3)
        done = any("完成" in b and "[x]" in b for b in blk)
        subm = any("提交" in b and "[x]" in b for b in blk)
        due_line = next((b for b in blk if b.strip().startswith("- 截止")), "")
        d = DUE.search(due_line)
        n = days_of("%02d-%02d" % (int(d.group(1)), int(d.group(2)))) if d else None
        title = re.sub(r"`[^`]*`", "", head)
        title = re.sub(r"\*\*", "", title)
        title = re.sub(r"\$([^$]*)\$", r"\1", title)
        title = re.sub(r"📅\s*2026-\d{2}-\d{2}", "", title).strip()[:52]
        if not done:
            item = "%s｜%s｜%s" % (subj, title, label(n))
            (overdue if (n is not None and n < 0) else (soon if (n is not None and n <= 3) else [])).append(item)
        elif not subm:
            waiting_submit.append("%s｜%s｜%s" % (subj, title, label(n)))
        # 时间基准自检
        if d and n is not None and "还剩" in due_line:
            stated = re.search(r"还剩 (\d+) 天", due_line)
            if stated and int(stated.group(1)) != n:
                stale.append("%s %s：写「还剩 %s 天」，今天实际 %d 天" %
                             (subj, "%02d-%02d" % (int(d.group(1)), int(d.group(2))), stated.group(1), n))
        i = j
p("  逾期 %d ｜ ≤3 天 %d ｜ 只剩提交 %d" % (len(overdue), len(soon), len(waiting_submit)))
for x in overdue:
    p("   🔴 " + x)
for x in soon:
    p("   ⚠️ " + x)
for x in waiting_submit:
    p("   📮 " + x)

# ---------- 2. 素材缺口（2026-10-28 改判据：快照取消后改用「作业池出处 / 流程日志 / 每日备案」三处留痕） ----------
p("\n【2】素材缺口（近 %d 天有课件目录、但作业池 / 流程日志 / 每日备案里都没提过那一天 → 那天可能没跑流程）" % DAYS)
FLOWLOG = r"D:\Clearn\_diag\flow-log.tsv"
DAILYDIR = r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\07-备案库\02-每日任务记录"
mentioned = set()
for f in glob.glob(os.path.join(POOL, "*.md")):          # ① 作业池「出处」里写到的日期
    txt = io.open(f, encoding="utf-8", errors="replace").read()
    for mm, dd in re.findall(r"(?:2026-)?(\d{2})-(\d{2})", txt):
        mentioned.add("%s-%s" % (mm, dd))
if os.path.exists(FLOWLOG):                              # ② daily_gate 跑过的日子
    for ln in io.open(FLOWLOG, encoding="utf-8", errors="replace"):
        for mm, dd in re.findall(r"(?:20\d{2}-)?(\d{2})-(\d{2})", ln):
            mentioned.add("%s-%s" % (mm, dd))
if os.path.isdir(DAILYDIR):                              # ③ 有详版备案的日子
    for fn in os.listdir(DAILYDIR):
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", fn)
        if m:
            mentioned.add("%s-%s" % (m.group(2), m.group(3)))
gaps = []
for sub in sorted(os.listdir(KEJIAN)) if os.path.isdir(KEJIAN) else []:
    sp = os.path.join(KEJIAN, sub)
    if not os.path.isdir(sp):
        continue
    for d in sorted(os.listdir(sp)):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            continue
        dd = datetime.date(*[int(x) for x in d.split("-")])
        if not (0 <= (TODAY - dd).days <= DAYS):
            continue
        nfiles = len(os.listdir(os.path.join(sp, d)))
        md = d[5:]
        if nfiles and md not in mentioned:
            gaps.append("%s  %s（%d 个文件）" % (d, sub, nfiles))
p("  %d 天有课件但三处都没留痕（提示项，不阻塞）" % len(gaps) if gaps else "  无 ✅")
for g in gaps[:10]:
    p("   ⚠️ " + g)
if len(gaps) > 10:
    p("   …（还有 %d 条）" % (len(gaps) - 10))

# ---------- 3. 镜像一致性 ----------
p("\n【3】Obsidian 镜像一致性（真身 → 镜像，dry-run）")
try:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, r"D:\Clearn\tools\merge_and_sync.py"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=180, env=env)
    tail = [l for l in (r.stdout or "").splitlines() if "合计" in l or "两侧一致" in l]
    if tail:
        for l in tail[-2:]:
            p("   " + l.strip())
    else:
        p("   !! 预演没有输出（rc=%s）%s" % (r.returncode, (r.stderr or "")[-300:]))
except Exception as e:
    p("   !! 预演失败: %s" % e)

# ---------- 4. 四级 ----------
p("\n【4】四级备考")
SH = os.path.join(CET, r"05-生词")
cnt = {}
for sub in ["02-陌生", "01-不熟悉", "00-已掌握"]:
    d = os.path.join(SH, sub)
    tot = marked = 0
    for f in glob.glob(os.path.join(d, "*.md")):
        for l in io.open(f, encoding="utf-8").read().splitlines():
            if re.match(r"^\|\s*\d+\s*\|", l):
                tot += 1
                cells = [c.strip() for c in l.strip("|").split("|")]
                if len(cells) > 1 and cells[1].endswith("#") and not cells[1].endswith("###"):
                    marked += 1
    cnt[sub] = (tot, marked)
p("   陌生 %d 词（待流转 %d）｜不熟悉 %d 词（待流转 %d）｜已掌握 %d" %
  (cnt["02-陌生"][0], cnt["02-陌生"][1], cnt["01-不熟悉"][0], cnt["01-不熟悉"][1], cnt["00-已掌握"][0]))
for name, d in [("笔试", datetime.date(2026, 12, 12)), ("口试", datetime.date(2026, 11, 21))]:
    p("   %s %s → 还剩 %d 天" % (name, d, (d - TODAY).days))
# 词汇标记未汇总
VOC = os.path.join(CET, r"01-词汇")
marks = 0
for f in glob.glob(os.path.join(VOC, "*核心词汇-*.md")):
    for l in io.open(f, encoding="utf-8").read().splitlines():
        if re.match(r"^\|\s*\d+\s*\|", l):
            cells = [c.strip() for c in l.strip("|").split("|")]
            if len(cells) > 2 and ("#" in cells[1] or "#" in cells[3]):
                marks += 1
p("   01-词汇 里仍有 %d 行带标记（已汇总进三态表；重复跑会自动去重）" % marks)

# ---------- 5. 索引新旧（2026-10-28 扩到全部 9 个库） ----------
p("\n【5】RAG 索引新鲜度（9 个库逐个比「笔记最新 mtime vs 索引目录 mtime」）")
DB = r"D:\rag\db"
OBS = r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian"
LIBDIRS = {
    "novel":   os.path.join(OBS, "06-小说"),
    "math":    os.path.join(OBS, "90-高数笔记库-Obsidian"),
    "game":    os.path.join(OBS, "04-博弈论基础"),
    "sec":     os.path.join(OBS, "00-网安零基础学习资料清单"),
    "note":    os.path.join(OBS, "01-笔记(AI assisted)"),
    "ai":      os.path.join(OBS, "02-人工智能基础与应用"),
    "csapp":   os.path.join(OBS, "03-深入理解计算机系统"),
    "archive": os.path.join(OBS, "07-备案库"),
    "aiout":   r"C:\Users\36578\Desktop\AI产出",
}
SKIP = {".obsidian", ".trash", ".git", "_backup"}
lagging = []
for lib, data in LIBDIRS.items():
    dp = os.path.join(DB, lib)
    t_db = max((os.path.getmtime(os.path.join(dp, f)) for f in os.listdir(dp)), default=0) if os.path.isdir(dp) else 0
    t_nt, n_md = 0, 0
    if os.path.isdir(data):
        for cur, dns, fns in os.walk(data):
            dns[:] = [x for x in dns if x not in SKIP]
            for f in fns:
                if f.endswith(".md"):
                    n_md += 1
                    t_nt = max(t_nt, os.path.getmtime(os.path.join(cur, f)))
    stale = t_nt > t_db
    if stale:
        lagging.append(lib)
    p("   %-8s md=%-4d 笔记最新 %s ｜ 索引 %s  %s" % (
        lib, n_md,
        datetime.datetime.fromtimestamp(t_nt).strftime("%m-%d %H:%M") if t_nt else "—",
        datetime.datetime.fromtimestamp(t_db).strftime("%m-%d %H:%M") if t_db else "—",
        "⚠️ 索引落后，建议重建 %s-rag" % lib if stale else "✅"))
orphan = [d for d in (sorted(os.listdir(DB)) if os.path.isdir(DB) else [])
          if os.path.isdir(os.path.join(DB, d)) and d not in LIBDIRS]
if orphan:
    p("   孤儿索引目录（KB_CONFIGS 里没有）：%s —— 可删" % ", ".join(orphan))
p("   → %s" % ("需要重建：" + "、".join("%s-rag" % x for x in lagging) if lagging else "9 个库都不落后 ✅"))

# ---------- 6. 备份 ----------
p("\n【6】备份")
subs = [os.path.join(BACKUP, d) for d in os.listdir(BACKUP) if os.path.isdir(os.path.join(BACKUP, d))]
if subs:
    newest = max(subs, key=os.path.getmtime)
    p("   最新备份：%s（%s）" % (os.path.basename(newest), datetime.datetime.fromtimestamp(os.path.getmtime(newest)).strftime("%m-%d %H:%M")))
    p("   共 %d 个子目录" % len(subs))

# ---------- 7. 时间基准自检 ----------
p("\n【7】时间基准自检（活文档按今天算）")
if stale:
    p("   发现 %d 处过期天数：" % len(stale))
    for s in stale:
        p("   ⚠️ " + s)
else:
    p("   全部与今天一致 ✅")

p("\n" + "=" * 68)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("（已存 %s）" % OUT)
