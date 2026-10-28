"""第二轮整理：教材库只留教材；课件 / 作业 / 课程资料分出去；重要文件归拢。
硬约束：只移动 + 建目录；不修改、不删除任何**文件**（空目录可删）。
校验：移动前后 Desktop 四个相关目录的「文件总数 + 总字节」必须一致。
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

D = Path(r"C:\Users\36578\Desktop")
T = D / "教材"
C = D / "课程"
G = D / "重要文件"
M = D / "临时文件"
LOG = Path(r"D:\Clearn\_整理记录\移动清单2-20261020.md")

PAIRS = [
    # ---- 教材\01-教材 上移一层 ----
    (T / "01-教材" / "工科数学分析", T),
    (T / "01-教材" / "线性代数", T),
    (T / "01-教材" / "计算机", T),
    (T / "01-教材" / "数学其他", T),
    (T / "01-教材" / "博弈论", T),
    # ---- 课件 ----
    (T / "高数课件（含作业）", C / "课件"),
    (T / "线性代数课件（含作业）", C / "课件"),
    (T / "C语言课件(含作业）", C / "课件"),
    (T / "博弈论课件（浙大版）", C / "课件"),
    (T / "99-旧版与空目录" / "线代课件（旧版）", C / "课件"),
    (T / "02-课程资料" / "人工智能基础与应用", C / "课件"),
    # ---- 课程资料 ----
    (T / "02-课程资料" / "通用学术英语" / "生词", C / "资料" / "通用学术英语"),
    (T / "02-课程资料" / "通用学术英语" / "课堂笔记", C / "资料" / "通用学术英语"),
    (T / "02-课程资料" / "通用学术英语课程资料", C / "资料"),
    (T / "03-其他资料" / "朋辅班会", C / "资料"),
    # ---- 作业 ----
    (T / "作业清单", C / "作业"),
    (T / "作业每日截图", C / "作业"),
    # ---- 重要文件 ----
    (G / "教务通知", G / "01-教务与证明"),
    (G / "升国旗仪式的集体活动参与证明.pdf", G / "01-教务与证明"),
    (M / "04-个人资料" / "证件", G / "02-证件"),
    (M / "04-个人资料" / "个人事务", G / "03-个人事务"),
]

NEW_DIRS = [
    T / "通用学术英语",
    C / "课件",
    C / "资料" / "通用学术英语",
    C / "作业",
    G / "01-教务与证明",
]

SCAN_ROOTS = [T, C, G, M]


def stat_tree(roots):
    files = []
    for r in roots:
        if r.exists():
            files += [f for f in r.rglob("*") if f.is_file()]
    return len(files), sum(f.stat().st_size for f in files)


def main():
    before = stat_tree(SCAN_ROOTS)
    print("BEFORE:", before)

    for d in NEW_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    lines = ["# 移动清单（第二轮）2026-10-20", "",
             "> 只做移动，未修改 / 未删除任何文件。回滚 = 反向移动。", ""]
    done, skipped = 0, []
    for src, parent in PAIRS:
        dst = parent / src.name
        if not src.exists():
            skipped.append(f"{src}（源不存在）")
            continue
        if dst.exists():
            skipped.append(f"{src} -> {dst}（目标已存在，跳过）")
            continue
        parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        done += 1
        lines.append(f"- `{src}` → `{dst}`")

    # 电子课本：从课程资料里抽出到 教材\通用学术英语（单文件移动）
    ebook = T / "02-课程资料" / "通用学术英语" / "通用学术英语_电子课本.pdf"
    if ebook.exists():
        target = T / "通用学术英语" / ebook.name
        if not target.exists():
            shutil.move(str(ebook), str(target))
            done += 1
            lines.append(f"- `{ebook}` → `{target}`")

    # 清理"移动后变空"的目录（只删空目录，不删文件）
    empties = [
        T / "01-教材", T / "02-课程资料" / "通用学术英语", T / "02-课程资料",
        T / "03-其他资料", T / "99-旧版与空目录" / "C语言程序设计 第5版",
        T / "99-旧版与空目录", M / "04-个人资料",
    ]
    removed = []
    for e in empties:
        if e.exists() and not any(e.rglob("*")):
            e.rmdir()
            removed.append(str(e))

    after = stat_tree(SCAN_ROOTS)
    print("AFTER :", after)

    lines += ["", f"共移动 {done} 项。", ""]
    if removed:
        lines += ["## 删掉的空目录（无文件）", ""] + [f"- `{x}`" for x in removed] + [""]
    if skipped:
        lines += ["## 跳过", ""] + [f"- {s}" for s in skipped] + [""]
    LOG.write_text("\n".join(lines), encoding="utf-8")

    ok = before == after
    print(f"文件数/字节: {before} -> {after}  {'OK' if ok else '!!! 不一致'}")
    if not ok:
        sys.exit(2)
    print(f"✅ 完成 {done} 项；清单：{LOG}")


if __name__ == "__main__":
    main()
