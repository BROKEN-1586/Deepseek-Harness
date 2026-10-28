# -*- coding: utf-8 -*-
"""md -> PDF（Edge headless）。一份通用工具，同时管住**公式**和**插图**。

特性
----
* 公式：`$...$` / `$$...$$` 用**本地离线 MathJax 3（tex-svg）**渲染成矢量公式，
  不联网、不需要字体文件。渲染前先把公式「保护」成占位符，避免 Markdown
  把 `\\` 转义、把 `_ ^ *` 当强调、把公式里的 `|` 当表格分隔符。
* 插图：Obsidian 的最短路径写法 `![](图片名.png)` / `![[图片名.png]]` 会按
  文件名在候选目录里查找，命中后转 base64 内嵌（PDF 自包含）。
* Obsidian 语法：frontmatter、`[[双链]]`、`> [!note]` callout、`==高亮==`、
  `- [ ]` / `- [x]` 任务框都会顺手处理。
* 版式：A4 纵向（默认）/ 横向（`--landscape`）；`--indent` 段首空两格。
* 成稿自检：用 pymupdf 回读 PDF 文本，出现**裸 `$`**说明公式没渲染，会提示。

用法
----
    python md2pdf.py <src.md> <out.pdf> [标题] [--landscape] [--indent]
    python md2pdf.py --batch <manifest.txt> [--landscape] [--indent]
        清单每行： 源.md|输出.pdf|标题|选项
        标题、选项可省略；选项逗号分隔，可取 landscape / indent / no-indent
    python md2pdf.py --dir <源文件夹> <输出文件夹> [--landscape] [--indent]
    python md2pdf.py --merge <输出.pdf> <src1.md> [src2.md ...] [--landscape] [--indent]

也当模块用：
    import md2pdf
    ok, err = md2pdf.to_pdf(src, out, title='', landscape=False, indent=False)
"""
import base64
import html
import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

from markdown_it import MarkdownIt

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
# 本地离线 MathJax 3（tex-svg：矢量输出、内嵌字形，不依赖网络与字体文件）
MATHJAX = os.path.join(
    r'C:\Users\36578\Desktop\高数笔记\高等数学笔记资源包\高等数学公式速查手册',
    '交互速查网页-离线版', 'mathjax.js')

CSS_PAGE_PORTRAIT = '@page { size: A4 portrait; margin: 14mm 12mm 14mm 12mm; }'
CSS_PAGE_LANDSCAPE = '@page { size: A4 landscape; margin: 10mm 10mm 10mm 10mm; }'

CSS_COMMON = """
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 10.5pt; line-height: 1.5; color: #111; }
p { margin: 5px 0; }
h1 { font-size: 16pt; border-bottom: 2px solid #444; padding-bottom: 3px; margin: 0 0 10px; }
h2 { font-size: 13pt; margin: 14px 0 6px; border-bottom: 1px solid #bbb; }
h3 { font-size: 11.5pt; margin: 10px 0 4px; }
h4 { font-size: 11pt; margin: 9px 0 3px; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; table-layout: auto; }
th, td { border: 1px solid #aaa; padding: 3px 6px; vertical-align: top;
         word-wrap: break-word; overflow-wrap: anywhere; font-size: 9.5pt; }
th { background: #eef1f4; }
tr:nth-child(even) td { background: #fafafa; }
blockquote { border-left: 3px solid #ccc; margin: 6px 0; padding: 2px 10px; color: #333; background: #f7f7f7; }
blockquote p { margin: 3px 0; }
code { background: #f2f2f2; padding: 0 3px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9.5pt; }
pre { background: #f6f8fa; padding: 7px; border-radius: 4px; overflow-wrap: anywhere; white-space: pre-wrap; font-size: 9pt; }
hr { border: 0; border-top: 1px solid #ddd; margin: 10px 0; }
ul, ol { margin: 4px 0 6px; padding-left: 24px; }
li { margin: 2px 0; }
img { max-width: 100%; height: auto; display: block; margin: 8px auto; }
mark { background: #fff2a8; }
mjx-container[display="true"] { margin: 8px 0 !important; }
"""

