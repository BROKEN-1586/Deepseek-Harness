"""DSH → MCP 前置探针（只读，不改任何东西）。

模拟 DSH 的 `@deepseek-ai/dsh-mcp-client` 启动方式，对 cordis.patch.yml 里
insert 块的两个 server 各做一遍真正的 MCP 握手：

  initialize → notifications/initialized → tools/list →（可选）tools/call

关键一点：用**精简环境变量**（类似 DSH 的 "scrubbed ambient env"）跑，
这样才能提前暴露「PATH 被削掉后找不到 goose.exe / 编码不对」这类问题。

用法：
    python dsh_mcp_preflight.py            # 两个 server 都测
    python dsh_mcp_preflight.py goose      # 只测一个

2026-10-28 建。
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time

PATCH = r"C:\Users\36578\.dsh\profiles\desktop\cordis.patch.yml"
PY = r"C:\Users\36578\AppData\Local\Programs\Python\Python314\python.exe"


def base_env(mode: str) -> dict:
    if mode == "full":
        return dict(os.environ)
    keep = ["SYSTEMROOT", "SystemRoot", "SystemDrive", "windir", "COMSPEC",
            "TEMP", "TMP", "PATHEXT", "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE", "OS", "COMPUTERNAME"]
    if mode != "strict":  # strict = 连用户目录类变量都不给（最坏情况）
        keep += ["USERPROFILE", "APPDATA", "LOCALAPPDATA",
                 "USERNAME", "USERDOMAIN", "HOMEDRIVE", "HOMEPATH"]
    env = {k: os.environ[k] for k in keep if k in os.environ}
    # 故意只给最小 PATH：模拟 PATH 里没有 goose / 没有 python 目录
    env["PATH"] = r"C:\Windows\system32;C:\Windows"
    return env


def load_servers() -> list[dict]:
    import yaml
    data = yaml.safe_load(open(PATCH, encoding="utf-8"))
    out = []
    for item in data:
        for ent in item.get("insert") or []:
            cfg = ent.get("config") or {}
            if str(cfg.get("transport")) == "stdio":
                out.append({"id": ent.get("id"), "name": ent.get("name"), **cfg})
    return out


class Server:
    def __init__(self, spec: dict, env_mode: str = "minimal", cwd: str | None = None):
        self.spec = spec
        self.name = spec.get("id") or spec.get("serverName")
        self.proc = subprocess.Popen(
            [spec["command"], *spec.get("args", [])],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=base_env(env_mode), cwd=cwd, bufsize=0,
        )
        self.q: queue.Queue = queue.Queue()
        self.err: list[str] = []
        threading.Thread(target=self._pump_out, daemon=True).start()
        threading.Thread(target=self._pump_err, daemon=True).start()
        self.next_id = 0

    def _pump_out(self):
        for line in iter(self.proc.stdout.readline, b""):
            line = line.strip()
            if not line:
                continue
            try:
                self.q.put(json.loads(line.decode("utf-8", "replace")))
            except json.JSONDecodeError:
                self.q.put({"__raw__": line.decode("utf-8", "replace")[:300]})

    def _pump_err(self):
        for line in iter(self.proc.stderr.readline, b""):
            self.err.append(line.decode("utf-8", "replace").rstrip())

    def send(self, method: str, params: dict | None = None, notify: bool = False, timeout: float = 60.0):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self.next_id += 1
            msg["id"] = self.next_id
            want = self.next_id
        else:
            want = None
        self.proc.stdin.write((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
        self.proc.stdin.flush()
        if notify:
            return None
        deadline = time.time() + timeout
        while time.time() < deadline:
            left = max(0.1, deadline - time.time())
            try:
                reply = self.q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError(f"{method} 超时（{timeout:.0f}s 无响应）")
            if reply.get("id") == want:
                return reply
            # 服务器主动推送的日志/通知，先攒着不打断
            if "__raw__" in reply:
                self.err.append("[stdout非JSON] " + reply["__raw__"])
        raise TimeoutError(f"{method} 超时")

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=8)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


def probe(spec: dict, calls: list[dict], env_mode: str = "minimal", cwd: str | None = None) -> tuple[bool, list[str]]:
    notes: list[str] = []
    notes.append(f"env={env_mode} / cwd={cwd or '(继承)'}")
    srv = Server(spec, env_mode=env_mode, cwd=cwd)
    ok = True
    try:
        r = srv.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "dsh-preflight", "version": "0.1"},
        }, timeout=120)
        if "error" in r:
            notes.append(f"initialize 失败：{r['error']}")
            return False, notes
        info = r.get("result", {}).get("serverInfo", {})
        notes.append(f"initialize OK → {info.get('name')} v{info.get('version')} / protocol {r['result'].get('protocolVersion')}")

        srv.send("notifications/initialized", {}, notify=True)
        tl = srv.send("tools/list", {}, timeout=120)
        tools = (tl.get("result") or {}).get("tools") or []
        notes.append(f"tools/list → {len(tools)} 个工具：{[t['name'] for t in tools]}")

        for call in calls:
            name = call["name"]
            t0 = time.time()
            res = srv.send("tools/call", {"name": name, "arguments": call.get("arguments", {})}, timeout=call.get("timeout", 120))
            dt = time.time() - t0
            if "error" in res:
                notes.append(f"tools/call {name} → ❌ {res['error']}  ({dt:.1f}s)")
                ok = False
                continue
            content = (res.get("result") or {}).get("content") or []
            text = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            text = " ".join(text.split())
            notes.append(f"tools/call {name} → ✅ {dt:.1f}s · {len(text)} 字符 · 预览：{text[:160]}")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"❌ 异常：{type(exc).__name__}: {exc}")
        ok = False
    finally:
        srv.close()
        if srv.err:
            tail = [ln for ln in srv.err if ln.strip()][-6:]
            notes.append("stderr 尾部：" + " | ".join(tail))
    return ok, notes


def main() -> int:
    wanted = sys.argv[1:] or ["mcp-goose", "mcp-rag"]
    servers = {s["id"]: s for s in load_servers()}
    plan = {
        "mcp-goose": [{"name": "info", "timeout": 120}],
        "mcp-rag": [{"name": "search_knowledge", "arguments": {"kb": "archive-rag", "query": "镜像 勾选 回写", "top_k": 2}, "timeout": 180}],
    }
    all_ok = True
    for key in wanted:
        spec = servers.get(key)
        print(f"\n{'='*70}\n[{key}] 启动命令：{spec['command'] if spec else '未找到'} {spec.get('args') if spec else ''}")
        if not spec:
            print("  ❌ cordis.patch.yml 的 insert 块里没有这个条目")
            all_ok = False
            continue
        ok, notes = probe(spec, plan.get(key, []), env_mode=os.environ.get("PREFLIGHT_ENV", "minimal"), cwd=os.environ.get("PREFLIGHT_CWD") or None)
        all_ok &= ok
        for n in notes:
            print("  " + n)
        print(f"  → {'PASS' if ok else 'FAIL'}")
    print(f"\n{'='*70}\n总判定：{'全部 PASS' if all_ok else '有 FAIL，见上'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
