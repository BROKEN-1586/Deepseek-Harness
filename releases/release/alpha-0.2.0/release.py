"""release.py — 自研工具的「四通道版本库」：发布 = 本地快照目录 + git commit + tag。

体例（2026-10-28 用户定）：
  releases/
    00-索引/00-索引.md            总表：工具 × 当前通道 × 最新版本 × 版本数
    <工具>/
      <通道>-<版本>/              每版一个只读快照，不覆盖旧版
        <脚本副本>                 tools\\<工具>.py 或 .bat 的原样拷贝
        MANIFEST.json             版本 / 通道 / 日期 / sha256 / 来源 commit / 环境
        改了什么.md                这版相对上一版改了什么（人读）

四通道（成熟度，不是递增序号）：alpha（开发中）→ beta（功能齐、优化中）→ stable（稳定）→ ultra（最终版，仍可 ultra.x 继续发）

用法：
  python tools/release.py publish <工具> --channel alpha --version 0.1.0 --note "首版"  # 预演
  python tools/release.py publish <工具> --channel beta  --version 0.2.0 --note "..." --apply
  python tools/release.py baseline --channel alpha --version 0.1.0 --apply   # 把 tools\\ 下全部脚本打成基线
  python tools/release.py list [<工具>]
  python tools/release.py verify <工具> <通道>-<版本>

默认**预演**，加 `--apply` 才写盘 / commit。写盘前会先做全部校验（通道只能前进、版本号只能变大、
目标目录不能已存在），校验不过一条都不写。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(r"D:\Clearn")
TOOLS = ROOT / "tools"
REL = ROOT / "releases"
INDEX = REL / "00-索引" / "00-索引.md"

CHANNELS = ["alpha", "beta", "stable", "ultra"]
CH_LABEL = {"alpha": "开发中", "beta": "基础功能完整、优化中", "stable": "稳定", "ultra": "最终版"}


# ---------- 基础 ----------

def _run_git(args: list[str], capture: bool = False) -> tuple[int, str]:
    """跑 git。沙箱里 CreatePipe 被拒，所以要用管道时必须落到临时文件。"""
    if not capture:
        rc = subprocess.run(["git", *args], cwd=str(ROOT)).returncode
        return rc, ""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        rc = subprocess.run(["git", *args], cwd=str(ROOT), stdout=out, stderr=err).returncode
        out.seek(0)
        err.seek(0)
        text = out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")
    return rc, text.strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ver_tuple(v: str) -> tuple:
    parts = []
    for piece in v.replace("v", "").split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _tool_files(name: str) -> list[Path]:
    hits = []
    for ext in (".py", ".bat", ".ps1"):
        p = TOOLS / (name + ext)
        if p.is_file():
            hits.append(p)
    if not hits:
        raise SystemExit(f"[release] 找不到工具：tools\\{name}.py / .bat / .ps1 都不存在")
    return hits


def _published(name: str) -> list[dict]:
    """已发布版本，按版本号升序。"""
    out = []
    base = REL / name
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        man = d / "MANIFEST.json"
        if not man.is_file():
            continue
        try:
            data = json.loads(man.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data.setdefault("dir", d.name)
        out.append(data)
    out.sort(key=lambda m: _ver_tuple(m.get("version", "0")))
    return out


def _all_tools() -> list[str]:
    names = set()
    for p in sorted(TOOLS.iterdir()):
        if p.is_file() and p.suffix.lower() in (".py", ".bat", ".ps1"):
            names.add(p.stem)
    return sorted(names)


def _check(name: str, channel: str, version: str) -> list[str]:
    errs = []
    if channel not in CHANNELS:
        errs.append(f"通道只能是 {CHANNELS}")
        return errs
    target = REL / name / f"{channel}-{version}"
    if target.exists():
        errs.append(f"目标目录已存在：{target}")
    old = _published(name)
    if old:
        top = old[-1]
        if _ver_tuple(version) <= _ver_tuple(top.get("version", "0.0.0")):
            errs.append(f"版本号必须大于已有的最高版 {top.get('version')}（现在给的是 {version}）")
        if CHANNELS.index(channel) < CHANNELS.index(top.get("channel", "alpha")):
            errs.append(f"通道不能倒退：上一版是 {top.get('channel')}，现在给 {channel}")
    return errs


# ---------- 写索引 ----------

def _index_row(name: str) -> str:
    old = _published(name)
    if not old:
        return ""
    top = old[-1]
    return f"| [[{name}]] | {top.get('channel')} | `{top.get('version')}` | {len(old)} | {top.get('released_at', '')[:10]} |"


def _write_index(names: list[str]) -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    rows = [r for r in (_index_row(n) for n in names) if r]
    body = "\n".join(rows) if rows else "| — | — | — | — | — |"
    text = f"""# 工具版本库 · 总表

> 每个版本一个目录，**不覆盖旧版**；每次发布 = 一个目录 ＋ 一次 commit ＋ 一个 tag。
> 四通道（成熟度，不是序号）：**alpha**（开发中）→ **beta**（基础功能完整、优化中）→ **stable**（稳定）→ **ultra**（最终版，仍可 ultra.x）
> 生成方式：`python tools\\release.py publish <工具> --channel <通道> --version <x.y.z> --note "..." --apply`

