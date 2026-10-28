# -*- coding: utf-8 -*-
"""四级生词流转：陌生里带 # 的词 → 移到不熟悉（去掉 #）；不熟悉里带 # 的词 → 移到已掌握。
   ###（或 ###数字）= 进度标记，忽略。先备份再写。"""
import os, re, io, shutil, datetime

B = r"C:\Users\36578\Desktop\英语四级\四级备考\05-生词"
F_STRANGE = os.path.join(B, r"02-陌生\001-100.md")
F_UNFAM = os.path.join(B, r"01-不熟悉\001-100.md")
F_MASTER = os.path.join(B, r"00-已掌握\001-100.md")

BK = r"D:\backup\cet4-shengci-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
os.makedirs(BK, exist_ok=True)
for p in (F_STRANGE, F_UNFAM, F_MASTER):
    tag = os.path.basename(os.path.dirname(p))
    shutil.copy2(p, os.path.join(BK, tag + "_" + os.path.basename(p)))
print("备份 ->", BK)

ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
SEP = re.compile(r"^\|[\s\-:|]+\|$")
HEADER = ["#", "单词", "音标", "释义", "备注"]

def parse(path):
    head, rows = [], []
    for line in io.open(path, encoding="utf-8").read().splitlines():
        m = ROW.match(line)
        if m:
            rows.append([m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)])
        else:
            head.append(line)
    return head, rows

def marked(word):
    w = word.strip()
    if re.search(r"#{3,}", w):      # ### 进度标记，不是生词标记
        return False
    return w.endswith("#")

def strip_hash(word):
    return re.sub(r"#+\s*$", "", word).strip()

def render(head, rows):
    rows = [[str(i)] + r[1:] for i, r in enumerate(rows, 1)]
    width = [max(len(HEADER[i]), *(len(r[i]) for r in rows)) if rows else len(HEADER[i]) for i in range(5)]
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

h_s, r_s = parse(F_STRANGE)
h_u, r_u = parse(F_UNFAM)
h_m, r_m = parse(F_MASTER)

moved_a = [r for r in r_s if marked(r[1])]
moved_b = [r for r in r_u if marked(r[1])]
stay_s = [r for r in r_s if not marked(r[1])]
stay_u = [r for r in r_u if not marked(r[1])]
for r in moved_a + moved_b:
    r[1] = strip_hash(r[1])

def key(r):
    return re.sub(r"[*#\s]", "", r[1]).lower()

seen_u = {key(r) for r in stay_u}
add_u = [r for r in moved_a if key(r) not in seen_u]
for r in add_u:
    seen_u.add(key(r))
dup_u = [r for r in moved_a if key(r) not in {key(x) for x in add_u}]

seen_m = {key(r) for r in r_m}
add_m = [r for r in moved_b if key(r) not in seen_m]

new_s, new_u, new_m = stay_s, stay_u + add_u, r_m + add_m

print("\n陌生：原 %d → 移出 %d → 剩 %d" % (len(r_s), len(moved_a), len(new_s)))
print("  移出词（%d）：%s" % (len(moved_a), ", ".join(strip_hash(r[1]).strip("*") for r in moved_a)))
if dup_u:
    print("  ⚠️ 不熟悉里已有、跳过：", [strip_hash(r[1]) for r in dup_u])
print("不熟悉：原 %d → 加入 %d → 现 %d" % (len(r_u), len(add_u), len(new_u)))
print("已掌握：原 %d → 加入 %d → 现 %d" % (len(r_m), len(add_m), len(new_m)))

bad = [r[1] for r in new_s + new_u if not r[2].startswith("/")]
print("缺音标的行：", bad or "无")

io.open(F_STRANGE, "w", encoding="utf-8", newline="\n").write(render(h_s, new_s))
io.open(F_UNFAM, "w", encoding="utf-8", newline="\n").write(render(h_u, new_u))
if new_m or "\u5df2\u638c\u63e1" in io.open(F_MASTER, encoding="utf-8").read() or os.path.getsize(F_MASTER) > 0:
    io.open(F_MASTER, "w", encoding="utf-8", newline="\n").write(render(h_m, new_m))

print("\n--- 不熟悉（全篇前 22 行）---")
print("\n".join(io.open(F_UNFAM, encoding="utf-8").read().splitlines()[:22]))
print("\n--- 陌生（前 12 行）---")
print("\n".join(io.open(F_STRANGE, encoding="utf-8").read().splitlines()[:14]))