MATHJAX_CFG = r"""
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    tags: 'none',
    /* 关掉 autoload：它会对 extpfeil/cancel 等宏去 CDN 拉包，离线时请求悬挂，
       整篇公式一个都不渲染（2026-10-10 踩过：\xlongequal 导致两篇笔记全空）。 */
    packages: {'[-]': ['autoload']},
    /* 把可能用到的 autoload 宏就地定义，免得变成红色报错 */
    macros: {
      xlongequal: ['\\overset{#1}{=\\!\\!=}', 1],
      xlongleftarrow: ['\\overset{#1}{\\longleftarrow}', 1],
      xlongrightarrow: ['\\overset{#1}{\\longrightarrow}', 1],
      /* 以下宏本来是 autoload 专门从 CDN 取的；autoload 已关（离线安全），
         改成本地定义，否则会退化成字面文本 `\宏名`（2026-10-14 实测确认）。 */
      boldsymbol: ['\\mathbf{#1}', 1],
      bm: ['\\mathbf{#1}', 1],
      oiint: ['\\mathop{\\bigcirc\\kern-1.05em\\int\\kern-0.55em\\int}', 0],
      oiiint: ['\\mathop{\\bigcirc\\kern-1.05em\\int\\kern-0.55em\\int\\kern-0.55em\\int}', 0],
      arccot: ['\\operatorname{arccot}', 0],
      arcsec: ['\\operatorname{arcsec}', 0],
      arccsc: ['\\operatorname{arccsc}', 0],
      sgn: ['\\operatorname{sgn}', 0],
      cancel: ['#1', 1]
    }
  },
  svg: { fontCache: 'local', displayOverflow: 'linebreak' },
  options: {
    enableMenu: false,
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  },
  startup: { typeset: true }
};
"""

# $$...$$ 优先；其次单个 $...$（不跨行、不被 \ 转义）
MATH_RE = re.compile(
    r'(?<!\\)\$\$(?P<d>.+?)(?<!\\)\$\$'
    r'|(?<!\\)\$(?P<i>[^$\n]+?)(?<!\\)\$',
    re.S)
IMGRE = re.compile(r'<img([^>]*?)\ssrc="([^"]+)"([^>]*?)>', re.S)
IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')


# ---------------------------------------------------------------- Markdown 前处理
def protect_math(text):
    """把数学段换成占位符，返回 (文本, 公式列表)。"""
    math = []

    def _sub(m):
        math.append(m.group(0))
        return '@@MJ%03d@@' % (len(math) - 1)

    return MATH_RE.sub(_sub, text), math


def read_md(path):
    """读 md，去 frontmatter，处理 Obsidian 语法；返回 (预处理文本, 公式列表, 缺失图片列表)。"""
    t = open(path, encoding='utf-8').read()
    if t.startswith('---'):
        m = re.match(r'^---\r?\n.*?\r?\n---\r?\n?', t, re.S)
        if m:
            t = t[m.end():]

    t, math = protect_math(t)
    t = re.sub(r'\[\[([^\]\|]+)\|([^\]]+)\]\]', r'\2', t)     # [[A|B]] -> B
    t = re.sub(r'\[\[([^\]]+)\]\]', r'\1', t)                 # [[A]]   -> A
    t = re.sub(r'!\[\[([^\]\|]+)(\|[^\]]*)?\]\]', r'![](\1)', t)  # ![[a.png]] -> ![](a.png)
    t = re.sub(r'^>\s*\[![a-zA-Z]+\][-+]?\s*', '> ', t, flags=re.M)   # callout
    t = re.sub(r'==([^=\n]+)==', r'<mark>\1</mark>', t)       # 高亮
    t = re.sub(r'^(\s*)[-*]\s+\[ \]\s+', r'\1- ☐ ', t, flags=re.M)    # 任务框
    t = re.sub(r'^(\s*)[-*]\s+\[[xX]\]\s+', r'\1- ☑ ', t, flags=re.M)
    return t, math, []


