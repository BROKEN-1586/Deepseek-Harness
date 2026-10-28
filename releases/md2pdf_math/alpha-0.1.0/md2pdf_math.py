# -*- coding: utf-8 -*-
"""兼容入口（2026-10-10 起）：真正的实现在 `md2pdf.py`，本文件只做转发。

保留原因：数学笔记那批 PDF 一直用这个文件名跑，留着方便老命令照抄。
**新脚本请直接 import / 调用 `md2pdf.py`。**

默认版式：A4 纵向、段首不缩进（适合公式与图多的数学笔记）。
要别版式照抄 md2pdf.py 的参数：

    python md2pdf_math.py <src.md> <out.pdf> [标题] [--landscape] [--indent]
    python md2pdf_math.py --batch <manifest.txt> [--landscape] [--indent]

（简言之：`md2pdf_math.py` = `md2pdf.py` + 纵向/不缩进的默认值。）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True      # 别在 tools\ 下留 __pycache__

from md2pdf import main, to_pdf, merge_pdfs  # noqa: F401  转发/复用

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
