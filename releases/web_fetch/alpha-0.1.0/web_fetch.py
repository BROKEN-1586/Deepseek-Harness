#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""web_fetch.py —— DeepSeek 网页抓取（POST /v1/tools/fetch）

把单个网页抓成 Markdown 正文。实测 0.2 秒级（2026-10-23），比本机 curl 稳。
联网口径：**先 DeepSeek 直连 → 失败再 Tavily（tavily_extract）**。

用法：
  python web_fetch.py https://example.com/article
  python web_fetch.py <url> -o D:\\tmp\\page.md              # 存全文（stdout 只打印摘要）
  python web_fetch.py <url> --max-chars 0                    # stdout 不截断
  python web_fetch.py <url> --max-chars 2000                 # 只打印前 2000 字
  python web_fetch.py <url> --json                           # 原始 JSON（title + content）

参数：
  --max-chars    stdout 打印的正文上限，默认 6000；0 = 全文
  -o/--out       写入文件（不加则只打印）
  --json         stdout 输出 JSON
  --quiet        只打印标题 + 字数

退出码：0 成功 / 1 参数或网络错误 / 2 站点拒绝或抓不到正文
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

API = "https://api.deepseek.com/v1/tools/fetch"
KEYS = Path(r"D:\AgentData\keys.json")
RETRY_STATUS = {408, 429, 500, 502, 503, 504}

# 文档的错误码含义（4xx 且不合法就别重试）
HINTS = {
    400: "请求头或请求体不合法（URL 格式？必须带 host 的 http/https，且不能带用户名密码）",
    401: "API Key 缺失或无效",
    402: "账号余额不足",
    403: "被安全策略拒绝（站点或目标内容不允许抓）",
    404: "抓不到可用的网页内容（URL 不可用 / 被站点拦截 / 内容类型不支持 / 无正文）",
    408: "读请求体超时",
    413: "请求体过大",
    429: "触发限速（Fetch 账号级 25 QPS，单个域名另有 QPS 限制）",
    500: "DeepSeek 服务端错误",
    504: "下游（目标站点）请求超时",
}


def die(msg, code=1):
    print(f"错误：{msg}", file=sys.stderr)
    return code


def load_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    try:
        data = json.loads(KEYS.read_text(encoding="utf-8"))
        prov = data["providers"]["deepseek"]
    except FileNotFoundError:
        raise SystemExit(die(f"找不到 {KEYS}，也没设环境变量 DEEPSEEK_API_KEY"))
    except (KeyError, json.JSONDecodeError) as e:
        raise SystemExit(die(f"{KEYS} 里没找到 providers.deepseek（{e}）"))
    for name in ("apiKey", "api_key", "key"):
        if prov.get(name):
            return prov[name]
    raise SystemExit(die(f"{KEYS} 的 providers.deepseek 里没有 apiKey 字段"))


def fetch(url, key, timeout=45):
    import requests

    last = None
    for i in range(3):
        t0 = time.time()
        try:
            r = requests.post(
                API,
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                json={"url": url},
                timeout=timeout,
            )
        except Exception as e:
            last = (1, f"{type(e).__name__}: {e}")
            time.sleep(1.5 * (i + 1))
            continue
        if r.status_code == 200:
            return r.json(), time.time() - t0
        msg = ""
        try:
            msg = r.json().get("error", {}).get("message", "")
        except Exception:
            msg = (r.text or "")[:200]
        hint = HINTS.get(r.status_code, "")
        detail = f"HTTP {r.status_code}" + (f"（{hint}）" if hint else "") + (f" {msg}" if msg else "")
        if r.status_code in RETRY_STATUS and i < 2:
            last = (2, detail + " —— 重试中")
            time.sleep(2.0 * (i + 1))
            continue
        return None, (2 if r.status_code in (403, 404) else 1, detail)
    return None, (last or (1, "未知错误"))


def main():
    ap = argparse.ArgumentParser(add_help=True, description="DeepSeek 网页抓取 → Markdown")
    ap.add_argument("url", help="http/https URL，≤8192 字符")
    ap.add_argument("--max-chars", dest="max_chars", type=int, default=6000,
                    help="stdout 打印的正文上限，默认 6000；0=全文")
    ap.add_argument("-o", "--out", default="", help="写入该文件")
    ap.add_argument("--json", action="store_true", help="stdout 输出 JSON")
    ap.add_argument("-q", "--quiet", action="store_true", help="只打印标题 + 字数")
    a = ap.parse_args()

    url = a.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return die("URL 必须以 http:// 或 https:// 开头")
    if len(url) > 8192:
        return die("URL 超过 8192 字符")

    key = load_key()
    data, info = fetch(url, key)
    if data is None:
        code, detail = info
        return die(f"抓取失败 —— {detail}\n  URL：{url}", code)

    elapsed = info
    title = (data.get("title") or "").strip()
    content = data.get("content") or ""

    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text((f"# {title}\n\n> 来源：{url}\n\n" if title else f"> 来源：{url}\n\n") + content,
                     encoding="utf-8")
        print(f"已写入 {p}（{len(content)} 字，{elapsed:.2f}s）")
        if not content:
            print("注意：抓到 0 字正文，文件里只有来源信息。", file=sys.stderr)
            return 2
        return 0

    if a.json:
        print(json.dumps({"title": title, "url": url, "elapsed_s": round(elapsed, 2), "content": content},
                         ensure_ascii=False, indent=2))
        return 0

    if not content:
        return die(f"抓到页面但没有正文（{elapsed:.2f}s）—— 换来源或改用浏览器截图 OCR。\n  URL：{url}", 2)

    print(f"标题：{title or '(无)'}")
    print(f"来源：{url}")
    print(f"正文 {len(content)} 字 ｜ 耗时 {elapsed:.2f}s")
    print("-" * 72)
    if a.quiet:
        return 0
    if a.max_chars and len(content) > a.max_chars:
        print(content[: a.max_chars])
        print(f"\n…（已截断，全文 {len(content)} 字；--max-chars 0 看全文，-o 文件.md 存全文）")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