# ---------------------------------------------------------------- 插图
def _index_images(md_dir):
    """按文件名给候选目录里的图片建索引（先近后远）。"""
    roots = [md_dir,
             os.path.join(md_dir, '99-附件'),
             os.path.join(os.path.dirname(md_dir), '99-附件')]
    idx = {}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for fn in filenames:
                if fn.lower().endswith(IMG_EXT):
                    idx.setdefault(fn, os.path.join(dirpath, fn))
    return idx


def _data_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    mime = {'jpg': 'jpeg', 'svg': 'svg+xml'}.get(ext, ext)
    with open(path, 'rb') as f:
        return 'data:image/%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


def inline_images(html_text, md_dir):
    """把 <img src="图片名.png"> 换成 base64 内嵌；返回 (HTML, 缺失图片名列表)。"""
    idx = _index_images(md_dir)
    missing = []

    def _sub(m):
        head, src, tail = m.group(1), m.group(2), m.group(3)
        if src.startswith(('data:', 'http://', 'https://')):
            return m.group(0)
        # markdown-it 会把 src 做百分号编码（中文文件名变 %E5%8F%8C…），先还原
        cand = idx.get(os.path.basename(unquote(src))) or (
            src if os.path.isabs(src) and os.path.exists(src) else None)
        if not cand or not os.path.exists(cand):
            missing.append(src)
            return m.group(0)
        return '<img%s src="%s"%s>' % (head, _data_uri(cand), tail)

    return IMGRE.sub(_sub, html_text), missing


# ---------------------------------------------------------------- HTML
def md_to_html(md_text, math, title='', landscape=False, indent=False, md_dir=None):
    md = MarkdownIt('commonmark')
    md.enable(['table', 'strikethrough'])
    body = md.render(md_text)
    body = re.sub(r'@@MJ(\d{3})@@', lambda m: html.escape(math[int(m.group(1))]), body)
    missing = []
    if md_dir:
        body, missing = inline_images(body, md_dir)
    css = (CSS_PAGE_LANDSCAPE if landscape else CSS_PAGE_PORTRAIT) + CSS_COMMON
    if indent:
        css += '\np { text-indent: 2em; }'
    return ('<!doctype html><html lang="zh"><head><meta charset="utf-8">\n'
            '<title>%s</title><style>%s</style>\n<script>%s</script>\n'
            '<script src="file:///%s"></script>\n</head><body>%s</body></html>'
            % (html.escape(title), css, MATHJAX_CFG, MATHJAX.replace('\\', '/'), body),
            missing)


# ---------------------------------------------------------------- 出 PDF
def to_pdf(src, out, title='', landscape=False, indent=False):
    """把 src.md 转成 out.pdf。返回 (是否成功, 提示信息)。"""
    if not os.path.exists(src):
        return False, '源文件不存在：%s' % src
    md_text, math, _ = read_md(src)
    md_dir = os.path.dirname(os.path.abspath(src))
    if not title:
        m = re.search(r'^#\s+(.+)$', md_text, re.M)
        title = m.group(1).strip() if m else os.path.basename(src)
    html_str, missing = md_to_html(md_text, math, title, landscape, indent, md_dir)

    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='md2pdf_')
    hp = os.path.join(tmpdir, 'doc.html')
    with open(hp, 'w', encoding='utf-8') as f:
        f.write(html_str)
    if os.path.exists(out):
        try:
            os.remove(out)
        except OSError:
            pass
    cmd = [EDGE, '--headless=new', '--disable-gpu', '--no-first-run',
           '--disable-extensions', '--virtual-time-budget=30000',
           '--run-all-compositor-stages-before-draw',
           '--user-data-dir=' + os.path.join(tmpdir, 'prof'),
           '--no-pdf-header-footer', '--print-to-pdf=' + out,
           'file:///' + hp.replace('\\', '/')]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=300)
    if not (os.path.exists(out) and os.path.getsize(out) > 1000):
        return False, 'Edge 没出 PDF：' + (r.stderr or '')[-300:]

    warn = []
    if missing:
        warn.append('缺图片 %d 张：%s' % (len(missing), ','.join(sorted(set(missing))[:4])))
    try:                                    # 成稿自检：文本里还有裸 $ 就是公式没渲染
        import pymupdf
        d = pymupdf.open(out)
        txt = ''.join(p.get_text() for p in d)
        pages = d.page_count
        if '$' in txt:
            warn.append('⚠️ 检出裸 $ —— 公式可能没渲染，回头查一下')
        d.close()
    except Exception:
        pages = -1
    return True, 'pages=%s%s' % (pages, ('  ' + '; '.join(warn)) if warn else '')


