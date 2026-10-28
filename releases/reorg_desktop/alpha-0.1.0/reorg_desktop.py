# 注：2026-10-21 之后 `课程\\02-作业\\作业截图` 已改名 `作业来源`，本表的 dst 仍是旧名，仅作历史记录（勿再直接跑）。
# -*- coding: utf-8 -*-
"""
reorg_desktop.py —— 桌面「临时文件 / 教材 / 重要文件 / 课程」四区重构（2026-10-21 用户批准版）

设计原则
  1. 默认 dry-run：只打印计划，不动任何文件。
  2. --apply 才执行；执行前把四区完整清单（路径/大小/修改时间）写进 D:\\backup\\reorg-<ts>\\manifest.json。
  3. 任何目标已存在 → 该条跳过并报 CONFLICT，不覆盖、不合并。
  4. 只做「移动 / 改名 / 建目录」，**不删任何文件**；重复件、备份、构建产物统一收进 临时文件\\99-暂存\\。
  5. 移动完清理四区内的空目录（空目录本身也先列出来，--apply 时只删「本次移空」的）。

用法
  python reorg_desktop.py            # 预演
  python reorg_desktop.py --apply    # 执行
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

DESK = Path(r"C:\Users\36578\Desktop")
TMP = DESK / "临时文件"
BOOK = DESK / "教材"
DOC = DESK / "重要文件"
COURSE = DESK / "课程"
BACKUP_ROOT = Path(r"D:\backup")

STAGE = TMP / "99-暂存"           # 重复 / 旧备份 / 构建产物
STAGE_DUP = STAGE / "重复文件"
STAGE_BAK = STAGE / "旧备份"
STAGE_BUILD = STAGE / "构建产物"
INBOX = TMP / "00-待归档"
CONTEST = TMP / "01-竞赛与活动"

MOVES = []   # dict(kind='dir'|'file', src=Path, dst=Path, note=str)
MKDIRS = []
NEW_FILES = []  # (path, content)

def mv(src, dst, note=""):
    MOVES.append(dict(kind="dir" if src.is_dir() else "file", src=Path(src), dst=Path(dst), note=note))

def mkdir(p, note=""):
    MKDIRS.append(dict(path=Path(p), note=note))

# ---------------------------------------------------------------- 教材（全量重排）
BOOK_INUSE = BOOK / "00-在用"
BOOK_REF = BOOK / "01-参考"
book_map = [
    # 源（相对 教材\）                                          → 目标
    (r"博弈论\博弈论教材\GT_book.pdf", "00-在用\博弈论-GT_book.pdf"),
    (r"工科数学分析\工科数学分析基础（第三版）\工科数学分析基础 上 第3版.PDF", "00-在用\工科数学分析基础-上册-第3版.pdf"),
    (r"工科数学分析\工科数学分析基础（第三版）\工科数学分析基础_下_第3版.pdf", "00-在用\工科数学分析基础-下册-第3版.pdf"),
    (r"工科数学分析\工科数学分析基础（第三版）\工科数学分析基础-教辅（上）.pdf", "00-在用\工科数学分析基础-教辅-上册-第3版.pdf"),
    (r"工科数学分析\工科数学分析基础（第三版）\工科数学分析基础-教辅（下).pdf", "00-在用\工科数学分析基础-教辅-下册-第3版.pdf"),
    (r"工科数学分析\工科数学分析基础（第四版）\工科数学分析基础第四版上册.pdf", "00-在用\工科数学分析基础-上册-第4版.pdf"),
    (r"线性代数\线代教材（第三版）与习题\线性代数与解析几何  第3版_14610014.pdf", "00-在用\线性代数与解析几何-第3版.pdf"),
    (r"通用学术英语\通用学术英语_电子课本.pdf", "00-在用\通用学术英语-电子课本.pdf"),
    (r"工科数学分析\数学分析教材\数学分析(第二版) 上下册 陈纪修.pdf", "01-参考\数学分析-陈纪修-第二版.pdf"),
    (r"工科数学分析\数学分析教材\微积分学教程.第一卷.菲赫金哥尔茨.pdf", "01-参考\微积分学教程-第1卷-菲赫金哥尔茨.pdf"),
    (r"工科数学分析\数学分析教材\微积分学教程.第二卷.菲赫金哥尔茨.pdf", "01-参考\微积分学教程-第2卷-菲赫金哥尔茨.pdf"),
    (r"工科数学分析\数学分析教材\微积分学教程.第三卷.菲赫金哥尔茨.pdf", "01-参考\微积分学教程-第3卷-菲赫金哥尔茨.pdf"),
    (r"线性代数\线代教材（第三版）与习题\线性代数习题集【苏联】普罗斯库烈.pdf", "01-参考\线性代数习题集-普罗斯库烈.pdf"),
    (r"数学其他\离散数学\离散数学 [陈建明，曾明，刘国荣 编] 2012年版.pdf", "01-参考\离散数学-陈建明-2012.pdf"),
    (r"计算机\《深入理解计算机系统》教材\深入理解计算机系统（原书第3版）（CSAPP）.pdf", "01-参考\深入理解计算机系统-原书第3版-CSAPP.pdf"),
    (r"计算机\数据结构\数据结构教程（第5版）_李春葆.pdf", "01-参考\数据结构教程-第5版-李春葆.pdf"),
]
for s, d in book_map:
    mv(BOOK / s, BOOK / d, "教材重排")

# ---------------------------------------------------------------- 课程：课件 → 01-课件
CW = COURSE / "课件"
CW_NEW = COURSE / "01-课件"
# C语言
mv(CW / "C语言课件(含作业）" / "00-分章课件", CW_NEW / "C语言程序设计" / "00-分章课件", "课件归科")
mv(CW / "C语言课件(含作业）" / "2026-10-14", CW_NEW / "C语言程序设计" / "2026-10-14", "课件归科")
mv(CW / "C语言课件(含作业）" / "09-21提交作业", COURSE / "02-作业" / "作业截图" / "2026-09-21", "提交截图归作业")
for f in ["第1、2章作业.pdf", "第1、2章作业.zip", "微信图片_20260918180046_264_453.png"]:
    mv(CW / "C语言课件(含作业）" / "第1、2章作业" / f, COURSE / "02-作业" / "作业文件" / "C语言程序设计" / "第1、2章作业" / f, "作业从课件里拆出")
for f in ["main.exe", "main.o", "proj1.exe"]:
    mv(CW / "C语言课件(含作业）" / "第1、2章作业" / "proj1" / f, STAGE_BUILD / "proj1" / f, "构建产物暂存（源码/.dev/Makefile 保留）")
mv(CW / "C语言课件(含作业）" / "第1、2章作业" / "proj1",
   COURSE / "02-作业" / "作业文件" / "C语言程序设计" / "第1、2章作业" / "proj1", "源码工程跟着作业走")
# 人工智能：分章 pdf 从根收进 00-分章课件
mv(CW / "人工智能基础与应用" / "1绪论20260917.pdf", CW_NEW / "人工智能基础与应用" / "00-分章课件" / "1绪论20260917.pdf", "章级归一")
mv(CW / "人工智能基础与应用" / "2知识表示.pdf", CW_NEW / "人工智能基础与应用" / "00-分章课件" / "2知识表示.pdf", "章级归一")
mv(CW / "人工智能基础与应用" / "2026-10-11", CW_NEW / "人工智能基础与应用" / "2026-10-11", "课件归科")
mv(CW / "人工智能基础与应用" / "2026-10-17", CW_NEW / "人工智能基础与应用" / "2026-10-17", "课件归科")
# 博弈论
mv(CW / "博弈论课件（浙大版）" / "第一讲 概述", CW_NEW / "博弈论" / "00-分章课件" / "第一讲 概述", "课件归科")
# 线代（旧版 ppt 下移一层）
mv(CW / "线代课件（旧版）", CW_NEW / "线性代数" / "99-旧版课件", "旧版不删、下移一层")
for d in ["00-分章课件", "09-20", "10-08", "2026-10-13", "2026-10-17", "2026-10-20"]:
    newname = {"09-20": "2026-09-20", "10-08": "2026-10-08"}.get(d, d)
    mv(CW / "线性代数课件（含作业）" / d, CW_NEW / "线性代数" / newname, "日期统一 YYYY-MM-DD")
# 高数
for d in ["00-分章课件", "09-20", "10-08", "10-09", "2026-10-10", "2026-10-12",
          "2026-10-14", "2026-10-15", "2026-10-17", "2026-10-19"]:
    newname = {"09-20": "2026-09-20", "10-08": "2026-10-08", "10-09": "2026-10-09"}.get(d, d)
    mv(CW / "高数课件（含作业）" / d, CW_NEW / "工科数学分析" / newname, "日期统一 YYYY-MM-DD")

# ---------------------------------------------------------------- 课程：资料 → 03-资料
ZL = COURSE / "资料"
ZL_NEW = COURSE / "03-资料"
mv(ZL / "朋辅班会", ZL_NEW / "朋辅班会", "资料归科")
mv(ZL / "通用学术英语" / "生词", ZL_NEW / "通用学术英语" / "生词", "两个同名目录合并")
mv(ZL / "通用学术英语" / "课堂笔记", ZL_NEW / "通用学术英语" / "课堂笔记", "两个同名目录合并")
for d in ["Unit 1", "Unit 2", "Unit 3", "Unit 4"]:
    mv(ZL / "通用学术英语课程资料" / d, ZL_NEW / "通用学术英语" / d, "两个同名目录合并")

# ---------------------------------------------------------------- 课程：作业（先拆截图，最后整体搬 作业清单）
ZY = COURSE / "作业"
ZY_NEW = COURSE / "02-作业"
for d, nn in [("09-24", "2026-09-24"), ("10-08", "2026-10-08"),
              ("2026-10-13", "2026-10-13"), ("国庆作业", "2026-09-29-国庆")]:
    mv(ZY / "作业每日截图" / d, ZY_NEW / "作业截图" / nn, "截图日期统一 YYYY-MM-DD")
# 作业清单（Obsidian 库）整体搬到 02-作业\作业清单 —— 先修 _backup，再搬
mv(ZY / "作业清单", ZY_NEW / "作业清单", "Obsidian 库整体搬（路径同步改代码）")

# ---------------------------------------------------------------- 临时文件：收件箱化
# 01-课程资料 → 课程\03-资料
for f in ["12点名册.xlsx", "12班B2-1.xls", "2026-2027学年第一学期国防教育课程须知（2026.9）(3).pdf"]:
    mv(TMP / "01-课程资料" / "国防教育" / f, ZL_NEW / "国防教育" / f, "课程资料归课程")
for f in ["EGAP Orientation Week 1_202609.pdf", "外语类学科竞赛目录及分级（供大英教学参考）.pdf",
          "通用学术英语课程AI使用提醒.pdf"]:
    mv(TMP / "01-课程资料" / "通用学术英语" / f, ZL_NEW / "通用学术英语" / f, "课程资料归课程")
# 劳动教育 pdf 与 重要文件\通知原件 重复 → 留原件，副本进暂存
mv(TMP / "01-课程资料" / "劳动教育" / "附件：西安交通大学本科生劳动教育修读要求.pdf",
   STAGE_DUP / "劳动教育修读要求.pdf", "与 重要文件\\通知原件 重复（MD5 相同）")

# 02-作业 → 课程\02-作业
AJ = TMP / "02-作业"
for f in ["微信图片_20261006184751_147_4.jpg", "微信图片_20261006184753_148_4.jpg",
          "微信图片_20261006184754_149_4.jpg"]:
    mv(AJ / "10-06C语言作业" / f, ZY_NEW / "作业截图" / "2026-10-06" / "C语言程序设计" / f, "截图归日/科")
for f in ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg", "10-06高数作业.pdf"]:
    mv(AJ / "10-06高数作业" / f, ZY_NEW / "作业截图" / "2026-10-06" / "工科数学分析" / f, "截图归日/科")
for f in ["工科数学分析-习题1.4.pdf", "工科数学分析-习题1.5.pdf", "线性代数作业.pdf"]:
    mv(AJ / "2026-10-18作业" / "PDF汇总" / f, ZY_NEW / "作业截图" / "2026-10-18" / "汇总" / f, "截图归日")
for f in [f"{i}.jpg" for i in range(1, 15)]:
    mv(AJ / "2026-10-18作业" / "线代作业" / f, ZY_NEW / "作业截图" / "2026-10-18" / "线性代数" / f, "截图归日/科")
for f in [f"{i}.jpg" for i in range(1, 9)]:
    mv(AJ / "2026-10-18作业" / "高数作业" / f, ZY_NEW / "作业截图" / "2026-10-18" / "工科数学分析" / f, "截图归日/科")
for f in ["微信图片_20261020193716_196_4.jpg", "微信图片_20261020193717_197_4.jpg"]:
    mv(AJ / "2026-10-20" / f, ZY_NEW / "作业截图" / "2026-10-20" / f, "截图归日")
for f in ["屏幕截图 2026-10-21 145602.png", "韦恩图.png"]:
    mv(AJ / "2026-10-21" / f, ZY_NEW / "作业截图" / "2026-10-21" / f, "截图归日")

# 人工智能作业：三层套娃拍平 → 作业文件\人工智能基础与应用
AI_SRC = AJ / "人工智能作业"
AI_DST = ZY_NEW / "作业文件" / "人工智能基础与应用"
AI_FILES = {
    "作业1-小型专家系统-电脑软件故障诊断.docx": "作业1-小型专家系统.docx",
    "推理网络图.png": "作业1-推理网络图.png",
    "微信图片_20261002210323_141_4.jpg": "作业1-手写稿.jpg",
    "微信图片_20261020221737_199_4.jpg": "作业2-手写稿-1.jpg",
    "微信图片_20261020221738_200_4.jpg": "作业2-手写稿-2.jpg",
    "作业2-极大极小搜索.docx": "作业2-极大极小搜索.docx",
    "作业3-α-β剪枝.docx": "作业3-α-β剪枝.docx",
    "朱雀AI检测助手.pdf": "课程论文-AI检测报告.pdf",
    "课程论文.docx": "课程论文.docx",
}
BACKUP_ONLY = {"课程论文_原始备份.docx", "课程论文_删改版备份.docx"}
for root, _, files in os.walk(AI_SRC):
    for f in files:
        if f in BACKUP_ONLY:
            continue
        mm = AI_FILES.get(f, f)
        mv(Path(root) / f, AI_DST / mm, "三层同名嵌套拍平")
for f in ["课程论文_原始备份.docx", "课程论文_删改版备份.docx"]:
    mv(AI_SRC / "人工智能作业" / "人工智能作业" / f,
       STAGE_BAK / "人工智能-课程论文" / f, "版本备份进暂存（原件留 作业文件）")

for root, _, files in os.walk(AJ / "手抄生词"):
    for f in files:
        mv(Path(root) / f, ZY_NEW / "作业文件" / "通用学术英语" / "手抄生词" / f, "作业文件归科")
for f in ["Unit 1 Presentation-第4、5问-原文与标记词标注.md",
          "Unit 1 Presentation-第4、5问-原文与标记词标注.pdf"]:
    mv(AJ / "英语-Unit1Presentation" / f, ZY_NEW / "作业文件" / "通用学术英语" / "Unit1-Presentation" / f, "作业文件归科")

# 03-竞赛与活动 → 临时文件\01-竞赛与活动（用户定：留在临时文件）
CT = TMP / "03-竞赛与活动"
# 先摘重复件（必须在整个 竞赛通知 目录搬走之前）
mv(CT / "竞赛通知" / "附件1：第十八届全国大学生数学竞赛通知+.pdf",
   STAGE_DUP / "数学竞赛通知-全国.pdf", "与 重要文件\\通知原件 重复（MD5 相同）")
mv(CT / "竞赛通知" / "附件2：第十八届全国大学生数学竞赛通知+（陕西）.docx",
   STAGE_DUP / "数学竞赛通知-陕西.docx", "与 重要文件\\通知原件 重复（MD5 相同）")
mv(CT / "国庆剪辑" / "校园素材", CONTEST / "国庆剪辑" / "校园素材", "留在临时文件")
mv(CT / "剪映-1.zip", CONTEST / "国庆剪辑" / "剪映-1.zip", "留在临时文件")
mv(CT / "第一次培训.pptx", CONTEST / "职业规划大赛" / "第一次培训.pptx", "留在临时文件")
for d in ["竞赛通知", "职业规划大赛", "飞盘新秀杯"]:
    mv(CT / d, CONTEST / d, "留在临时文件")

# 孤立截图 → 收件箱
mv(TMP / "屏幕截图 2026-10-20 205200.png", INBOX / "屏幕截图 2026-10-20 205200.png", "未归档")

# ---------------------------------------------------------------- 重要文件：拍平 + 可读命名
JY = DOC / "01-教务与证明"
mv(JY / "升国旗仪式的集体活动参与证明.pdf", JY / "证明" / "升国旗仪式的集体活动参与证明.pdf", "证明归位")
mv(JY / "教务通知" / "原件" / "劳动教育" / "附件：西安交通大学本科生劳动教育修读要求.pdf",
   JY / "通知原件" / "劳动教育修读要求-2026.pdf", "原件保留，单文件拍平")
mv(JY / "教务通知" / "原件" / "数学竞赛附件" / "附件1：第十八届全国大学生数学竞赛通知+.pdf",
   JY / "通知原件" / "数学竞赛通知-全国.pdf", "原件保留，可读命名")
mv(JY / "教务通知" / "原件" / "数学竞赛附件" / "附件2：第十八届全国大学生数学竞赛通知+（陕西）.docx",
   JY / "通知原件" / "数学竞赛通知-陕西.docx", "原件保留，可读命名")
NOTES = JY / "教务通知" / "笔记"
if NOTES.is_dir():
    for f in NOTES.iterdir():
        mv(f, JY / "通知笔记" / f.name, "笔记独立成层")
mv(DOC / "02-证件" / "学生证和学籍卡" / "微信图片_20261008105152_547_242.jpg",
   DOC / "02-证件" / "学生证和学籍卡-01.jpg", "去掉微信默认名")
mv(DOC / "02-证件" / "学生证和学籍卡" / "微信图片_20261008105153_548_242.jpg",
   DOC / "02-证件" / "学生证和学籍卡-02.jpg", "去掉微信默认名")
mv(DOC / "03-个人事务" / "附件1入党申请书参考格式.docx",
   DOC / "03-个人事务" / "入党申请书-参考格式.docx", "可读命名")

# ---------------------------------------------------------------- 作业清单备份：只留最近 2 份（在搬 作业清单 之前做）
HW_BAK = ZY / "作业清单" / "_backup"
keep2 = []

# ---------------------------------------------------------------- 空目录 / 新文件
mkdir(INBOX, "收件箱")
mkdir(STAGE_DUP, "重复件暂存")
mkdir(STAGE_BAK, "备份暂存")
mkdir(STAGE_BUILD, "构建产物暂存")
mkdir(BOOK_INUSE, "本学期的教材")
mkdir(BOOK_REF, "参考书")
mkdir(CONTEST, "竞赛与活动")
mkdir(DESK / "AI产出", "AI 产出与版本存档（今天日记的需求）")

INDEX_MD = """# AI 产出索引

