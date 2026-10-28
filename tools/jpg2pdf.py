#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
jpg2pdf.py —— 把一堆图片按「标号从小到大」合成一个 PDF（A4 比例、不裁切、不重压缩）

用法:
  python jpg2pdf.py <图片目录> [-o 输出.pdf] [--recurse] [--page a4|fit] [--dpi 200]

排序规则:
  从文件名里抽数字（优先 f"{主名数字}_{后缀数字}" 自然序，如 IMG_20261026_121407 → 20261026121407），
  没有数字的退回自然序字符串比较。可用 --key 指定正则从文件名抽取排序键。

页面:
  --page a4  (默认) 每页等比缩放进 A4（595x842pt），长边贴边，短边留白居中，不裁切内容;
  --page fit 页面尺寸 = 图片本身尺寸等比缩到长边 842pt（不补白）。

实现: 用 PyMuPDF 直接把 JPEG 原始数据塞进 PDF（无二次编码），仅当 EXIF 有旋转时才预旋一次。
"""
import argparse
import io
import os
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("需要 PyMuPDF: pip install pymupdf")
from PIL import Image, ImageOps

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
A4_W, A4_H = 595.0, 842.0


def sort_key(path, pattern=None):
    name = os.path.basename(path)
    if pattern:
        m = re.search(pattern, name)
        return (0, m.group(1), name) if m else (1, "", name)
    nums = re.findall(r"\d+", os.path.splitext(name)[0])
    if nums:
        return (0, "_".join(n.zfill(18) for n in nums), name)
    return (1, "", name)


def collect(src, recurse):
    if os.path.isfile(src):
        return [src]
    out = []
    for root, dirs, files in os.walk(src):
        for f in files:
            if os.path.splitext(f)[1].lower() in IMG_EXT:
                out.append(os.path.join(root, f))
        if not recurse:
            break
    return out


def load_bytes(path):
    """返回 (jpeg_bytes, w, h)；必要时按 EXIF 摆正。"""
    with Image.open(path) as im:
        im.load()
        orientation = im.getexif().get(0x0112, 1) if hasattr(im, "getexif") else 1
        need_rotate = orientation not in (None, 1)
        if not need_rotate and im.format == "JPEG" and im.mode in ("RGB", "L"):
            with open(path, "rb") as fh:
                return fh.read(), im.width, im.height
        fixed = ImageOps.exif_transpose(im).convert("RGB")
        buf = io.BytesIO()
        fixed.save(buf, format="JPEG", quality=95, subsampling=0)
        return buf.getvalue(), fixed.width, fixed.height


def build(src, out, recurse=False, pattern=None, page="a4", dpi=200):
    files = collect(src, recurse)
    if not files:
        sys.exit("没找到图片: %s" % src)
    files.sort(key=lambda p: sort_key(p, pattern))

    doc = fitz.open()
    for i, p in enumerate(files, 1):
        data, w, h = load_bytes(p)
        if page == "fit":
            s = (A4_H if max(w, h) == h else A4_W) / max(w, h)
            pw, ph = w * s, h * s
            rect = fitz.Rect(0, 0, pw, ph)
        else:
            s = min(A4_W / w, A4_H / h)
            pw, ph = w * s, h * s
            rect = fitz.Rect((A4_W - pw) / 2, (A4_H - ph) / 2, (A4_W + pw) / 2, (A4_H + ph) / 2)
            pw, ph = A4_W, A4_H
        pg = doc.new_page(width=pw, height=ph)
        pg.insert_image(rect, stream=data)
        print("  [%2d] %s  (%dx%d)" % (i, os.path.basename(p), w, h))

    doc.set_metadata({"title": os.path.splitext(os.path.basename(out))[0], "producer": "jpg2pdf.py"})
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    size = os.path.getsize(out)
    print("\n共 %d 页 -> %s  (%.2f MB)" % (len(files), out, size / 1048576))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--recurse", action="store_true")
    ap.add_argument("--key", help="从文件名抽取排序键的正则（group(1)）")
    ap.add_argument("--page", choices=["a4", "fit"], default="a4")
    a = ap.parse_args()
    src = os.path.abspath(a.src)
    out = a.out or (os.path.join(src if os.path.isdir(src) else os.path.dirname(src),
                                 os.path.basename(os.path.normpath(src)) + ".pdf"))
    build(src, os.path.abspath(out), a.recurse, a.key, a.page)


if __name__ == "__main__":
    main()
