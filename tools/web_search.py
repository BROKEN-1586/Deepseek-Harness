#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""web_search.py —— DeepSeek 自研搜索引擎（POST /v1/tools/search）

本机直连外网不稳，但 api.deepseek.com 实测稳定（2026-10-23：1.0 秒返回）。
所以联网查资料的口径是：**先 DeepSeek 直连 → 失败再 Tavily**。

用法：
  python web_search.py "DeepSeek V4 发布"                    # 搜 8 条（默认）
  python web_search.py "矩阵的秩" -n 5 --content             # 顺带抓正文
  python web_search.py "DeepSeek" --site github.com --after 2025
  python web_search.py "精确短语" --exact --lang zh,en
  python web_search.py "..." --min-score 1.5                 # 只留优质结果（≥1.5）
  python web_search.py "..." -o D:\\tmp\\res.md              # 存文件（.md / .json 看后缀）
  python web_search.py "..." --json                          # stdout 输出 JSON（给程序吃）

参数：
  -n/--count        返回条数 1~50，默认 8
  --content         need_content=true（在结果里返回网页正文，单条可能几千字）
  --ori-question    原始问题（帮助理解搜索意图，1~128 字）
  --site            限定站点，可重复 / 逗号分隔 → site:a OR site:b
  --exclude-site    排除站点，可重复 / 逗号分隔
  --exclude         排除关键词，可重复 → -词
  --exact           把 query 当精确短语（"..."）
  --lang            限定语言，如 zh,en
  --after/--before  发布时间限制，如 2025 或 2025-01-01
  --min-score       只保留 rerank_score ≥ 该值的结果（≥1.5 为优质）
  --min-authority   只保留 authority ≥ 该值的结果（≥3 为极权威）
  --full-summary    打印完整长摘要（默认截到 400 字）
  -o/--out          写入文件；后缀 .json = 原始 JSON，其它 = Markdown
  --json            stdout 打印 JSON
  -q/--quiet        只打印标题 + URL

退出码：0 成功 / 1 参数或网络错误 / 2 搜索无结果
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

API = "https://api.deepseek.com/v1/tools/search"
KEYS = Path(r"D:\AgentData\keys.json")
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


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


def build_query(a):
    q = f'"{a.query}"' if a.exact else a.query
    if a.site:
        q += " " + " OR ".join(f"site:{s}" for s in a.site)
    if a.exclude_site:
        q += " " + " ".join(f"-site:{s}" for s in a.exclude_site)
    if a.exclude:
        q += " " + " ".join(f"-{w}" for w in a.exclude)
    if a.lang:
        q += f" lang:{a.lang}"
    if a.after:
        q += f" after:{a.after}"
    if a.before:
        q += f" before:{a.before}"
    return q


