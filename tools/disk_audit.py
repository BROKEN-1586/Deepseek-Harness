# -*- coding: utf-8 -*-
"""disk_audit.py —— 磁盘体检（纯只读）

用法：
  python disk_audit.py                # 体检 D 盘
  python disk_audit.py --root C:\\    # 体检 C 盘
  python disk_audit.py --big 500      # 大文件阈值（MB，默认 800）
  python disk_audit.py --top 20       # 顶层显示个数

输出：磁盘占用 / 顶层目录体量 / 根目录散落文件 / 大文件榜 / 已知缓存点 / 空目录 / 备份区概况
并存一份到 D:\\Clearn\\_diag\\disk-audit.txt
"""
import os, sys, io, shutil, datetime

ROOT = "D:\\"
if "--root" in sys.argv:
    ROOT = sys.argv[sys.argv.index("--root") + 1]
BIG = 800 * 2**20
if "--big" in sys.argv:
    BIG = int(sys.argv[sys.argv.index("--big") + 1]) * 2**20
TOP = 20
if "--top" in sys.argv:
    TOP = int(sys.argv[sys.argv.index("--top") + 1])

out = []
def p(s=""):
    print(s); out.append(s)

def dt(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")

def size(pth):
    s = 0
    for dp, dn, fn in os.walk(pth, onerror=lambda e: None):
        for f in fn:
            try:
                s += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return s

u = shutil.disk_usage(ROOT)
p("=" * 70)
p("💽 磁盘体检 · %s · %s" % (ROOT, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
p("=" * 70)
p("  总 %.1f GB｜已用 %.1f GB（%.0f%%）｜可用 %.1f GB" %
  (u.total / 2**30, u.used / 2**30, 100 * u.used / u.total, u.free / 2**30))

p("\n【1】顶层条目（按体量）")
rows, loose, empties = [], [], []
for n in sorted(os.listdir(ROOT)):
    fp = os.path.join(ROOT, n)
    try:
        st = os.stat(fp)
    except OSError:
        continue
    if os.path.isdir(fp):
        s = size(fp)
        rows.append((s, n, dt(st.st_mtime), sum(len(f) for _, _, f in os.walk(fp))))
        try:
            if not os.listdir(fp):
                empties.append(fp)
        except PermissionError:
            pass
    else:
        loose.append((st.st_size, n, dt(st.st_mtime)))
rows.sort(reverse=True)
for s, n, m, nf in rows[:TOP]:
    p("   %-32s %9.1f GB  %7d 文件  %s" % (n[:32], s / 2**30, nf, m))
rest = sum(r[0] for r in rows[TOP:])
if rest:
    p("   …其余 %d 个目录合计 %.1f GB" % (len(rows) - TOP, rest / 2**30))

p("\n【2】根目录散落文件")
if loose:
    for s, n, m in sorted(loose, reverse=True):
        p("   %-46s %8.2f MB  %s%s" % (n[:46], s / 2**20, m,
                                        "   ← 系统文件，勿动" if n.lower() in ("pagefile.sys", "swapfile.sys", "dumpstack.log.tmp", ".gamingroot", "dumpstack.log") else ""))
else:
    p("   无 ✅")

p("\n【3】大文件榜（> %.0f MB）" % (BIG / 2**20))
big = []
for dp, dn, fn in os.walk(ROOT, onerror=lambda e: None):
    for f in fn:
        fp = os.path.join(dp, f)
        try:
            s = os.path.getsize(fp)
        except OSError:
            continue
        if s > BIG:
            big.append((s, fp))
big.sort(reverse=True)
for s, fp in big[:15]:
    p("   %7.2f GB  %s" % (s / 2**30, fp))
p("   合计 %d 个，%.1f GB" % (len(big), sum(s for s, _ in big) / 2**30))

p("\n【4】已知可清缓存点（需人工确认后清）")
for c in [r"C:\Users\36578\AppData\Local\Temp", r"C:\Windows\Temp",
          r"C:\Users\36578\AppData\Local\npm-cache", r"C:\Users\36578\AppData\Local\pip\Cache",
          r"C:\Users\36578\AppData\Local\uv\cache",
          r"C:\Users\36578\AppData\Local\Google\Chrome\User Data\Default\Cache",
          r"C:\Users\36578\AppData\Local\Microsoft\Edge\User Data\Default\Cache",
          r"C:\Users\36578\AppData\Local\JetBrains\Toolbox\cache\download",
          r"C:\ProgramData\NVIDIA Corporation\NVIDIA app\UpdateFramework\ota-artifacts",
          os.path.join(ROOT, "LeStoreDownload")]:
    if os.path.exists(c):
        p("   %-72s %7.2f GB" % (c.replace("\\", "/")[:72], size(c) / 2**30))

p("\n【5】空目录（顶层 2 层内）")
cnt = 0
for dp, dn, fn in os.walk(ROOT):
    d = dp[len(ROOT):].count(os.sep)
    if d > 2:
        dn[:] = []
        continue
    if not dn and not fn and dp != ROOT:
        p("   " + dp); cnt += 1
        if cnt >= 20:
            p("   …(截断)"); break
if cnt == 0:
    p("   无 ✅")

p("\n【6】备份区")
bk = os.path.join(ROOT, "backup")
if os.path.isdir(bk):
    subs = [(os.path.getmtime(os.path.join(bk, d)), d) for d in os.listdir(bk) if os.path.isdir(os.path.join(bk, d))]
    subs.sort(reverse=True)
    p("   %d 个子目录，%.2f GB" % (len(subs), size(bk) / 2**30))
    if subs:
        p("   最新：%s（%s）｜最早：%s（%s）" % (subs[0][1], dt(subs[0][0]), subs[-1][1], dt(subs[-1][0])))
    p("   👉 保留策略用 `backup_rotate.py`（默认预演）")
else:
    p("   无备份目录")

os.makedirs(r"D:\Clearn\_diag", exist_ok=True)
io.open(r"D:\Clearn\_diag\disk-audit.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n（已存 D:\\Clearn\\_diag\\disk-audit.txt）")