def merge_pdfs(out, srcs, **kw):
    """多个 md 各自转 PDF 后合成一本（每个文件从新页开始，不插分隔页）。"""
    import pymupdf
    parts = []
    tmpdir = tempfile.mkdtemp(prefix='md2pdf_merge_')
    for i, s in enumerate(srcs):
        p = os.path.join(tmpdir, '%02d.pdf' % i)
        ok, err = to_pdf(s, p, **kw)
        if not ok:
            return False, '%s -> %s' % (s, err)
        parts.append(p)
    doc = pymupdf.open()
    for p in parts:
        src = pymupdf.open(p)
        doc.insert_pdf(src)
        src.close()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    doc.save(out)
    pages = doc.page_count
    doc.close()
    return True, '合并 %d 个文件 / %d 页' % (len(parts), pages)


# ---------------------------------------------------------------- CLI
def _flags(argv):
    kw = {'landscape': False, 'indent': False}
    rest = []
    for a in argv:
        if a == '--landscape':
            kw['landscape'] = True
        elif a == '--indent':
            kw['indent'] = True
        elif a == '--portrait':
            kw['landscape'] = False
        else:
            rest.append(a)
    return rest, kw


def _opt_field(opts, kw):
    """清单第 4 列的选项 → 覆盖本次设置。"""
    k = dict(kw)
    for o in opts.split(','):
        o = o.strip()
        if o == 'landscape':
            k['landscape'] = True
        elif o == 'portrait':
            k['landscape'] = False
        elif o == 'indent':
            k['indent'] = True
        elif o == 'no-indent':
            k['indent'] = False
    return k


def main(argv):
    args, kw = _flags(argv)
    if not args:
        print(__doc__)
        return 0

    if args[0] == '--batch':
        lines = [l.strip() for l in open(args[1], encoding='utf-8-sig') if l.strip()]
        bad = 0
        for l in lines:
            parts = l.split('|')
            src, out = parts[0].strip(), parts[1].strip()
            title = parts[2].strip() if len(parts) > 2 else ''
            k = _opt_field(parts[3], kw) if len(parts) > 3 else kw
            ok, err = to_pdf(src, out, title, **k)
            bad += 0 if ok else 1
            print(('OK   ' if ok else 'FAIL ') + out + ('  ' + err if err else ''), flush=True)
        print('--- %d 个，失败 %d 个' % (len(lines), bad))
        return 1 if bad else 0

    if args[0] == '--dir':
        in_dir, out_dir = args[1], args[2]
        mds = sorted(f for f in os.listdir(in_dir) if f.lower().endswith('.md'))
        bad = 0
        for f in mds:
            ok, err = to_pdf(os.path.join(in_dir, f),
                             os.path.join(out_dir, os.path.splitext(f)[0] + '.pdf'), **kw)
            bad += 0 if ok else 1
            print(('OK   ' if ok else 'FAIL ') + f + ('  ' + err if err else ''), flush=True)
        print('--- %d 个，失败 %d 个' % (len(mds), bad))
        return 1 if bad else 0

    if args[0] == '--merge':
        ok, err = merge_pdfs(args[1], args[2:], **kw)
        print(('OK   ' if ok else 'FAIL ') + args[1] + '  ' + err)
        return 0 if ok else 1

    src, out = args[0], args[1]
    title = args[2] if len(args) > 2 else ''
    ok, err = to_pdf(src, out, title, **kw)
    print(('OK   ' if ok else 'FAIL ') + out + ('  ' + err if err else ''))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
