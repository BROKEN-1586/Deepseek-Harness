# -*- coding: utf-8 -*-
r"""
ai_archive.py —— AI 产出归档管理（2026-10-21 用户口径）

口径
  · 收录范围：**凡有 AI 参与制作的文档**（不限于 goose / 不限于谁做的）——docx / pdf / md / pptx / xlsx 等
  · 一律存**副本**（都是文档，不做大小阈值）；原件留在原处继续用，这里只做快照
  · 一次改版 = 一个 `<YYYY-MM-DD>-v<N>` 目录，**永不覆盖旧版**
  · 每版必有 `改了什么.md`；项目有 `00-索引.md`；根有 `00-索引.md`（总表）
  · 废弃只进 `99-废弃\`，**不真删**

用法
  python ai_archive.py list
  python ai_archive.py show   <项目>
  python ai_archive.py new    <项目> --from <文件>[,<文件>...] --note "这版改了什么" [--who "..."] [--ai 起草|改写|排版] [--slug 目录名]
  python ai_archive.py add    <项目> <文件>[,<文件>...]
  python ai_archive.py diff   <项目> <版本A> <版本B>
  python ai_archive.py restore <项目> <版本> --to <目标目录> [--apply]
  python ai_archive.py retire <项目> [--apply]
  （new / add / retire 默认 dry-run，加 --apply 才写盘；new / add 落盘后**自动重建 aiout-rag**，加 --no-rebuild 跳过）
"""
import argparse
import hashlib
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(r"C:\Users\36578\Desktop\AI产出")
TRASH = ROOT / "99-废弃"
INDEX = ROOT / "00-索引.md"

RAG_SERVER = Path(r"D:\rag\rag_server.py")
RAG_KB = "aiout-rag"


def rebuild_aiout():
    """归档后自动重建 aiout-rag 索引（用户 2026-10-21 定：直接重建，不问）。"""
    import os
    import subprocess
    env = dict(os.environ)
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["PYTHONIOENCODING"] = "utf-8"
    print(f"  [rag] 重建 {RAG_KB} …")
    try:
        r = subprocess.run([sys.executable, str(RAG_SERVER), "--build", RAG_KB, "--force"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800, env=env)
        tail = [l for l in (r.stdout or "").strip().splitlines() if l.strip()][-2:]
        for l in tail:
            print(f"  [rag] {l.strip()}")
        ok = any(l.strip().startswith(f"[{RAG_KB}] 完成") for l in tail)
        print(f"  [rag] {'✅ 索引已更新' if ok else '⚠️ 未见到完成标记，请手动核对'}")
        if not ok and r.stderr:
            print("  [rag] stderr:", r.stderr.strip().splitlines()[-1][:200])
    except Exception as e:
        print(f"  [rag] ⚠️ 重建失败：{e}")


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:10]

def human(n: int) -> str:
    return f"{n/1024:.0f} KB" if n < 1 << 20 else f"{n/1048576:.1f} MB"

def projects():
    if not ROOT.is_dir():
        return []
    return sorted(p for p in ROOT.iterdir()
                  if p.is_dir() and not p.name.startswith(".") and p.name != "99-废弃")

def find_proj(name: str) -> Path:
    for p in projects():
        if p.name == name or p.name.endswith(name) or name in p.name:
            return p
    raise SystemExit(f"找不到项目「{name}」。现有：{[p.name for p in projects()]}")

