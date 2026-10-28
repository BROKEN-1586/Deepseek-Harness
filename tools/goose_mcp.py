"""goose_mcp.py — 把 goose CLI 包成一个 MCP stdio server，供 DSH（或任何 MCP 客户端）调用。

暴露 3 个工具（在 DSH 里显示为 mcp__goose__run / __recipes / __info）：
  run      让 goose 跑完一个任务（无头、一次性会话），返回最终回复 + 用量
  recipes  列出可用 recipe
  info     goose 版本与当前 provider/model

挂到 DSH（%USERPROFILE%\\.dsh\\profiles\\desktop\\cordis.patch.yml）：

- id: mcp-goose
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: goose
    transport: stdio
    command: 'C:\\Users\\36578\\AppData\\Local\\Programs\\Python\\Python314\\python.exe'
    args: ['D:\\Clearn\\tools\\goose_mcp.py']
    toolCallTimeoutMs: 900000

手动自测：python D:\\Clearn\\tools\\goose_mcp.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import anyio
from mcp.server.mcpserver import MCPServer

DEFAULT_CWD = r"D:\Clearn"
GOOSE_FALLBACKS = [
    r"D:\Goose-win32-x64\resources\bin\goose.exe",           # 1.56+ 标准安装布局
    r"D:\Goose-win32-x64\dist-windows\resources\bin\goose.exe",  # 1.5x 旧布局（可能已被更新清掉）
]
RECIPE_DIRS = [Path(r"D:\Clearn\.goose\recipes")]
TIMEOUT_CAP = 1800.0

app = MCPServer(
    name="goose",
    instructions=(
        "goose 是本机的一个独立 AI agent（有自己的工具、recipe 和知识库）。"
        "用 run 把「整块任务」交给它跑完并拿回最终回复：整理笔记、跑本地脚本、批量检索、按 recipe 处理流程。"
        "它不共享当前会话上下文，所以 task 要写成自足的完整指令："
        "把用户原话里的路径、文件名、日期、题号、参数原样抄进去，不要自己改写或概括；缺什么必须先问用户，不要猜。"
        "它只回一段最终结果，中途的思考过程你看不到，所以不要指望用它做需要来回确认的交互式步骤。"
        "它一次跑完可能需要几分钟。"
    ),
)


def _goose_bin() -> str:
    found = shutil.which("goose")
    if found:
        return found
    for cand in GOOSE_FALLBACKS:
        if Path(cand).exists():
            return cand
    root = Path(r"D:\Goose-win32-x64")
    if root.is_dir():
        hits = sorted(root.rglob("goose.exe"))
        if hits:
            return str(hits[0])
    raise FileNotFoundError("找不到 goose 可执行文件（PATH、已知安装目录、D:\\Goose-win32-x64 递归搜索都没命中）")


def _goose_run_sync(
    task: str,
    recipe: str | None,
    workdir: str | None,
    max_turns: int,
    timeout_sec: float,
) -> str:
    cwd = Path(workdir).expanduser() if workdir else Path(DEFAULT_CWD)
    if not cwd.is_dir():
        return f"[goose] workdir 不存在：{cwd}"

    cmd = [_goose_bin(), "run", "-q", "--no-session", "--output-format", "json",
           "--max-turns", str(int(max_turns))]
    if recipe:
        cmd += ["--recipe", recipe]
    cmd += ["-t", task]

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return f"[goose] 超时：{timeout_sec:.0f}s 内没跑完（任务可能太大，缩小范围或加大 timeout_sec）"
    except OSError as exc:
        return f"[goose] 启动失败：{exc}"

    elapsed = time.time() - started
    out = proc.stdout.decode("utf-8", "replace").strip()
    err = proc.stderr.decode("utf-8", "replace").strip()

    if proc.returncode != 0 and not out:
        return f"[goose] 退出码 {proc.returncode}\nSTDERR:\n{err[-2000:]}"

    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        body = out or err
        return f"{body[-4000:]}\n\n（goose 原始输出 · 退出码 {proc.returncode} · {elapsed:.1f}s）"

    texts: list[str] = []
    for msg in payload.get("messages", []):
        if msg.get("role") == "assistant":
            for block in msg.get("content", []):
                if block.get("type") == "text" and block.get("text"):
                    texts.append(block["text"])
    body = "\n\n".join(texts).strip() or "（goose 没有返回文本）"

    meta = payload.get("metadata", {}) or {}
    infer = {}
    for msg in reversed(payload.get("messages", [])):
        infer = (msg.get("metadata") or {}).get("inference") or infer
        if infer:
            break
    footer = [
        f"status={meta.get('status', '?')}",
        f"provider={infer.get('provider', '?')}",
        f"model={infer.get('requestedModel', '?')}",
        f"tokens={meta.get('input_tokens', '?')}/{meta.get('output_tokens', '?')}",
        f"cost=${meta.get('cost_usd', '?')}",
        f"{elapsed:.1f}s",
    ]
    if err:
        footer.append(f"stderr尾={err[-300:]!r}")
    return f"{body}\n\n—— goose · {' · '.join(footer)}"


@app.tool(title="Run a task with goose")
async def run(
    task: str,
    recipe: str | None = None,
    workdir: str | None = None,
    max_turns: int = 20,
    timeout_sec: float = 600,
) -> str:
    """Hand one self-contained task to the local goose agent and return its final answer.

    Args:
        task: Complete, self-sufficient instruction for goose (it does not see this conversation).
        recipe: Optional goose recipe name or YAML path to run instead of an ad-hoc task.
        workdir: Working directory for goose; defaults to D:\\Clearn.
        max_turns: Tool-iteration cap for goose.
        timeout_sec: Hard wall-clock limit, capped at 1800.
    """
    timeout_sec = max(30.0, min(float(timeout_sec), TIMEOUT_CAP))
    return await anyio.to_thread.run_sync(
        lambda: _goose_run_sync(task, recipe, workdir, max_turns, timeout_sec)
    )


@app.tool(title="List goose recipes")
async def recipes() -> str:
    """List the goose recipes available locally (name + first description line)."""
    lines: list[str] = []
    for root in RECIPE_DIRS:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.y*ml")):
            title = ""
            try:
                for raw in path.read_text("utf-8", "replace").splitlines()[:20]:
                    if raw.strip().startswith("title:"):
                        title = raw.split(":", 1)[1].strip().strip("'\"")
                        break
            except OSError:
                pass
            lines.append(f"- {path.stem}" + (f"：{title}" if title else ""))
    return "\n".join(lines) if lines else "（没有找到 recipe）"


def _provider_summary() -> str:
    cfg = Path(os.environ.get("APPDATA", "")) / "Block" / "goose" / "config" / "config.yaml"
    if not cfg.is_file():
        return f"config: {cfg} (不存在)"
    lines = cfg.read_text("utf-8", "replace").splitlines()
    provider = ""
    for raw in lines:
        if raw.strip().startswith("active_provider:"):
            provider = raw.split(":", 1)[1].strip()
            break
    model = ""
    if provider:
        for idx, raw in enumerate(lines):
            if raw.strip().rstrip(":") == provider and raw.strip().endswith(":"):
                for follow in lines[idx + 1: idx + 16]:
                    if follow.strip().startswith("model:"):
                        model = follow.split(":", 1)[1].strip()
                        return f"provider: {provider}\nmodel: {model}"
                break
    return f"provider: {provider or '?'}\nconfig: {cfg}"


@app.tool(title="goose info")
async def info() -> str:
    """Report the goose version, binary path and the configured provider/model."""
    binary = _goose_bin()
    proc = subprocess.run([binary, "--version"], capture_output=True, timeout=60)
    version = (proc.stdout or proc.stderr).decode("utf-8", "replace").strip()
    return f"binary: {binary}\nversion: {version}\n{_provider_summary()}"


def _selftest() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("goose:", _goose_bin())
    print(anyio.run(info))
    print("--- recipes ---")
    print(anyio.run(recipes))
    print("--- run (tiny task) ---")
    print(anyio.run(lambda: run("只回复两个字：可行", None, None, 2, 120.0)))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="goose MCP server (stdio)")
    parser.add_argument("--selftest", action="store_true", help="run local checks then exit")
    args = parser.parse_args()
    if args.selftest:
        return _selftest()
    app.run("stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