> 规则（2026-10-21 定）：**凡是有 AI 参与制作的文件都放这里，每次改版整份存档。**
> 目录结构：`AI产出\\<项目名>\\<YYYY-MM-DD>-v<N>\\`
> 每版目录里放：成品文件 + `改了什么.md`（一句一条，写清这版相对上一版改了什么）。
> 不动上一版的目录，改版一律新建目录 —— 这样任何一版都能原样取回。

## 项目清单

| 项目 | 最新版本 | 说明 |
|---|---|---|
| （待填） | | |
"""

NEW_FILES.append((DESK / "AI产出" / "00-索引.md", INDEX_MD))

# ================================================================ 执行
def build_conflict_report():
    conflicts, ok = [], []
    for m in MOVES:
        if not m["src"].exists():
            conflicts.append(("MISSING", m["src"], m["dst"], m["note"]))
        elif m["dst"].exists():
            conflicts.append(("EXISTS ", m["src"], m["dst"], m["note"]))
        else:
            ok.append(m)
    return ok, conflicts

def manifest_snapshot():
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = BACKUP_ROOT / f"reorg-{ts}"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for base in (TMP, BOOK, DOC, COURSE):
        for root, _, files in os.walk(base):
            for f in files:
                p = Path(root) / f
                try:
                    st = p.stat()
                    rows.append({"path": str(p), "size": st.st_size, "mtime": st.st_mtime})
                except OSError:
                    pass
    (out / "manifest.json").write_text(
        json.dumps({"time": ts, "files": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, len(rows)

def prune_empty(bases):
    removed = []
    for base in bases:
        for root, dirs, files in os.walk(base, topdown=False):
            for d in dirs:
                p = Path(root) / d
                try:
                    if p.is_dir() and not any(p.iterdir()):
                        p.rmdir()
                        removed.append(str(p))
                except OSError:
                    pass
    return removed

def main():
    apply = "--apply" in sys.argv
    ok, conflicts = build_conflict_report()

    print(f"=== reorg_desktop  {'APPLY' if apply else 'DRY-RUN'} ===  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"计划移动 {len(MOVES)} 条：可执行 {len(ok)}，异常 {len(conflicts)}；新建目录 {len(MKDIRS)}；新文件 {len(NEW_FILES)}")
    print()

    # 作业清单 _backup 修剪（只留最近 2 个目录 + 顶层 .md 备份）
    bak_plan = []
    if HW_BAK.is_dir():
        entries = sorted([e for e in HW_BAK.iterdir()], key=lambda p: p.name)
        dirs = [e for e in entries if e.is_dir()]
        olds = dirs[:-2] if len(dirs) > 2 else []
        for e in olds:
            bak_plan.append((e, STAGE_BAK / "作业清单-_backup" / e.name, "只留最近 2 份"))

    print("--- 移动明细 ---")
    for i, m in enumerate(ok, 1):
        print(f"{i:3d}. [{m['kind']}] {m['src'].relative_to(DESK)}")
        print(f"      → {m['dst'].relative_to(DESK)}   （{m['note']}）")
    if bak_plan:
        print("\n--- 旧备份修剪（→ 99-暂存\\旧备份）---")
        for s, d, n in bak_plan:
            print(f"  {s.relative_to(DESK)}  →  {d.relative_to(DESK)}   （{n}）")
    if conflicts:
        print("\n--- 异常（不会执行）---")
        for tag, s, d, n in conflicts:
            print(f"  {tag} {s}  →  {d}   （{n}）")
    print("\n--- 新建目录 ---")
    for m in MKDIRS:
        print(f"  {m['path'].relative_to(DESK)}   （{m['note']}）")
    print("\n--- 新文件 ---")
    for p, _ in NEW_FILES:
        print(f"  {p.relative_to(DESK)}")

    if not apply:
        print("\n[dry-run] 未改动任何文件。确认无误后加 --apply 执行。")
        return

    out, n = manifest_snapshot()
    print(f"\n[manifest] {out}\\manifest.json  ({n} 个文件)")

    for m in MKDIRS:
        m["path"].mkdir(parents=True, exist_ok=True)

    done = fail = skip = 0
    for s, d, note in bak_plan:
        d.parent.mkdir(parents=True, exist_ok=True)
        if d.exists():
            skip += 1
            continue
        shutil.move(str(s), str(d))
        done += 1

    for m in ok:
        d = m["dst"]
        d.parent.mkdir(parents=True, exist_ok=True)
        if d.exists():
            print(f"  SKIP(EXISTS) {m['src']}")
            skip += 1
            continue
        try:
            shutil.move(str(m["src"]), str(d))
            done += 1
        except Exception as e:
            print(f"  FAIL {m['src']}: {e}")
            fail += 1

    for p, content in NEW_FILES:
        if not p.exists():
            p.write_text(content, encoding="utf-8")

    removed = prune_empty([TMP, BOOK, DOC, COURSE])
    print(f"\n完成：移动 {done}，跳过 {skip}，失败 {fail}；清理空目录 {len(removed)} 个")
    for r in removed:
        print(f"  已删空目录 {r}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