def versions(proj: Path):
    if not proj.is_dir():
        return []
    return sorted(p for p in proj.iterdir() if p.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-v\d+$", p.name))

def next_version(proj: Path) -> str:
    today = date.today().isoformat()
    n = sum(1 for v in versions(proj) if v.name.startswith(today)) + 1
    return f"{today}-v{n}"

def files_of(vdir: Path):
    return sorted(f for f in vdir.rglob("*") if f.is_file() and f.name != "改了什么.md")

# ---------------------------------------------------------------- 索引维护
def proj_index_text(proj: Path) -> str:
    vs = versions(proj)
    rows = []
    for v in vs:
        fs = files_of(v)
        size = sum(f.stat().st_size for f in fs)
        note = ""
        md = v / "改了什么.md"
        if md.is_file():
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("- 这版改了什么："):
                    note = line.split("：", 1)[1].strip()
                    break
        rows.append(f"| `{v.name}` | {len(fs)} | {human(size)} | {note} |")
    body = "\n".join(rows) if rows else "| — | — | — | 尚无版本 |"
    return f"""# {proj.name} · 索引

> 每个版本一个目录，**不覆盖旧版**；`改了什么.md` 写清这版相对上版改了什么。
> 最新版本：**{vs[-1].name if vs else '—'}**　·　共 {len(vs)} 版　·　返回 [[../00-索引]]

| 版本 | 文件数 | 体积 | 这版改了什么 |
|---|---|---|---|
{body}
"""

def root_index_text() -> str:
    rows2 = []
    for p in projects():
        vs = versions(p)
        if not vs:
            continue
        last = vs[-1]
        ts = last.stat().st_mtime
        import datetime as _dt
        rows2.append((p, last, len(vs), _dt.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")))
    body = "\n".join(
        f"| [[{p.name}/00-索引\\|{p.name}]] | `{last.name}` | {n} | {t} |"
        for p, last, n, t in rows2) or "| — | — | — | — |"
    return f"""# AI 产出索引（总表）

> **收录口径**（2026-10-21 用户定）：凡是有 AI 参与制作的**文档**都收 —— 不限于 goose，不限于谁做的。
> **存放口径**：一次改版 = 一个 `<YYYY-MM-DD>-v<N>` 目录，**永不覆盖旧版**；一律存**副本**，原件留在原处照常用。
> **索引分两层**：本页＝项目总表；每个项目另有 `00-索引.md`＝版本时间线。
> **删除口径**：废弃只进 `99-废弃\\`，不真删。

| 项目 | 最新版本 | 版本数 | 最后改动 |
|---|---|---|---|
{body}

## 用法

```bat
python D:\\Clearn\\tools\\ai_archive.py list                     :: 看全部项目
python D:\\Clearn\\tools\\ai_archive.py show   人工智能-课程论文   :: 看版本时间线
python D:\\Clearn\\tools\\ai_archive.py new    人工智能-课程论文 --from "C:\\...\\课程论文.docx" --note "补了第3章" --apply
python D:\\Clearn\\tools\\ai_archive.py diff   人工智能-课程论文 2026-10-21-v1 2026-10-22-v1
python D:\\Clearn\\tools\\ai_archive.py restore 人工智能-课程论文 2026-10-21-v1 --to "C:\\...\\提交" --apply
```

> 不接 RAG（避免污染现有库）；需要时再单开 `aiout-rag`。
"""

def write_indexes(apply: bool, only: Path | None = None):
    targets = [only] if only else list(projects())
    for p in targets:
        if not versions(p):
            continue
        path = p / "00-索引.md"
        txt = proj_index_text(p)
        if apply:
            path.write_text(txt, encoding="utf-8")
        print(f"  索引{'已写' if apply else '将写'}：{path.relative_to(ROOT)}")
    if not only:
        txt = root_index_text()
        if apply:
            INDEX.write_text(txt, encoding="utf-8")
        print(f"  总表{'已写' if apply else '将写'}：{INDEX.relative_to(ROOT)}")

# ---------------------------------------------------------------- 命令
def cmd_new(a):
    proj = None
    for p in projects():
        if (a.slug and p.name == a.slug) or (not a.slug and (p.name == a.project or a.project in p.name)):
            proj = p
            break
    if proj is None:
        dirname = a.slug or a.project
        proj = ROOT / dirname
        print(f"  新建项目目录：{proj.relative_to(ROOT)}")
    vname = next_version(proj)
    vdir = proj / vname
    srcs = [Path(s.strip().strip('"')) for s in a.files.split(",")]
    for s in srcs:
        if not s.exists():
            raise SystemExit(f"源文件不存在：{s}")
    print(f"  新版本：{proj.name}/{vname}（{len(srcs)} 个文件）")
    for s in srcs:
        print(f"    + {s.name}  ({human(s.stat().st_size)})")
    if not a.apply:
        print("  [dry-run] 未写入；加 --apply 执行")
        return
    vdir.mkdir(parents=True, exist_ok=True)
    for s in srcs:
        shutil.copy2(s, vdir / s.name)
    md = [f"# {proj.name} · {vname}", ""]
    md.append(f"- 这版改了什么：{a.note or '（待补）'}")
    md.append(f"- 谁提的需求：{a.who or '（待补）'}")
    prev = [v for v in versions(proj) if v.name < vname]
    if prev:
        before = {f.name: (f.stat().st_size, md5(f)) for f in files_of(prev[-1])}
        after = {f.name: (f.stat().st_size, md5(f)) for f in files_of(vdir)}
        lines = [f"  - `{n}`：大小 {human(before[n][0])} → {human(after[n][0])}（{'内容相同' if after[n][1]==before[n][1] else '内容已变'}）"
                 for n in after if n in before]
        lines += [f"  - `{n}`：新增" for n in after if n not in before]
        lines += [f"  - `{n}`：本版未包含" for n in before if n not in after]
        md.append(f"- 与上版（{prev[-1].name}）差异：")
        md.extend(lines or ["  - （无文件级差异）"])
    else:
        md.append("- 与上版差异：（这是第一版，无上版）")
    md.append(f"- AI 参与方式：{a.ai or '（待补：起草 / 改写 / 排版）'}")
    md.append(f"- 原件位置：{'；'.join(str(s) for s in srcs)}")
    (vdir / "改了什么.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    write_indexes(True, only=proj)
    write_indexes(True)
    if not getattr(a, "no_rebuild", False):
        rebuild_aiout()

def cmd_add(a):
    proj = find_proj(a.project)
    vs = versions(proj)
    if not vs:
        raise SystemExit("该项目还没有版本，先 new")
    vdir = vs[-1]
    srcs = [Path(s.strip().strip('"')) for s in a.files.split(",")]
    print(f"  追加到 {proj.name}/{vdir.name}")
    for s in srcs:
        if not s.exists():
            raise SystemExit(f"源文件不存在：{s}")
        print(f"    + {s.name}")
        if a.apply:
            shutil.copy2(s, vdir / s.name)
    if a.apply:
        write_indexes(True, only=proj)
        write_indexes(True)
        if not getattr(a, "no_rebuild", False):
            rebuild_aiout()
    else:
        print("  [dry-run] 未写入")

def cmd_list(_):
    ps = projects()
    if not ps:
        print("（空）")
        return
    for p in ps:
        vs = versions(p)
        last = vs[-1].name if vs else "—"
        print(f"{p.name:<32} {len(vs)} 版  最新 {last}")

def cmd_show(a):
    proj = find_proj(a.project)
    vs = versions(proj)
    print(f"== {proj.name}（{len(vs)} 版）==")
    for v in vs:
        fs = files_of(v)
        print(f"  {v.name}  {len(fs)} 文件 / {human(sum(f.stat().st_size for f in fs))}")
        md = v / "改了什么.md"
        if md.is_file():
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("- 这版改了什么："):
                    print(f"      {line.split('：',1)[1].strip()}")
                    break

def cmd_diff(a):
    proj = find_proj(a.project)
    v1, v2 = proj / a.v1, proj / a.v2
    for v in (v1, v2):
        if not v.is_dir():
            raise SystemExit(f"版本目录不存在：{v}")
    d1 = {f.name: (f.stat().st_size, md5(f)) for f in files_of(v1)}
    d2 = {f.name: (f.stat().st_size, md5(f)) for f in files_of(v2)}
    print(f"== {v1.name} → {v2.name} ==")
    for n in sorted(set(d1) | set(d2)):
        if n not in d1:
            print(f"  + {n}（新增，{human(d2[n][0])}）")
        elif n not in d2:
            print(f"  - {n}（本版未包含）")
        elif d1[n][1] == d2[n][1]:
            print(f"  = {n}（内容相同）")
        else:
            print(f"  ~ {n}（{human(d1[n][0])} → {human(d2[n][0])}）")

def cmd_restore(a):
    proj = find_proj(a.project)
    vdir = proj / a.version
    if not vdir.is_dir():
        raise SystemExit(f"版本不存在：{vdir}")
    dst = Path(a.to)
    fs = files_of(vdir)
    print(f"  取回 {proj.name}/{vdir.name} → {dst}（{len(fs)} 文件）")
    for f in fs:
        t = dst / f.name
        flag = ""
        if t.exists():
            flag = f"  ⚠️ 将覆盖现有 {human(t.stat().st_size)} 文件（先备份为 .bak）"
        print(f"    {f.name}{flag}")
        if a.apply:
            dst.mkdir(parents=True, exist_ok=True)
            if t.exists():
                shutil.copy2(t, t.with_suffix(t.suffix + ".bak"))
            shutil.copy2(f, t)
    if not a.apply:
        print("  [dry-run] 未写入；加 --apply 执行")

def cmd_retire(a):
    proj = find_proj(a.project)
    dst = TRASH / proj.name
    print(f"  {proj.name} → {dst.relative_to(ROOT)}")
    if a.apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(proj), str(dst))
        write_indexes(True)
        if not getattr(a, "no_rebuild", False):
            rebuild_aiout()
    else:
        print("  [dry-run] 未写入")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("show")
    p.add_argument("project")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("retire")
    p.add_argument("project")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--no-rebuild", action="store_true", help="不重建 aiout-rag 索引")
    p.set_defaults(fn=cmd_retire)
    p = sub.add_parser("new")
    p.add_argument("project")
    p.add_argument("--from", dest="files", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--who", default="")
    p.add_argument("--ai", default="")
    p.add_argument("--slug", default="")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--no-rebuild", action="store_true", help="不重建 aiout-rag 索引")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("add")
    p.add_argument("project")
    p.add_argument("files")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--no-rebuild", action="store_true", help="不重建 aiout-rag 索引")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("diff")
    p.add_argument("project")
    p.add_argument("v1")
    p.add_argument("v2")
    p.set_defaults(fn=cmd_diff)
    p = sub.add_parser("restore")
    p.add_argument("project")
    p.add_argument("version")
    p.add_argument("--to", required=True)
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_restore)
    a = ap.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    a.fn(a)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
