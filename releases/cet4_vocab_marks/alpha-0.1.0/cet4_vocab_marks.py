# -*- coding: utf-8 -*-
"""把 01-词汇 核心词汇里的 #/## 标记汇总进 05-生词 三态表（# → 不熟悉，## → 陌生，释义里的标记按「义项不熟」入不熟悉）
用法: python _vocab_marks.py [范围文件关键词] [--apply]
"""
import io, os, re, sys, shutil, datetime

VOC = r"C:\Users\36578\Desktop\英语四级\四级备考\01-词汇"
SHENG = r"C:\Users\36578\Desktop\英语四级\四级备考\05-生词"
APPLY = "--apply" in sys.argv
KW = next((a for a in sys.argv[1:] if not a.startswith("--")), "201-400")

ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")

def marks_in(cell):
    """返回 (词面, 标记)：词面末尾 ## = 陌生(2)、单个 # = 不熟悉(1)、词中间/带注释的 # = 义项级"""
    c = cell.strip()
    if c.endswith("##"):
        return c[:-2].strip(), 2
    if c.endswith("#"):
        return c[:-1].strip(), 1
    if "#" in c:
        return c, ("inline",)
    return c, None

rows_out = []
for f in sorted(os.listdir(VOC)):
    if (KW not in ("all", "*") and KW not in f) or not f.endswith(".md"):
        continue
    for line in io.open(os.path.join(VOC, f), encoding="utf-8").read().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        no, word, ipa, mean, extra = m.groups()
        if no.isdigit() and int(no) < 100:      # 表头行
            continue
        w, mk = marks_in(word)
        mk_mean = None
        if mk is None:                          # 词面没标记 → 看释义里有没有
            if re.search(r"#", mean):
                mk_mean = mean
                mk = ("inline",)
        if mk is None:
            continue
        clean_word = re.sub(r"\*+", "", w).strip()
        rows_out.append({"no": no, "word": clean_word, "ipa": ipa,
                         "mean": re.sub(r"#+", "", mean).strip(),
                         "note": "", "mark": mk, "src": f})

fam = [r for r in rows_out if r["mark"] == 1]
strn = [r for r in rows_out if r["mark"] == 2]
inln = [r for r in rows_out if r["mark"] == ("inline",)]
for r in inln:
    # 释义里带 # 的：抓出紧挨 # 的义项作为备注
    m = re.search(r"([^；;，,。]{0,12}?)#", r["mean"] + "#")
    r["note"] = "义项不熟：" + (m.group(1).strip() if m else r["mean"][:12])
    if r["mark"] == ("inline",):
        pass

print("来源 %s：命中 %d 行 → 不熟悉(词中标 #) %d｜陌生(##) %d｜释义内标记 %d"
      % (KW, len(rows_out), len(fam), len(strn), len(inln)))
print("\n不熟悉候选：", ", ".join(r["word"] for r in fam + inln))
print("\n陌生候选：", ", ".join(r["word"] for r in strn))
if not APPLY:
    print("\n[预演] 加 --apply 才写入")
    sys.exit(0)

BK = r"D:\backup\cet4-marks-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
os.makedirs(BK, exist_ok=True)

def load(path):
    head, rows = [], []
    for line in io.open(path, encoding="utf-8").read().splitlines():
        m = ROW.match(line)
        if m:
            rows.append([m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)])
        else:
            head.append(line)
    return head, rows

HEADER = ["#", "单词", "音标", "释义", "备注"]
SEP = re.compile(r"^\|[\s\-:|]+\|$")

def render(head, rows):
    rows = [[str(i)] + r[1:] for i, r in enumerate(rows, 1)]
    width = [max([len(HEADER[i])] + [len(r[i]) for r in rows]) for i in range(5)]
    out = []
    for line in head:
        s = line.strip()
        if s.startswith("| #"):
            out.append("| " + " | ".join(HEADER[i].ljust(width[i]) for i in range(5)) + " |")
            out.append("| " + " | ".join("-" * width[i] for i in range(5)) + " |")
        elif SEP.match(s) or ROW.match(line):
            continue
        else:
            out.append(line)
    for r in rows:
        out.append("| " + " | ".join(r[i].ljust(width[i]) for i in range(5)) + " |")
    return "\n".join(out).rstrip("\n") + "\n"

def key(s):
    return re.sub(r"[*#\s]", "", s).lower()

def push(target_dir, incoming, label):
    """把 incoming 追加进 target_dir 的当前篇；超过 100 就开下一篇"""
    files = sorted(f for f in os.listdir(target_dir) if f.endswith(".md"))
    cur = os.path.join(target_dir, files[-1])
    head, rows = load(cur)
    have = {key(r[1]) for r in rows}
    added = []
    for r in incoming:
        if key(r["word"]) in have:
            continue
        rows.append(["0", r["word"], r["ipa"], r["mean"], r["note"]])
        have.add(key(r["word"]))
        added.append(r["word"])
    # 超 100 拆篇
    chunks = [rows[i:i + 100] for i in range(0, len(rows), 100)]
    for idx, ch in enumerate(chunks, 1):
        name = "%03d-%03d.md" % ((idx - 1) * 100 + 1, idx * 100)
        p = os.path.join(target_dir, name)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(BK, os.path.basename(target_dir) + "_" + name))
        io.open(p, "w", encoding="utf-8", newline="\n").write(render(head, ch))
    print("%s：原有 %d → 新增 %d → 现 %d 词（%d 篇）" % (label, len(rows) - len(added), len(added), len(rows), len(chunks)))
    return added

a1 = push(os.path.join(SHENG, "01-不熟悉"), fam + inln, "不熟悉")
a2 = push(os.path.join(SHENG, "02-陌生"), strn, "陌生")
print("\n备份:", BK)
