# -*- coding: utf-8 -*-
"""backup_rotate.py —— 备份保留策略（默认预演）

规则（两条任一满足就保留）：
  ① 最新的 N 个子目录（默认 20）
  ② 最近 M 天内（默认 14）
其余按 `--mode` 处理：`report`（默认，只列）/ `zip`（打包到 backup\\_archive\\）/ `delete`（直接删）

用法：
  python backup_rotate.py                        # 预演，只看会处理哪些
  python backup_rotate.py --keep 30 --days 21     # 改阈值再看
  python backup_rotate.py --mode zip  --apply     # 打包（先打包成功才删原件）
  python backup_rotate.py --mode delete --apply    # 直接删

安全：`legacy\\` 与 `_archive\\` 永不处理；打包模式下**校验 zip 大小 > 0 才删原件**。
"""
import os, sys, io, shutil, zipfile, datetime

APPLY = "--apply" in sys.argv
KEEP = int(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else 20
DAYS = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 14
MODE = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "report"

BK = r"D:\backup"
ARCH = os.path.join(BK, "_archive")
SKIP = {"legacy", "_archive"}
now = datetime.datetime.now()
cutoff = now - datetime.timedelta(days=DAYS)

subs = []
for d in sorted(os.listdir(BK)):
    p = os.path.join(BK, d)
    if not os.path.isdir(p) or d in SKIP:
        continue
    m = datetime.datetime.fromtimestamp(os.path.getmtime(p))
    sz = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(p) for f in fn)
    subs.append({"name": d, "path": p, "mtime": m, "size": sz})

subs.sort(key=lambda x: x["mtime"], reverse=True)
keep, drop = [], []
for i, s in enumerate(subs):
    (keep if (i < KEEP or s["mtime"] >= cutoff) else drop).append(s)

print("=" * 66)
print("🗄️ 备份轮转 · %s · 模式 %s%s" % (now.strftime("%Y-%m-%d %H:%M"), MODE, "" if APPLY else "（预演，不写）"))
print("=" * 66)
print("  保留规则：最新 %d 个 或 最近 %d 天内" % (KEEP, DAYS))
print("  总计 %d 个｜保留 %d 个｜待处理 %d 个（%.2f GB）" % (
    len(subs), len(keep), len(drop), sum(s["size"] for s in drop) / 2**30))
if drop:
    print("\n  待处理明细：")
    for s in drop:
        print("    %-40s %7.1f MB  %s" % (s["name"][:40], s["size"] / 2**20, s["mtime"].strftime("%m-%d %H:%M")))
if keep:
    print("\n  最近保留的 5 个：")
    for s in keep[:5]:
        print("    %-40s %7.1f MB  %s" % (s["name"][:40], s["size"] / 2**20, s["mtime"].strftime("%m-%d %H:%M")))

if not drop:
    print("\n  无事可做 ✅")
    sys.exit(0)
if MODE == "report" or not APPLY:
    print("\n[预演] 未处理任何文件。要打包用 `--mode zip --apply`，要删除用 `--mode delete --apply`。")
    sys.exit(0)

done = 0
if MODE == "zip":
    os.makedirs(ARCH, exist_ok=True)
    for s in drop:
        z = os.path.join(ARCH, s["name"] + ".zip")
        try:
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
                for dp, dn, fn in os.walk(s["path"]):
                    for f in fn:
                        fp = os.path.join(dp, f)
                        zf.write(fp, os.path.relpath(fp, s["path"]))
            if os.path.getsize(z) > 0:
                shutil.rmtree(s["path"])
                done += 1
                print("  ✅ 打包并删除 %-36s → %s（%.1f MB）" % (s["name"][:36], os.path.basename(z), os.path.getsize(z) / 2**20))
            else:
                print("  ⚠️ zip 为空，保留原目录：", s["name"])
        except Exception as e:
            print("  ❌ %s: %s" % (s["name"], e))
elif MODE == "delete":
    for s in drop:
        try:
            shutil.rmtree(s["path"]); done += 1
            print("  ✅ 已删除", s["name"])
        except Exception as e:
            print("  ❌ %s: %s" % (s["name"], e))
else:
    print("未知模式:", MODE)

print("\n处理完成：%d / %d" % (done, len(drop)))
u = shutil.disk_usage(BK)
print("backup 现在 %.2f GB" % (sum(s["size"] for s in keep) / 2**30 + sum(
    os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(ARCH) for f in fn) / 2**30 if os.path.isdir(ARCH) else sum(s["size"] for s in keep) / 2**30))
