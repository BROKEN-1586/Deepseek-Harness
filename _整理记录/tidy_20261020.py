"""教材 / 临时文件 结构整理（2026-10-20）
硬约束：
  1. 只移动 / 建目录，绝不修改、绝不删除任何文件；
  2. 移动前记录 before 文件数 + 总字节，移动后必须完全一致，否则报错退出；
  3. 生成移动清单（旧路径 -> 新路径）便于回滚。
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DESK = Path(r"C:\Users\36578\Desktop")
LOG = Path(r"D:\Clearn\_整理记录\移动清单-20261020.md")

T = DESK / "教材"
M = DESK / "临时文件"

PAIRS = [
    # ---------- 教材：01-教材（整目录搬，按科目分组） ----------
    (T / "工科数学分析基础（第三版）", T / "01-教材" / "工科数学分析"),
    (T / "工科数学分析基础（第四版）", T / "01-教材" / "工科数学分析"),
    (T / "数学分析教材", T / "01-教材" / "工科数学分析"),
    (T / "线代教材（第三版）与习题", T / "01-教材" / "线性代数"),
    (T / "离散数学", T / "01-教材" / "数学其他"),
    (T / "数据结构", T / "01-教材" / "计算机"),
    (T / "《深入理解计算机系统》教材", T / "01-教材" / "计算机"),
    (T / "博弈论教材", T / "01-教材" / "博弈论"),
    # ---------- 教材：02-课程资料 ----------
    (T / "通用学术英语", T / "02-课程资料"),
    (T / "通用学术英语课程资料", T / "02-课程资料"),
    (T / "人工智能基础与应用", T / "02-课程资料"),
    # ---------- 教材：03-其他资料 ----------
    (T / "朋辅班会", T / "03-其他资料"),
    # ---------- 教材：99-旧版与空目录 ----------
    (T / "线代课件（旧版）", T / "99-旧版与空目录"),
    (T / "C语言程序设计 第5版", T / "99-旧版与空目录"),
    # ---------- 临时文件 ----------
    (M / "课程资料", M / "01-课程资料"),
    (M / "人工智能作业", M / "02-作业" / "人工智能作业"),
    (M / "竞赛通知", M / "03-竞赛与活动"),
    (M / "职业规划大赛", M / "03-竞赛与活动"),
    (M / "国庆剪辑", M / "03-竞赛与活动"),
    (M / "剪映-1.zip", M / "03-竞赛与活动"),
    (M / "第一次培训.pptx", M / "03-竞赛与活动"),
    (M / "证件", M / "04-个人资料"),
    (M / "个人事务", M / "04-个人资料"),
]

NEW_DIRS = [
    T / "01-教材" / "工科数学分析",
    T / "01-教材" / "线性代数",
    T / "01-教材" / "数学其他",
    T / "01-教材" / "计算机",
    T / "01-教材" / "博弈论",
    T / "02-课程资料",
    T / "03-其他资料",
    T / "99-旧版与空目录",
    M / "01-课程资料",
    M / "02-作业" / "人工智能作业",
    M / "03-竞赛与活动",
    M / "04-个人资料",
]


def stat_tree(p: Path):
    files = [f for f in p.rglob("*") if f.is_file()]
    return len(files), sum(f.stat().st_size for f in files)


def main():
    before = {str(r): stat_tree(r) for r in (T, M)}
    print("BEFORE:", before)

    for d in NEW_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    lines = ["# 移动清单 2026-10-20", "", "> 只做移动，未修改 / 未删除任何文件。回滚 = 反向移动。", ""]
    done = 0
    skipped = []
    for src, parent in PAIRS:
        dst = parent / src.name
        if not src.exists():
            skipped.append(f"{src}  （源不存在，跳过）")
            continue
        if dst.exists():
            skipped.append(f"{src} -> {dst}  （目标已存在，跳过，未覆盖）")
            continue
        parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        done += 1
        lines.append(f"- `{src}` → `{dst}`")

    after = {str(r): stat_tree(r) for r in (T, M)}
    print("AFTER :", after)

    lines += ["", f"共移动 {done} 项。", ""]
    if skipped:
        lines += ["## 跳过", ""] + [f"- {s}" for s in skipped] + [""]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(lines), encoding="utf-8")

    print("文件数 / 总字节 对比：")
    ok = True
    for k in before:
        b, a = before[k], after[k]
        same = b == a
        ok = ok and same
        print(f"  {k}: {b} -> {a}  {'OK' if same else '!!! 不一致'}")
    if not ok:
        print("🔴 统计不一致，请立刻检查（清单见日志）")
        sys.exit(2)
    print(f"✅ 移动完成 {done} 项，文件总数与总大小未变；清单：{LOG}")


if __name__ == "__main__":
    main()
