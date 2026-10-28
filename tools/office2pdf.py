"""office2pdf.py — 用本机 WPS 的 COM 接口把 docx / pptx / xlsx 转成 PDF，可选再渲染成 PNG。

为什么走 WPS 而不是 LibreOffice：
  · 本机已装 WPS 教育版（`Kwps.Application` / `Kwpp.Application` / `KET.Application` 三个 COM 都已注册），
    不用再装 300 MB 的 LibreOffice；
  · 中文排版、表格边框、字体替换的保真度比 LibreOffice 更贴 Office 本身。

⚠️ 唯一硬限制：**进程外 COM 在 DSH 沙箱（低完整性）里起不来**，报 `0x80080005 服务器运行失败`。
   → 必须在沙箱外跑，或交给 goose 调用（它没有沙箱）。

依赖：**系统 Python**（`C:\\Users\\36578\\AppData\\Local\\Programs\\Python\\Python314\\python.exe`），
      它才有 `win32com`（pywin32）与 `fitz`（PyMuPDF）。DSH 自带运行时没有这两个。

用法：
  python D:\\Clearn\\tools\\office2pdf.py 稿子.docx                  # 同目录同名 .pdf
  python D:\\Clearn\\tools\\office2pdf.py 稿子.docx --out D:\\x.pdf --png 150
  python D:\\Clearn\\tools\\office2pdf.py 稿子.pptx --png 150 --pages 1-3
  python D:\\Clearn\\tools\\office2pdf.py a.docx b.xlsx --png 120     # 批量

退出码：0 全部成功；2 有文件失败；3 参数问题。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

WORD_EXT = {".docx", ".doc", ".rtf", ".wps"}
PPT_EXT = {".pptx", ".ppt", ".dps"}
XLS_EXT = {".xlsx", ".xls", ".et", ".csv"}

WD_EXPORT_PDF = 17      # wdExportFormatPDF
PP_SAVE_AS_PDF = 32     # ppSaveAsPDF
XL_TYPE_PDF = 0         # xlTypePDF


def _need(name: str):
    try:
        return __import__(name)
    except ImportError:
        raise SystemExit(f"[x] 缺依赖 `{name}` —— 这个脚本要用系统 Python 跑（不是 DSH 自带的运行时）")


def convert(src: Path, out: Path) -> tuple[bool, str]:
    import win32com.client as win32

    ext = src.suffix.lower()
    started = time.time()
    app = None
    try:
        if ext in WORD_EXT:
            app = win32.DispatchEx("Kwps.Application")
            app.Visible = False
            try:
                app.DisplayAlerts = 0
            except Exception:
                pass
            doc = app.Documents.Open(str(src))
            doc.ExportAsFixedFormat(str(out), WD_EXPORT_PDF)
            doc.Close(0)
        elif ext in PPT_EXT:
            app = win32.DispatchEx("Kwpp.Application")
            pres = app.Presentations.Open(str(src), ReadOnly=True, WithWindow=False)
            pres.SaveAs(str(out), PP_SAVE_AS_PDF)
            pres.Close()
        elif ext in XLS_EXT:
            app = win32.DispatchEx("KET.Application")
            app.Visible = False
            try:
                app.DisplayAlerts = False
            except Exception:
                pass
            wb = app.Workbooks.Open(str(src), ReadOnly=True)
            wb.ExportAsFixedFormat(XL_TYPE_PDF, str(out))
            wb.Close(False)
        else:
            return False, f"不支持的扩展名 {ext}"
    except Exception as exc:  # COM 失败通常是这一个
        hint = ""
        msg = str(exc)
        if "0x80080005" in msg or "-2146959355" in msg or "运行失败" in msg:
            hint = "（低完整性沙箱里起不动 COM —— 请在沙箱外或交给 goose 跑）"
        return False, f"{type(exc).__name__}: {msg[:200]}{hint}"
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
    if not out.exists() or out.stat().st_size == 0:
        return False, "COM 返回成功但没生成 PDF"
    return True, f"{out.stat().st_size / 1024:.0f} KB · {time.time() - started:.1f}s"


def render(pdf: Path, dpi: int, pages: str | None, out_dir: Path) -> list[Path]:
    fitz = _need("fitz")
    doc = fitz.open(str(pdf))
    wanted = list(range(doc.page_count))
    if pages:
        wanted = []
        for part in pages.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                wanted.extend(range(int(a) - 1, min(int(b), doc.page_count)))
            elif part:
                wanted.append(int(part) - 1)
        wanted = [i for i in wanted if 0 <= i < doc.page_count]
    outs = []
    for i in wanted:
        pix = doc[i].get_pixmap(dpi=dpi)
        p = out_dir / f"{pdf.stem}.p{i + 1}.png"
        pix.save(str(p))
        outs.append(p)
    print(f"    pages={doc.page_count} 渲染 {len(outs)} 张 → {outs[0].parent if outs else '-'}")
    return outs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="office2pdf.py")
    ap.add_argument("inputs", nargs="+", help="docx / pptx / xlsx 路径")
    ap.add_argument("--out", help="输出 PDF（单文件时可用）")
    ap.add_argument("--png", type=int, metavar="DPI", help="转完再渲染 PNG，例：150")
    ap.add_argument("--pages", help="只渲染这些页，例：1-3,5（默认全部）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的输出")
    a = ap.parse_args(argv)

    if a.out and len(a.inputs) > 1:
        print("[x] --out 只能配单个输入")
        return 3

    rc = 0
    for raw in a.inputs:
        src = Path(raw).expanduser().resolve()
        if not src.is_file():
            print(f"[x] 不存在：{src}")
            rc = 2
            continue
        out = Path(a.out).expanduser().resolve() if a.out else src.with_suffix(".pdf")
        if out.exists() and not a.force:
            print(f"[skip] {out.name} 已存在（要覆盖加 --force）")
        else:
            ok, note = convert(src, out)
            print(f"[{'ok' if ok else 'x'}] {src.name} → {out.name} · {note}")
            if not ok:
                rc = 2
                continue
        if a.png:
            try:
                render(out, a.png, a.pages, out.parent)
            except Exception as exc:
                print(f"[x] 渲染失败：{type(exc).__name__}: {exc}")
                rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
