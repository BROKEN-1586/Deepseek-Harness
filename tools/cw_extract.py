# -*- coding: utf-8 -*-
"""课件正文抽取（PDF 用 blocks 合并，PPTX 按 slide 合并），存到 _diag\\courseware 并打印摘要"""
import os, re, zipfile, sys

OUT = r"D:\Clearn\_diag\courseware"
os.makedirs(OUT, exist_ok=True)

def clean_pdf(path, smooth=6):
    import pymupdf
    d = pymupdf.open(path)
    pages = []
    for i in range(d.page_count):
        blocks = d[i].get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1] / smooth), b[0]))
        frag = [re.sub(r"\s+", " ", b[4]).strip() for b in blocks]
        frag = [f for f in frag if len(f) > 1]
        pages.append((i + 1, " ⟂ ".join(frag)))
    return d.page_count, pages

def clean_pptx(path):
    z = zipfile.ZipFile(path)
    names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    names.sort(key=lambda n: int(re.search(r"(\d+)", os.path.basename(n)).group(1)))
    out = []
    for n in names:
        xml = z.read(n).decode("utf-8", "ignore")
        txt = [t.strip() for t in re.findall(r"<a:t>(.*?)</a:t>", xml) if t.strip()]
        out.append((os.path.basename(n), " ".join(txt)))
    return len(names), out

def dump(path, tag, show_chars=200000, page_filter=None):
    print("=" * 30, tag, os.path.basename(path))
    if path.lower().endswith(".pdf"):
        n, pages = clean_pdf(path)
        lines = ["=== 第 %d 页 ===\n%s" % (p, t) for p, t in pages]
    else:
        n, pages = clean_pptx(path)
        lines = ["=== %s ===\n%s" % (p, t) for p, t in pages]
    body = "\n\n".join(lines)
    fp = os.path.join(OUT, tag + ".txt")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(body)
    print("段落数 %d，共 %d 字符 -> %s" % (len(pages), len(body), fp))
    print(body[:show_chars])
    return fp

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    tasks = {
        "23": (r"C:\Users\36578\Desktop\课程\01-课件\工科数学分析\2026-10-21\2.3  交互式课件-微分-有笔记.pdf", "sd-2.3"),
        "24": (r"C:\Users\36578\Desktop\课程\01-课件\工科数学分析\2026-10-23\2.4 微分中值定理及其应用-有笔记1.pdf", "sd-2.4"),
        "33": (r"C:\Users\36578\Desktop\课程\01-课件\线性代数\2026-10-23\3.3节.pptx", "ld-3.3"),
        "c6": (r"C:\Users\36578\Desktop\课程\01-课件\C语言程序设计\2026-10-22\第6章.pptx", "c-ch6"),
    }
    keys = list(tasks) if which == "all" else [which]
    for k in keys:
        p, tag = tasks[k]
        if not os.path.exists(p):
            print("缺失:", p)
            continue
        dump(p, tag, show_chars=(0 if which == "all" else 200000))