def post(url, key, payload, timeout=45):
    import requests

    last = None
    for i in range(3):
        t0 = time.time()
        try:
            r = requests.post(
                url,
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(1.5 * (i + 1))
            continue
        if r.status_code == 200:
            return r.json(), time.time() - t0
        if r.status_code in RETRY_STATUS and i < 2:
            last = f"HTTP {r.status_code}（重试中）"
            time.sleep(2.0 * (i + 1))
            continue
        msg = ""
        try:
            msg = r.json().get("error", {}).get("message", "")
        except Exception:
            msg = (r.text or "")[:200]
        return None, f"HTTP {r.status_code}：{msg}"
    return None, last or "未知错误"


def split_csv(vals):
    out = []
    for v in vals or []:
        out.extend(x.strip() for x in v.split(",") if x.strip())
    return out


def render_text(a, query, results, elapsed):
    lines = []
    tail = []
    if a.content:
        tail.append("含正文")
    lines.append(f"搜索：{query}")
    meta = f"结果 {len(results)} 条 ｜ 耗时 {elapsed:.2f}s"
    if tail:
        meta += " ｜ " + "、".join(tail)
    lines.append(meta)
    lines.append("-" * 72)
    for i, r in enumerate(results, 1):
        score = r.get("rerank_score")
        auth = r.get("authority")
        badges = []
        if isinstance(score, (int, float)) and score >= 1.5:
            badges.append("★优质")
        if isinstance(auth, (int, float)) and auth >= 3:
            badges.append("◆权威")
        head = f"[{i}] {r.get('title') or '(无标题)'}"
        if badges:
            head += "  " + "".join(badges)
        lines.append(head)
        bits = []
        if isinstance(score, (int, float)):
            bits.append(f"相关 {score:.2f}")
        if isinstance(auth, (int, float)) and auth >= 0:
            bits.append(f"权威 {auth}")
        if r.get("date"):
            bits.append(str(r["date"])[:10])
        if r.get("site_name"):
            bits.append(str(r["site_name"]))
        if bits:
            lines.append("    " + " ｜ ".join(bits))
        lines.append("    " + (r.get("url") or ""))
        summ = (r.get("summary") or r.get("snippet") or "").replace("\n", " ").strip()
        if summ and not a.quiet:
            if not a.full_summary and len(summ) > 400:
                summ = summ[:400] + "…"
            lines.append("    " + summ)
        body = r.get("content") or ""
        if body:
            lines.append(f"    〔正文 {len(body)} 字〕")
        lines.append("")
    return "\n".join(lines)


def render_md(a, query, results, elapsed):
    out = [f"# 搜索：{query}", "", f"> 结果 {len(results)} 条 ｜ 耗时 {elapsed:.2f}s ｜ {time.strftime('%Y-%m-%d %H:%M')}", ""]
    for i, r in enumerate(results, 1):
        out.append(f"## {i}. {r.get('title') or '(无标题)'}")
        out.append("")
        meta = []
        if isinstance(r.get("rerank_score"), (int, float)):
            meta.append(f"相关 {r['rerank_score']:.2f}")
        if isinstance(r.get("authority"), (int, float)):
            meta.append(f"权威 {r['authority']}")
        if r.get("date"):
            meta.append(str(r["date"])[:10])
        if r.get("site_name"):
            meta.append(str(r["site_name"]))
        if meta:
            out.append("- " + " ｜ ".join(meta))
        out.append(f"- {r.get('url')}")
        out.append("")
        if r.get("summary"):
            out += [r["summary"].strip(), ""]
        if r.get("content"):
            out += [r["content"].strip(), ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(add_help=True, description="DeepSeek 网页搜索")
    ap.add_argument("query", help="搜索词（1~128 字）")
    ap.add_argument("-n", "--count", type=int, default=8, help="返回条数 1~50，默认 8")
    ap.add_argument("--content", action="store_true", help="返回网页正文")
    ap.add_argument("--ori-question", dest="ori_question", default=None)
    ap.add_argument("--site", action="append", default=[], help="限定站点，可重复/逗号分隔")
    ap.add_argument("--exclude-site", dest="exclude_site", action="append", default=[], help="排除站点")
    ap.add_argument("--exclude", action="append", default=[], help="排除关键词")
    ap.add_argument("--exact", action="store_true", help="精确短语匹配")
    ap.add_argument("--lang", default="", help="限定语言，如 zh,en")
    ap.add_argument("--after", default="", help="该日期之后，如 2025 或 2025-01-01")
    ap.add_argument("--before", default="", help="该日期之前")
    ap.add_argument("--min-score", dest="min_score", type=float, default=None)
    ap.add_argument("--min-authority", dest="min_authority", type=float, default=None)
    ap.add_argument("--full-summary", dest="full_summary", action="store_true")
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--json", action="store_true", help="stdout 打印 JSON")
    ap.add_argument("-q", "--quiet", action="store_true", help="只打印标题 + URL")
    a = ap.parse_args()

    q = a.query.strip()
    if not q or len(q) > 128:
        return die("query 需为 1~128 个非空白字符")
    if not (1 <= a.count <= 50):
        return die("count 需在 1~50 之间")

    key = load_key()
    query = build_query(a)
    payload = {"query": query, "count": a.count, "need_content": bool(a.content)}
    if a.ori_question:
        payload["ori_question"] = a.ori_question

    data, info = post(API, key, payload)
    if data is None:
        return die(f"搜索失败 —— {info}")
    elapsed = info
    results = data.get("results") or []

    if a.min_score is not None:
        results = [r for r in results if (r.get("rerank_score") or 0) >= a.min_score]
    if a.min_authority is not None:
        results = [r for r in results if (r.get("authority") or 0) >= a.min_authority]

    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() == ".json":
            p.write_text(
                json.dumps({"query": query, "elapsed_s": round(elapsed, 2), "results": results},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            p.write_text(render_md(a, query, results, elapsed), encoding="utf-8")
        print(f"已写入 {p}（{len(results)} 条）")
        if a.json:
            print(json.dumps({"query": query, "elapsed_s": round(elapsed, 2), "results": results},
                             ensure_ascii=False, indent=2))
        return 0 if results else 2

    if a.json:
        print(json.dumps({"query": query, "elapsed_s": round(elapsed, 2), "results": results},
                         ensure_ascii=False, indent=2))
        return 0 if results else 2

    if not results:
        print(f"搜索「{query}」无结果（{elapsed:.2f}s）—— 换个词或去掉限定条件再试。")
        return 2
    print(render_text(a, query, results, elapsed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
