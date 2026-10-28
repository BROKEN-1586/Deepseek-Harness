# -*- coding: utf-8 -*-
"""syncflow.py —— 「同步跟进」：检测你改了哪些文件，按规则把连带文件一次改到位。

你动手 → 跑这个（或跟我说「同步一下」）→ 它按规则把**派生量**全改好：
  ① 05-生词：陌生里带 # → 不熟悉；不熟悉里带 # → 已掌握（去标记、重排序号）
  ② 01-词汇：新打的 #/## → 去重汇总进三态表（满 100 自动拆篇）
  ③ 作业池：剩余天数按今天重算、完成＋提交都勾的条目折成一行、updated 对齐
  ④ 快照：按「那一页自己的日期」重算剩余天数
  ⑤ 总览：三级词数、按日期表补漏登、updated
  ⑥ 镜像：真身 → Obsidian（含勾选并集回写）
  ⑦ 索引：笔记/资料比索引新时**只报告**（加 --rebuild-index 才真重建）
默认**预演**；加 --apply 才写。所有写入前都进 D:\\backup\\syncflow-<ts>\\。
"""
import os, re, io, sys, glob, json, shutil, subprocess, datetime

APPLY = "--apply" in sys.argv
REBUILD = "--rebuild-index" in sys.argv
TODAY = datetime.date.today()
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = os.path.join(r"D:\backup", "syncflow-" + TS)
PY = sys.executable
HW = r"D:\任务清单"
POOL, SNAP, HWO = os.path.join(HW, "01-作业清单"), os.path.join(HW, "_已取消-每日快照"), os.path.join(HW, "00-总览", "00-作业总览.md")  # 2026-10-27 起无每日快照
PAGES = os.path.join(HW, "02-教务清单")  # 2026-10-28 补：教务页的「剩余天数」同样每次重算（DEEPCODE 本节 §4「两处通用」）
CET = r"C:\Users\36578\Desktop\英语四级\四级备考"
SH, VOC, CETO = os.path.join(CET, "05-生词"), os.path.join(CET, "01-词汇"), os.path.join(CET, r"00-总览\00-四级备考总览.md")
NOTE = r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\01-笔记(AI assisted)"
DBSRC = {"note": NOTE, "math": r"C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\90-高数笔记库-Obsidian"}

report = []
def say(s=""):
    print(s); report.append(s)

def save(path, text):
    if not APPLY:
        return False
    os.makedirs(BK, exist_ok=True)
    dst = os.path.join(BK, os.path.basename(os.path.dirname(path)) + "_" + os.path.basename(path))
    if os.path.exists(path):
        shutil.copy2(path, dst)
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    return True

def days(mm, dd):
    try:
        return (datetime.date(TODAY.year, int(mm), int(dd)) - TODAY).days
    except ValueError:
        return None

def lab(n):
    if n is None:  return "待确认"
    if n < 0:      return "已逾期 %d 天" % -n
    if n == 0:     return "今天截止"
    if n <= 3:     return "还剩 %d 天" % n
    if n <= 13:    return "还剩 %d 天" % n
    return "还剩 %d 天" % n

DUE = re.compile(r"^(\s*- 截止：)([^0-9*]*?)\*\*(\d{1,2})-(\d{1,2})（([^）]*)）(.*?)\*\*(.*)$")
ROW = re.compile(r"^\|\s*\d+\s*\|")

