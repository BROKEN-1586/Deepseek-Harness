"""把代码/文档里对「教材\\」的旧引用改成新结构（2026-10-20 第二轮整理后）。"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

MAP = [
    # 作业（脚本硬编码 + recipe）
    (r"教材\作业清单", r"课程\作业\作业清单"),
    (r"教材\作业每日截图", r"课程\作业\作业每日截图"),
    # 课件
    (r"教材\高数课件（含作业）", r"课程\课件\高数课件（含作业）"),
    (r"教材\线性代数课件（含作业）", r"课程\课件\线性代数课件（含作业）"),
    (r"教材\C语言课件(含作业）", r"课程\课件\C语言课件(含作业）"),
    (r"教材\博弈论课件（浙大版）", r"课程\课件\博弈论课件（浙大版）"),
    (r"教材\*课件（含作业）", r"课程\课件\*课件（含作业）"),
    (r"教材\02-课程资料\人工智能基础与应用", r"课程\课件\人工智能基础与应用"),
    # 课程资料
    (r"教材\02-课程资料\通用学术英语课程资料", r"课程\资料\通用学术英语课程资料"),
    (r"教材\02-课程资料\通用学术英语\生词", r"课程\资料\通用学术英语\生词"),
    (r"教材\02-课程资料\通用学术英语\课堂笔记", r"课程\资料\通用学术英语\课堂笔记"),
    (r"教材\02-课程资料\通用学术英语", r"教材\通用学术英语"),
    (r"教材\03-其他资料\朋辅班会", r"课程\资料\朋辅班会"),
    # 教材本体上移一层
    ("教材\\01-教材\\", "教材\\"),
    (r"教材\01-教材", r"教材"),
]

FILES = [
    r"D:\Clearn\tools\merge_and_sync.py",
    r"D:\Clearn\tools\tasks_syntax.py",
    r"D:\Clearn\tools\stamp_backfill.py",
    r"D:\Clearn\.goose\recipes\read-the-night.yaml",
    r"D:\Clearn\.goose\recipes\note-pipeline.yaml",
    r"D:\Clearn\DEEPCODE.md",
]

for f in FILES:
    p = Path(f)
    s = p.read_text(encoding="utf-8")
    total = 0
    detail = []
    for old, new in MAP:
        c = s.count(old)
        if c:
            s = s.replace(old, new)
            total += c
            detail.append(f"{old} -> {new} ({c})")
    if total:
        p.write_text(s, encoding="utf-8")
        print(f"[改] {p.name}: {total} 处")
        for d in detail:
            print("     " + d)
    else:
        print(f"[跳过] {p.name}: 无匹配")
