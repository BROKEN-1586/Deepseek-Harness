# -*- coding: utf-8 -*-
"""hw_from_courseware.py —— 从课件首页抓「作业页」→ 候选条目（默认只打印，核对后才写）

用法：
  python hw_from_courseware.py --date 2026-10-23           # 扫当天所有科目的课件
  python hw_from_courseware.py --file "<课件.pdf>"          # 指定文件
  python hw_from_courseware.py --date ... --apply          # 核对通过后写入作业池（截止标「待确认」）

规则（DEEPCODE「课件的分工」）：课件**前几页**的作业页 → 作业池；正文 → 笔记。**不抄题目、只记题号**。
写池前会按题号去重；写入的条目一律带 `📅 待确认`→不带日期，截止写「待确认」。
"""
import os, re, io, sys, glob, shutil, datetime, zipfile

APPLY = "--apply" in sys.argv
DATE = None
FILE = None
if "--date" in sys.argv:
    DATE = sys.argv[sys.argv.index("--date") + 1]
if "--file" in sys.argv:
    FILE = sys.argv[sys.argv.index("--file") + 1]
if not (DATE or FILE):
    DATE = datetime.date.today().isoformat()

KJ = r"C:\Users\36578\Desktop\课程\01-课件"
POOL = r"C:\Users\36578\Desktop\课程\02-作业\作业清单\01-按科目"
KW = ("作业", "习题", "练习", "上交", "提交", "homework", "exercise")

def pdf_pages(path, n=3):
    import pymupdf
    d = pymupdf.open(path)
    out = []
    for i in range(min(n, d.page_count)):
        out.append("\n".join(l.strip() for l in d[i].get_text("text").splitlines() if l.strip()))
    return d.page_count, out

def pptx_pages(path, n=3):
    z = zipfile.ZipFile(path)
    names = [x for x in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", x)]
    names.sort(key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1)))
    out = []
    for x in names[:n]:
        xml = z.read(x).decode("utf-8", "ignore")
        out.append(" ".join(t.strip() for t in re.findall(r"<a:t>(.*?)</a:t>", xml) if t.strip()))
    return len(names), out

def guess_subject(path):
    txt = (os.path.basename(path) + os.path.dirname(path)).lower()
    for k, v in [("数学分析", "工科数学分析"), ("高数", "工科数学分析"), ("线性代数", "线性代数"),
                 ("线代", "线性代数"), ("c语言", "C语言程序设计"), ("人工智能", "人工智能基础与应用"),
                 ("博弈", "博弈论"), ("素养", "大学生思想文化素养"), ("英语", "通用学术英语")]:
        if k in txt:
            return v
    return "待确认科目"

targets = []
if FILE:
    targets = [FILE]
else:
    for sub in sorted(os.listdir(KJ)) if os.path.isdir(KJ) else []:
        d = os.path.join(KJ, sub, DATE)
        if os.path.isdir(d):
            targets += [os.path.join(d, f) for f in sorted(os.listdir(d))
                        if f.lower().endswith((".pdf", ".pptx"))]

print("扫描 %d 个课件（日期 %s）\n" % (len(targets), DATE))
found = []
for p in targets:
    try:
        pages = pdf_pages(p, 3) if p.lower().endswith(".pdf") else pptx_pages(p, 3)
    except Exception as e:
        print("  !! 读取失败 %s: %s" % (os.path.basename(p), e)); continue
    total, texts = pages
    hit = []
    for i, t in enumerate(texts, 1):
        for line in t.splitlines() if isinstance(t, str) else []:
            if any(k in line.lower() for k in KW) and len(line) > 3:
                hit.append((i, line.strip()))
    print("📄 %-50s（共 %d 页）%s" % (os.path.basename(p)[:50], total, "— 命中作业页" if hit else ""))
    for i, line in hit[:4]:
        print("     第%d页：%s" % (i, line[:110]))
    if hit:
        found.append({"file": p, "subject": guess_subject(p), "hits": hit, "pages": total})

if not found:
    print("\n结论：本次没有抓到作业页 —— 可能当天课件确实没作业（C 语言理论课常见），或作业页在第 4 页之后（本工具只看前 3 页）。")
    sys.exit(0)

print("\n=== 候选条目（核对用）===")
for f in found:
    print("\n[%s] %s" % (f["subject"], os.path.basename(f["file"])))
    for i, line in f["hits"]:
        m = re.search(r"[Pp]\s*(\d{2,3})", line)
        nums = re.search(r"([\d,，、．.()（）\s]{6,})$", line)
        print("   第%d页 → 教材页 %s ｜ 题号片段：%s" % (i, m.group(1) if m else "未识别", (nums.group(1).strip() if nums else line)[:90]))

if not APPLY:
    print("\n[预演] 只打印，未写任何文件。核对无误后加 --apply 写入作业池（截止标「待确认」）。")
    sys.exit(0)

TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bk = os.path.join(r"D:\backup", "hw_from_cw-" + TS)
os.makedirs(bk, exist_ok=True)
today = datetime.date.today().isoformat()
written = 0
for f in found:
    pool = os.path.join(POOL, "%s-作业汇总.md" % f["subject"])
    if not os.path.exists(pool):
        print("  跳过（没有对应作业池）：", f["subject"]); continue
    t = io.open(pool, encoding="utf-8").read()
    key = os.path.basename(f["file"])[:18]
    if key in t:
        print("  跳过（池里已有该课件出处）：", key); continue
    line = f["hits"][0][1][:160]
    entry = ("\n- [ ] **%s 作业**（课件首页）：%s　`%s 第 %d 页`（待整理成标准题号）\n"
             "    - [ ] 完成\n    - [ ] 提交\n    - 截止：**待确认**\n") % (DATE, line, os.path.basename(f["file"]), f["hits"][0][0])
    shutil.copy2(pool, os.path.join(bk, os.path.basename(pool)))
    t2 = re.sub(r"^updated:\s*\d{4}-\d{2}-\d{2}$", "updated: " + today, t.rstrip("\n") + "\n" + entry, count=1, flags=re.M)
    io.open(pool, "w", encoding="utf-8", newline="\n").write(t2)
    written += 1
    print("  ✅ 写入 %s ← %s" % (f["subject"], key))
print("\n写入 %d 条；备份 %s" % (written, bk))
print("⚠️ 写入的是「原始样式的候选条目」，题号请人工整理成标准写法（本工具不猜题号）。")