# ---------- ① ② 四级：调现成脚本 ----------
def run(cmd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

say("=" * 66)
say("🔁 同步跟进 · %s · %s" % (TODAY, "写入模式" if APPLY else "预演（不写）"))
say("=" * 66)

say("\n【① 05-生词：三态流转】")
if APPLY:
    rc, out = run([PY, r"D:\Clearn\tools\cet4_shengci_flow.py"])
    for l in out.strip().splitlines():
        if "：" in l or "移" in l or "现" in l:
            say("   " + l.strip()[:120])
    if rc: say("   !! rc=%s" % rc)
else:
    marked = 0
    for sub in ["02-陌生", "01-不熟悉"]:
        for f in glob.glob(os.path.join(SH, sub, "*.md")):
            for l in io.open(f, encoding="utf-8").read().splitlines():
                if ROW.match(l):
                    c = [x.strip() for x in l.strip("|").split("|")]
                    if len(c) > 1 and c[1].endswith("#") and not c[1].endswith("###"):
                        marked += 1
    say("   待流转 %d 个词（预演：加 --apply 才搬）" % marked)

say("\n【② 01-词汇：标记汇总进三态表】")
if APPLY:
    rc, out = run([PY, r"D:\Clearn\tools\cet4_vocab_marks.py", "all", "--apply"])
    for l in out.strip().splitlines():
        if "：" in l or "现" in l or "命中" in l:
            say("   " + l.strip()[:120])
else:
    say("   预演：可用 `cet4_vocab_marks.py all --apply` 汇总（本工具已内置）")

# ---------- ③ ④ ⑤ 作业：天数重算 + 折叠 + 总览 ----------
say("\n【③ 作业池 ＋ 教务页：剩余天数 / 折叠已完成 / updated】")
changed_files = 0

def due_new(l):
    """重算一行「- 截止：…（还剩 N 天）」，返回 (新行, 是否改动)；不匹配则原样返回。"""
    m = DUE.match(l)
    if not m:
        return l, False
    n = days(m.group(3), m.group(4))
    if n is None:
        return l, False
    pre = "🔴 " if n <= 3 else ("⚠️ " if n <= 13 else "")
    new = "%s%s**%02d-%02d（%s）%s**%s" % (m.group(1), pre, int(m.group(3)), int(m.group(4)), lab(n), m.group(6), m.group(7))
    return new, new != l
for f in sorted(glob.glob(os.path.join(POOL, "*.md"))) + sorted(glob.glob(os.path.join(PAGES, "*.md"))):
    lines = io.open(f, encoding="utf-8").read().splitlines()
    out, n_due, n_fold = [], 0, 0
    i = 0
    while i < len(lines):
        l = lines[i]
        new, ch = due_new(l)
        if new != l:
            n_due += 1
            out.append(new); i += 1; continue
        if re.match(r"^- \[x\] ", l):
            blk = [l]; j = i + 1
            while j < len(lines) and (re.match(r"^\s+- \[[ x]\]", lines[j]) or lines[j].strip().startswith("- 截止")):
                blk.append(lines[j]); j += 1
            done = any("完成" in b and "[x]" in b for b in blk)
            subm = any("提交" in b and "[x]" in b for b in blk)
            if done and subm and len(blk) > 1:
                def d(b):
                    mm2 = re.search(r"(\d{4}-\d{2}-\d{2})", b)
                    return mm2.group(1) if mm2 else "日期未记录"
                head = blk[0].rstrip()
                if "（完成" not in head:
                    head += "（完成 %s、提交 %s）" % (d(next(b for b in blk if "完成" in b)), d(next(b for b in blk if "提交" in b)))
                out.append(head); n_fold += 1; i = j; continue
            # 🔴 2026-10-28 两处修：① 没到「完成＋提交都勾」时原来只留首行、把 完成/提交/截止 子行丢了（真写会静默删行）
            #    ② 子行里的「- 截止：」以前被折叠 while 吞掉、从不重算 → 已勾条目的剩余天数一直漂移。整块保留并逐行重算。
            fixed = [blk[0]]
            for b in blk[1:]:
                nb, ch2 = due_new(b)
                if ch2:
                    n_due += 1
                fixed.append(nb)
            out.extend(fixed); i = j; continue
        out.append(l); i += 1
    new_txt = "\n".join(out) + "\n"
    m2 = re.search(r"^updated:\s*\d{4}-\d{2}-\d{2}$", new_txt, re.M)
    if (n_due or n_fold or new_txt != io.open(f, encoding="utf-8").read()):
        if m2:
            new_txt = re.sub(r"^updated:\s*\d{4}-\d{2}-\d{2}$", "updated: " + TODAY.isoformat(), new_txt, count=1, flags=re.M)
        if save(f, new_txt):
            changed_files += 1
        say("   %-30s 天数 %d 处 / 折叠 %d 条" % (os.path.basename(f), n_due, n_fold))

say("\n【④ 快照：按那一页自己的日期重算天数】")
for f in sorted(glob.glob(os.path.join(SNAP, "*.md"))):
    ds = re.search(r"(\d{4})-(\d{2})-(\d{2})", os.path.basename(f))
    if not ds:
        continue
    base = datetime.date(int(ds.group(1)), int(ds.group(2)), int(ds.group(3)))
    lines = io.open(f, encoding="utf-8").read().splitlines()
    out, n = [], 0
    for l in lines:
        m = DUE.match(l)
        if m:
            try:
                due = datetime.date(base.year, int(m.group(3)), int(m.group(4)))
                k = (due - base).days
            except ValueError:
                out.append(l); continue
            pre = "🔴 " if k <= 3 else ("⚠️ " if k <= 13 else "")
            new = "%s%s**%02d-%02d（%s）%s**%s" % (m.group(1), pre, int(m.group(3)), int(m.group(4)), lab(k), m.group(6), m.group(7))
            if new != l:
                n += 1
            out.append(new)
        else:
            out.append(l)
    if n:
        fix = "--fix-snapshots" in sys.argv
        if fix:
            save(f, "\n".join(out) + "\n")
        say("   %-34s %d 处天数与「%s 基准」不符%s" % (
            os.path.basename(f), n, base, "（已改写）" if (fix and APPLY) else "（归档只读，不动；加 --fix-snapshots 才改）"))

say("\n【⑤ 总览：三级词数 / 按日期表 / updated】")
cnt = {}
for sub in ["02-陌生", "01-不熟悉", "00-已掌握"]:
    cnt[sub] = sum(1 for f in glob.glob(os.path.join(SH, sub, "*.md"))
                   for l in io.open(f, encoding="utf-8").read().splitlines() if ROW.match(l))
t = io.open(CETO, encoding="utf-8").read()
t2 = re.sub(r"现：陌生 \*\*\d+\*\* ／ 不熟悉 \*\*\d+\*\* ／ 已掌握 \*\*\d+\*\*",
            "现：陌生 **%d** ／ 不熟悉 **%d** ／ 已掌握 **%d**" % (cnt["02-陌生"], cnt["01-不熟悉"], cnt["00-已掌握"]), t)
if t2 != t:
    save(CETO, t2); say("   四级总览词数 → 陌生 %d／不熟悉 %d／已掌握 %d" % (cnt["02-陌生"], cnt["01-不熟悉"], cnt["00-已掌握"]))
else:
    say("   四级总览词数已是最新（%d/%d/%d）" % (cnt["02-陌生"], cnt["01-不熟悉"], cnt["00-已掌握"]))

t = io.open(HWO, encoding="utf-8").read()
add = []
for f in sorted(glob.glob(os.path.join(SNAP, "*-作业清单.md"))):
    d = os.path.basename(f).replace("-作业清单.md", "")
    if "[[%s-作业清单]]" % d not in t and d != "2026-09-29-国庆":
        add.append(d)
if add:
    lines = t.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("| 2026-") and "作业清单]]" in l:
            last = i
    lines[last + 1:last + 1] = ["| %s | [[%s-作业清单]] |" % (d, d) for d in add]
    t2 = "\n".join(lines) + "\n"
    t2 = re.sub(r"^updated:\s*\d{4}-\d{2}-\d{2}$", "updated: " + TODAY.isoformat(), t2, count=1, flags=re.M)
    save(HWO, t2); say("   作业总览补登：%s" % ", ".join(add))
else:
    say("   作业总览按日期表无漏登")

# ---------- ⑥ 镜像 ----------
say("\n【⑥ 镜像：真身 → Obsidian】")
if APPLY:
    rc, out = run([PY, r"D:\Clearn\tools\merge_and_sync.py", "--apply", "--stamp", TODAY.isoformat()])
    for l in out.strip().splitlines():
        if "合计" in l or "复核" in l or "两侧一致" in l:
            say("   " + l.strip()[:120])
    rc2, out2 = run([PY, r"D:\Clearn\tools\merge_and_sync.py"])
    tail = [l for l in out2.splitlines() if "两侧一致" in l or "合计" in l]
    for l in tail[-1:]:
        say("   复验：" + l.strip()[:110])
else:
    rc, out = run([PY, r"D:\Clearn\tools\merge_and_sync.py"])
    for l in out.strip().splitlines():
        if "两侧一致" in l or "合计" in l or "差异" in l:
            say("   " + l.strip()[:120])

# ---------- ⑦ 索引 ----------
say("\n【⑦ 索引新鲜度】")
for lib, src in DBSRC.items():
    db = os.path.join(r"D:\rag\db", lib)
    if not (os.path.isdir(db) and os.path.isdir(src)):
        continue
    t_db = max((os.path.getmtime(os.path.join(dp, f)) for dp, dn, fn in os.walk(db) for f in fn), default=0)
    t_src = max((os.path.getmtime(os.path.join(dp, f)) for dp, dn, fn in os.walk(src) for f in fn if f.endswith(".md")), default=0)
    stale = t_src > t_db
    say("   %-5s %s（源 %s / 索引 %s）" % (lib, "⚠️ 需要重建" if stale else "✅ 不落后",
        datetime.datetime.fromtimestamp(t_src).strftime("%m-%d %H:%M"), datetime.datetime.fromtimestamp(t_db).strftime("%m-%d %H:%M")))
    if stale and REBUILD and APPLY:
        rc, out = run([PY, r"D:\rag\rag_server.py", "--build", lib, "--force"])
        ok = "完成" in out
        say("        重建%s：%s" % ("成功" if ok else "失败", out.strip().splitlines()[-1][:90] if out.strip() else ""))

say("\n" + "=" * 66)
say("本次写入文件 %d 个（作业池 ＋ 教务页）｜备份 %s" % (changed_files, BK if APPLY else "（预演未写）"))
os.makedirs(r"D:\Clearn\_diag", exist_ok=True)
io.open(r"D:\Clearn\_diag\syncflow.txt", "w", encoding="utf-8").write("\n".join(report) + "\n")
print("（已存 D:\\Clearn\\_diag\\syncflow.txt）")