| 工具 | 当前通道 | 最新版本 | 版本数 | 最近发布 |
|---|---|---|---|---|
{body}
"""
    INDEX.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


# ---------- 命令 ----------

def cmd_publish(name: str, channel: str, version: str, note: str, apply: bool,
                git: bool = True, quiet: bool = False) -> int:
    files = _tool_files(name)
    errs = _check(name, channel, version)
    if errs:
        for e in errs:
            print(f"[x] {e}")
        return 2

    dest = REL / name / f"{channel}-{version}"
    if not quiet:
        print(f"[plan] {name} {channel} {version}")
        print(f"       来源：{', '.join(str(f) for f in files)}")
        print(f"       落点：{dest}")
    if not apply:
        print("       预演：加 --apply 才写盘并提交 git")
        return 0

    dest.mkdir(parents=True)
    for f in files:
        shutil.copy2(f, dest / f.name)
    rc, head = _run_git(["rev-parse", "HEAD"], capture=True)
    manifest = {
        "tool": name,
        "channel": channel,
        "channel_label": CH_LABEL[channel],
        "version": version,
        "released_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": [str(f) for f in files],
        "files": [
            {"name": f.name, "size": (dest / f.name).stat().st_size, "sha256": _sha256(dest / f.name)}
            for f in files
        ],
        "git_head_before": head if rc == 0 else None,
        "python": sys.version.split()[0],
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")

    old = _published(name)
    prev = f"上一版：{old[-1]['channel']}-{old[-1]['version']}（{old[-1].get('released_at','')[:10]}）" if old else "首版"
    md = f"""# {name} {channel}-{version}

- 通道：**{channel}**（{CH_LABEL[channel]}）
- 发布：{manifest['released_at']}
- 这版改了什么：{note or '（未写）'}
- {prev}
- 来源：{', '.join(f'`{f}`' for f in files)}
- 校验：见 `MANIFEST.json`（sha256 × {len(files)}）
"""
    (dest / "改了什么.md").write_bytes(md.replace("\n", "\r\n").encode("utf-8"))

    _write_index(_all_tools())
    if not git:
        if not quiet:
            print(f"[ok] {dest}（未提交，交给上层统一 commit）")
        return 0

    _run_git(["add", "--", str(REL)])
    rc, _ = _run_git(["commit", "-m", f"release({name}): {channel}-{version}"], capture=True)
    tag = f"{name}/v{version}"
    _run_git(["tag", "-f", tag])
    print(f"[ok] {dest}")
    print(f"[git] tag {tag}" + ("" if rc == 0 else f"（commit rc={rc}）"))
    return 0


def cmd_baseline(channel: str, version: str, note: str, apply: bool) -> int:
    names = _all_tools()
    print(f"[plan] baseline：{len(names)} 个工具 → {channel}-{version}")
    bad = []
    for n in names:
        errs = _check(n, channel, version)
        if errs:
            bad.append((n, errs))
    if bad:
        for n, errs in bad:
            print(f"[x] {n}: {'; '.join(errs)}")
        return 2
    if not apply:
        print("       预演：加 --apply 才写")
        return 0
    for n in names:
        rc = cmd_publish(n, channel, version, note, apply=True, git=False, quiet=True)
        if rc:
            return rc
    _run_git(["add", "--", str(REL)])
    rc, _ = _run_git(["commit", "-m", f"release(baseline): {channel}-{version}（{len(names)} 个工具）"], capture=True)
    for n in names:
        _run_git(["tag", "-f", f"{n}/v{version}"])
    print(f"[ok] baseline：{len(names)} 个工具写入 {channel}-{version}" + ("" if rc == 0 else f"（commit rc={rc}）"))
    print(f"[git] tag：{len(names)} 个（<工具>/v{version}）")
    return 0


def cmd_list(name: str | None) -> int:
    names = [name] if name else _all_tools()
    for n in names:
        old = _published(n)
        if not old:
            print(f"{n}: （还没有发布版本）")
            continue
        print(f"{n}: {len(old)} 版，最新 {old[-1]['channel']}-{old[-1]['version']}（{old[-1].get('released_at','')[:10]}）")
        for m in old:
            print(f"    {m['channel']}-{m['version']:<8} {m.get('released_at','')[:10]}")
    return 0


def cmd_verify(name: str, dsn: str) -> int:
    d = REL / name / dsn
    man = d / "MANIFEST.json"
    if not man.is_file():
        print(f"[x] 没有 {man}")
        return 2
    data = json.loads(man.read_text("utf-8"))
    bad = 0
    for item in data.get("files", []):
        p = d / item["name"]
        if not p.is_file():
            print(f"[x] 缺文件 {p.name}")
            bad += 1
            continue
        got = _sha256(p)
        if got != item["sha256"]:
            print(f"[x] {p.name} sha256 不符：{got[:12]} != {item['sha256'][:12]}")
            bad += 1
    print(f"[{'ok' if bad == 0 else 'x'}] {name} {dsn}：{len(data.get('files', []))} 个文件校验{'通过' if bad == 0 else f'失败 {bad} 个'}")
    return 0 if bad == 0 else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="release.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("publish")
    p.add_argument("tool")
    p.add_argument("--channel", required=True, choices=CHANNELS)
    p.add_argument("--version", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--apply", action="store_true")

    b = sub.add_parser("baseline")
    b.add_argument("--channel", default="alpha", choices=CHANNELS)
    b.add_argument("--version", default="0.1.0")
    b.add_argument("--note", default="基线：现有脚本原样入库")
    b.add_argument("--apply", action="store_true")

    l = sub.add_parser("list")
    l.add_argument("tool", nargs="?")

    v = sub.add_parser("verify")
    v.add_argument("tool")
    v.add_argument("dsn")

    a = ap.parse_args(argv)
    if a.cmd == "publish":
        return cmd_publish(a.tool, a.channel, a.version, a.note, a.apply)
    if a.cmd == "baseline":
        return cmd_baseline(a.channel, a.version, a.note, a.apply)
    if a.cmd == "list":
        return cmd_list(a.tool)
    if a.cmd == "verify":
        return cmd_verify(a.tool, a.dsn)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
