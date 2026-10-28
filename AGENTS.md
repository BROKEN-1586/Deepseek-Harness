# 项目说明书（入口 · 框架无关）

> ⚠️ **本文件是「入口」，不是「真身」。**
> **真身**：`D:\Clearn\DEEPCODE.md`（一直在维护，**不要在这里重复规则内容**）。
> 🦢 当前运行框架 = **Goose**（2026-10-08 确认）。　🏷️ **当前版本：Alpha 0.5.0** —— 真身 `D:\Clearn\VERSION`（单行）＋ 历史 `CHANGELOG.md`。**每次有效改动都要升号**（用户 2026-10-28 定，规则见 `DEEPCODE.md`「🏷️ 版本号规则」；一个任务一只号、没验证不升、汇报第一行报版本）

## 🔴 第一步（每次会话都做，别跳）

读 `D:\Clearn\DEEPCODE.md` **最前面的约 105 行（A → E 整屏，读完 §E 才算完）** —— 那里是「硬性要求速查 + 任务路由 + 收尾清单 + 每日流程」（2026-10-11 建，2026-10-20 扩到 §E），把「漏了就出错」的要求全列齐了：

1. **六条铁律在哪里**（第一条 Bash 可用 / 第二条 长文件只用 `safe_edit` / 第四条 改动前审批 / 第五条 收尾必写备案 / 第六条 单文件也套文件夹）
2. **「不许」清单**——用户定过的口径：不写非知识内容、**新建 `.md` 前先通知用户**（2026-10-14 改）、词汇必带音标、别用 MCP `rebuild_index`、别先直连联网、别用 `read_image` 批量读图、待办不进 DEEPCODE……
3. **任务 → 该读哪节**（路由表：不需要通读 1000 行）；**遇到坑 / 查「这问题以前怎么解的」→ 📋 `D:\Clearn\问题汇总\问题汇总.md`**（问题 → 措施 → 来源）
4. **收尾 6 步**：挂索引 → 重建索引（最后只建一次）→ 检索探针 → 写备案（直接写，不问）→ **升版本号**（有有效改动才升，写 `VERSION` ＋ `CHANGELOG.md`）→ 汇报（**第一行报版本号**）

读完按路由表**只读本任务需要的节**。**条文冲突时以 DEEPCODE.md 各节正文为准**（速查是导航层，可能滞后）。

> 为什么这样设计：2026-10-11 用户指出「经常读漏要求」。旧版把要求散在 1000+ 行里、铁律又首尾各一半，所以现在把入口压到 60 行内。

## 🔴 会话一开始就跑「每日流程」（用户 2026-10-20 定：**自动，不用问**）

读完上面速查，**第一件事就是它**，别等用户开口：

0. **先跑机器判据**（约 1 秒）：`python D:\Clearn\tools\daily_gate.py` → 读 `D:\Clearn\_diag\daily-gate.txt` 的 **`VERDICT`** 行：
   - `FULL` → 跑完整版；`LITE` → 跑轻量版（① 合并预演 ② 扫未勾项 ③ 一句话 ＋ 问「要不要补跑完整版」）
   - 它同时给出**未勾条数（今天/昨天）、镜像是否一致、≤3 天或逾期风险** —— **别自己数，以它为准**。
   - 兜底判据（脚本跑不了时）：~~旧日记 / 旧作业快照路径~~ **⛔ 2026-10-28 作废** —— 旧库 `D:\日程规划` 已删、`02-按日期` 快照已取消，那两个路径**永远不存在**，按它判只会永远得出「没跑过」。**改为直说卡在哪一步**（报错原文 ＋ 已确认到的状态），**不要靠猜路径**判「今天跑没跑」，也不要把流程跑两遍。
1. **合并**：`merge-sync` recipe 预演（两侧勾选取并集）；有「镜像独有 / 内容差异」先列条目。
2. **读素材**：`delegate(source: "read-the-night")` —— **子代理跑**，截图 / 课件不要灌进主上下文；超时给足（`max_turns` ≥ 60）。
3. **核对**：把作业（科目 / 任务 / 截止 / 出处）＋ 顺延项**列表给用户**，点头才落盘（2026-10-14 定）。
4. **汇报三件**：今天新作业 N 条 ／ 顺延未完成 N 条 ／ 风险（≤3 天或已逾期）。

- 🔴 **例外（2026-10-28 定）：由 MCP / `goose run -q --no-session` 调进来的一次性任务，不跑每日流程。** 那类调用背后没有人在等你汇报，跑一遍只会白烧几分钟 token、甚至误动任务清单 —— 直接做 task 里交代的事就行。判据：任务是从 `mcp__goose__run`（外部入口）传来的、没有会话上下文。
- 用户说「跳过早间流程」→ 本次不跑，但回复里要提一句「今天还没跑」。
- 失败 / 超时：先查有没有部分落盘（文件 mtime、`_backup` 目录），**别重跑当没发生**，说清卡在第几步。
- 详情：`DEEPCODE.md` §E 会话启动：每日流程。

## 🔴 2026-10-27 结构变更（先看这条）

- 旧 `D:\日程规划` 库 **已删**；**不再每天建笔记**（日记 / 每日作业快照全部取消）。
- 新库 **`D:\任务清单`**：`01-作业清单`（作业大类，6 池）＋ `02-教务清单`（考试节点 / 课程信息 / 学习计划 / 考前考后 / 证明 / 其它）＋ `00-总览\00-任务总览.md`。
- 镜像：`Obsidian\92-任务清单`（旧的 `92-作业清单` 已改名、`93-日程规划` 已删）。
- 会话开场的每日流程判据 → `python D:\Clearn\tools\daily_gate.py`（FULL = 今天有新课件/作业来源；LITE = 没有）。
- 完整换算表见 `DEEPCODE.md`「🔴 结构变更（2026-10-27）」一节。

## 本文件只做三件事

1. 告诉你去读哪里（上一步）
2. 标注哪些规则是 **DeepCode 专属**、换框架后不适用（下表）
3. 给**框架无关的服务 / 路径速查**（完整版在 DEEPCODE.md）

## ⚠️ 框架适配：原 DeepCode 规则 → Goose 现状

| DEEPCODE.md 里的规则 | 现状 |
|---|---|
| 第一条铁律：不要调用 Bash | ✅ **已作废**——那是 DeepCode 自己的安全协议。Goose 的 shell 完全可用，直接跑 |
| `!` 前缀执行 cmd | ⚫ **不适用**——那是 DeepCode TUI 的功能；Goose 用 shell 工具 |
| 用 `mcp__obsidian-rag__safe_*` 工具 | ✅ **工具名去掉 `mcp__` 前缀**：`obsidian-rag__safe_read` / `safe_edit` / `safe_append` / `safe_replace_section` |
| 删文件要用户 `!del` | ⚫ **不适用**（Goose 可直接删）；但**删前仍按第四条铁律先问** |
| `Write` 静默截断 | ⚠️ **口径保留（保守）**：>100 行仍走 `safe_edit`，不整篇 Write |

## 服务与路径速查（完整清单见 DEEPCODE.md）

| 项 | 值 |
|---|---|
| RAG 服务（OpenAI 兼容） | `http://127.0.0.1:8001`；**开机自启** = 计划任务 `RAGServerAutoStart` ＋ 启动项「RAG 与 Ollama 自检」→ `D:\rag\boot-rag.ps1`（幂等：先保 Ollama 11434、再保服务 8001，日志 `D:\rag\boot-rag.log`）；手动 `start.bat`，排障 `restart-rag.bat` |
| MCP 桥接 | `D:\rag\mcp_rag_bridge.py` |
| 知识库（9 个） | math-rag / sec-rag / game-rag / note-rag / ai-rag / csapp-rag / novel-rag / archive-rag / **aiout-rag**（AI 产出） |
| Python | `C:\Users\36578\AppData\Local\Programs\Python\Python314\python.exe` |
| Obsidian 笔记库 | `C:\Users\36578\Nutstore\1\我的坚果云\Obsidian\<NN-库名>\`（每个子文件夹是独立库，带 `.obsidian`） |
| 任务清单库（**非 RAG**） | `D:\任务清单\`（`01-作业清单` ＋ `02-教务清单`＋`00-总览`）—— 旧 `D:\日程规划` **已删**（2026-10-27） |
| 记忆 / 备案 | `D:\AgentData\memory\`（索引 `MEMORY.md`） |
| 固定流程 recipes | `D:\Clearn\.goose\recipes\`（8 个：rag-rebuild / note-pipeline / read-the-night / weekly-review / **merge-sync** / **img-ingest** / **closeout** / **export-note**；2026-10-28 全量 `goose recipe validate` **8/8 通过**） |
| 问题 / 踩坑汇总 | `D:\Clearn\问题汇总\问题汇总.md`（问题 → 措施 → 来源，分 5 区；**非 RAG，改动不需重建索引**） |

## 常用脚本

| 脚本 | 作用 |
|---|---|
| `D:\rag\rag_server.py` | RAG 主服务（`--serve` / `--build <库> --force`） |
| `D:\rag\rebuild-one.bat <库名>` | 重建单个库（⚠️ 末尾有 `pause`，无人值守时直接跑 `python rag_server.py --build`） |
| `D:\AutoPrep\study_planner.py` | 学习规划（定时任务已停用，需时手动跑 `morning` / `evening`） |
| `D:\AutoPrep\weekly_review.py` | 周报 |
| `D:\Clearn\tools\md2pdf.py` | 笔记 → PDF（离线 MathJax，公式 + 插图） |
| `D:\Clearn\tools\merge_and_sync.py` | **合并「真身 ↔ Obsidian 镜像」的勾选**（取并集、补 `✅ 时间`）并同步；默认预演，加 `--apply` 才写 |
| `D:\Clearn\tools\daily_gate.py` | **每日流程的机器判据**：跑一次写 `_diag\daily-gate.txt`（VERDICT = FULL/LITE ＋ 未勾数 ＋ 镜像是否一致 ＋ ≤3 天风险）；会话开场第一件事读它。`chcp 65001` + `PYTHONIOENCODING=utf-8` 再跑，约 1 秒 |
| `D:\Clearn\tools\web_search.py` | **联网搜索首选**（DeepSeek 官方 Search 直连，实测 0.2~1 秒）：`"词" -n 5 --content --site xxx.com --after 2025`；`-o x.md`/`.json` 存文件，`--json` 给程序吃 |
| `D:\Clearn\tools\web_fetch.py` | **抓单个网页首选**（DeepSeek Fetch 直连）：`web_fetch.py <url> --max-chars 6000 -o x.md`；失败再退 `tavily_extract` |
| `D:\Clearn\tools\stamp_backfill.py` | 给历史 `- [x]` 条目统一补时间标记（`（时间未记录）` / `✅ 日期未记录`）；默认预演 |
| `D:\Clearn\tools\tasks_syntax.py` | 给带截止的顶层任务行补 **Tasks 插件**到期日 `📅 YYYY-MM-DD`（作业池 ＋ 教务页，旧口径写作「作业清单 + 日程规划」）；默认预演 |
| `D:\Clearn\tools\ai_archive.py` | **AI 产出归档**（`Desktop\AI产出\`）：每版一个 `<日期>-vN` 目录 ＋ `改了什么.md` ＋ 两层索引（项目 `00-索引.md` / 根总表）；`new` / `add` / `list` / `show` / `diff` / `restore` / `retire`，默认预演；**落盘后自动重建 `aiout-rag`**（`--no-rebuild` 跳过） |
| `D:\Clearn\tools\reorg_desktop.py` | 桌面四区（临时文件/教材/重要文件/课程）重构脚本：145 条显式移动表，默认预演，`--apply` 前写 `D:\backup\reorg-<ts>\manifest.json` 快照；**只移动不删除** |
| `D:\Clearn\tools\jpg2pdf.py` | **图片 → 一个 PDF**（2026-10-26 建）：按文件名数字自然序排，`--page a4`（默认，A4 版式不裁切）/ `fit`（页面随图），PyMuPDF 直塞 JPEG 不重编码；`--recurse` / `--key 正则` |
| `D:\Clearn\tools\cw_extract.py` | **课件 → 纯文字**（2026-10-26 建，写课件笔记用）：PDF 走 pymupdf `blocks` 按 `(round(y/6), x)` 排序重排（原始 `get_text` 碎片流读不通），PPTX 直接解 `slideN.xml` 的 `<a:t>`；产物落 `D:\Clearn\_diag\courseware\<tag>.txt`，**不读图、不 OCR** |
| `D:\Clearn\tools\cet4_shengci_flow.py` | **四级生词三级流转**（2026-10-27 建）：`02-陌生` 带 `#` → `01-不熟悉`、`01-不熟悉` 带 `#` → `00-已掌握`，移完去掉 `#`、两表重排序号；`###`/`###N` 进度锚点自动忽略；先备份再写 |
| `D:\Clearn\tools\cet4_vocab_marks.py` | **四级词汇标记汇总**（2026-10-27 建）：扫 `01-词汇\NN-核心词汇-*.md` 里的 `#`/`##`（词末 `#`→不熟悉、`##`→陌生；释义内 `#`→义项不熟、`##`→整词陌生），去重后追加进 `05-生词` 三态表，满 100 自动拆篇；默认预演，`--apply` 才写 |
| `D:\Clearn\tools\followup.py` | **同步跟进体检**（2026-10-27 建，**纯只读、不改任何文件**）：一次出七块——作业（逾期 / ≤3 天 / 只剩提交，天数按今天重算）、素材缺口（有课件但那天没清单快照）、镜像一致性（内部跑 `merge_and_sync` 预演）、四级（三态词数 / 待流转 / 倒计时）、RAG 索引新鲜度、最新备份、时间基准自检；结果同时落 `_diag\followup.txt`。双击 `followup.bat`，或直接说「跟进一下」 |
| `D:\Clearn\tools\syncflow.py` | **同步跟进（连锁改写）**（2026-10-27 建）：**你改了什么，它把连带文件一次改到位** —— ①`05-生词` 三态流转 ②`01-词汇` 标记汇总（满 100 拆篇）③作业池剩余天数重算 ＋ 已完成折叠 ＋ `updated` ④历史快照**只报告不改**（`--fix-snapshots` 才写）⑤总览词数/按日期表 ⑥真身→Obsidian 镜像（`--apply` 时）⑦索引新鲜度（`--rebuild-index` 才真重建）。**默认预演，`--apply` 才写**，写前全进 `D:\backup\syncflow-<ts>\` |
| `D:\Clearn\tools\annotate_folders.py` | **给文件夹写悬停注释**（2026-10-27 建）：在目标目录写 `desktop.ini` 的 `[.ShellClassInfo] InfoTip=`（UTF-16 带 BOM ＋ 隐藏/系统属性 ＋ 目录置只读），资源管理器悬停即显示功能说明；**可逆**（删 desktop.ini 即还原）；`Program Files` / `WindowsApps` / `$RECYCLE.BIN` 等无权限目录自动跳过 |
| `D:\Clearn\tools\hw_snapshot.py` | **⛔ 已退役（2026-10-27 起不再每天建快照，仅保留备查）** —— 原功能：生成当日作业清单快照：从 `01-按科目\` 抽未完成条目，四行式搬运 ＋ 「顺延自 X，连顺 N 天」，天数**按快照日期**算；写 `02-按日期\<日期>-作业清单.md` 并把日期补进 `00-作业总览`；默认预演，`--apply` 才写，`--date` 指定日期，已存在需 `--force` |
| `D:\Clearn\tools\hw_from_courseware.py` | **课件首页作业页 → 候选条目**（2026-10-27 建）：扫 `01-课件\*\<日期>\` 或 `--file`，取 PDF/PPTX **前 3 页**抓「作业/习题」行，按内容判科目；**默认只打印候选**（符合「落盘前核对」），`--apply` 才写进作业池（截止标「待确认」、按课件出处去重） |
| `D:\Clearn\tools\disk_audit.py` | **磁盘体检**（2026-10-27 建，**纯只读**）：占用/顶层体量榜/根目录散落文件/大文件榜（`--big` 阈值）/已知缓存点/空目录/备份区概况；`--root` 换盘、`--top` 控行数；结果落 `_diag\disk-audit.txt` |
| `D:\Clearn\tools\backup_rotate.py` | **备份保留策略**（2026-10-27 建）：保留「最新 N 个（默认 20）**或** 最近 M 天（默认 14）」，其余可 `--mode zip`（打包校验非空才删原件）/ `--mode delete`；**默认 report 预演**；`legacy\`、`_archive\` 永不处理 |
| `D:\Clearn\tools\goose_mcp.py` | **把 goose 包成 MCP server**（2026-10-28 建）：暴露 `run` / `recipes` / `info` 三个工具，底层 `goose run -q --no-session --output-format json`；供 DSH 等外部入口调用。**守卫层归 DSH**（危险命令拦截 / workdir 白名单 / max_turns 上限 / 审计 `_diag\goose-audit.tsv`，见 DEEPCODE「🛡️ goose 执行守卫」） |
| `D:\Clearn\tools\dsh_mcp_preflight.py` | **DSH 侧 MCP 只读验收探针**（2026-10-28 建）：读 `cordis.patch.yml` 的 `insert:` 块，用最坏环境（无 `APPDATA` / `cwd=C:\Windows` / PATH 只剩 system32）真握手 `initialize → tools/list → tools/call`；DSH 升级后重跑即可 |
| `D:\Clearn\tools\daily_0730.bat` | **每天 07:30 的零 token 体检**（2026-10-28 建）：计划任务 `ClearnDailyGate` 调用，顺序跑 `daily_gate.py` ＋ `followup.py`，日志追加 `_diag\daily-0730.log`；已内置 `chcp 65001` ＋ `PYTHONIOENCODING=utf-8` |
| `D:\Clearn\tools\release.py` | **工具版本库**（2026-10-28 建）：把 `tools\` 下的脚本按**四通道**（alpha 开发中 / beta 优化中 / stable 稳定 / ultra 最终版）发布成 `releases\<工具>\<通道>-<版本>\` 快照 ＋ git commit ＋ tag；`publish` / `baseline` / `list` / `verify`，默认预演，`--apply` 才写。**归 goose 维护**（2026-10-28 用户定；DSH 只读，改动走 goose） |
| `.git`（仓库根 `D:\Clearn`） | **版本留痕**（2026-10-28 建）：只入库规则 / 脚本 / 版本记录，`_diag`、`_backup*`、`_work`、`tools\_retired` 忽略；`.gitattributes` 写 `* -text` 保字节原样（仓库混有 CRLF 规则与 LF 脚本两种行尾） |

> 以上脚本全是用户自己写的，不是框架自带。API key 已从 DeepCode 配置挪到 `D:\AgentData\keys.json`（4 处硬编码早已改完）。

## 🚪 入口分工与边界（goose ↔ DSH，2026-10-28 定）

> **一套资产层（文件 ＋ MCP ＋ 记忆）＋ 两个专用入口**：goose 管「已验证能力」，DSH（DeepSeek Harness）管「孵化未定型能力」。任一个入口停更，资产不丢。
> **默认各干各的**，只有「跨调口径」那三类才交给对方；**重叠区禁令**：同一件事只允许一个入口实现，换归属要先删旧的再建新的，不许并存。

| 域 | 归属 | 产物落点 | **禁做** |
|---|---|---|---|
| 笔记整理、Obsidian 库、RAG 重建 | **goose** | `Obsidian\<NN-库名>\` | DSH 不改笔记库 |
| 本机脚本 / 计划任务 / 备份 / 任务清单同步 | **goose** | `D:\Clearn\tools\`、`D:\任务清单` | DSH 不改 `tools\*.py` |
| 文档 / PPT / 表格生成与转换 | **DSH**（Office 技能） | 中立输出目录（逐个约定） | goose 不许为「也能做」再写一套 |
| 新能力试验（需求还不定型） | **DSH** | 同上 ＋ 孵化记录 | 不许在 DSH 里积累只有 DSH 能读的东西 |
| 记忆与纪律（`D:\AgentData\memory`、`DEEPCODE.md`） | **goose 单写** | — | **DSH 只读**，不写 memory / 纪律 |

**跨调口径（只有这三类交给对方，其余本地干）**：① recipe ② `D:\Clearn\tools\*.py` ③ 9 个 RAG 库的批量操作。

**🔀 路由判定（2026-10-28 定，用户原话：「已经验证成熟的功能就直接交给 goose，免得我反复授权；其他的还是先交给你」）**

一句话：**成熟的、一次能跑完的 → 直接给 goose；边做边试、要拿中间结果给你看的 → 留 DSH。**

| 判据（五条**全满足**才交给 goose） | 说明 |
|---|---|
| ① 在 DSH 里**跑通过至少一次** | 有产物 ＋ 有验证判据，不是第一次试 |
| ② 有**固定入口** | `tools\*.py` / recipe / 现成脚本组合，不是临时拼的命令 |
| ③ **落点清楚** | 路径、格式、命名都定死 |
| ④ **可回滚** | 脚本自带 dry-run 或备份 |
| ⑤ **不需要 DSH 独占能力** | 不涉及 Office 生成转换、`.univer` 编辑、slide 渲染 / lint |

- **直接交 goose（免反复授权）**：`daily_gate` / `followup` / `syncflow` / `merge_and_sync` / `daily_0730`、8 个 recipe、笔记整理与 Obsidian 库、RAG 批量重建、任务清单同步
- **留在 DSH**：新能力试验、需求还没定型、Office / `.univer` 产出、要逐步判断的排查（例：2026-10-28 的权限问题）、以及「DSH 产出 → 沉淀成 `tools\*.py` / recipe」这一步本身
- **交接要求**：task 必须自足（路径 / 日期 / 文件名 / 参数原样抄）＋ 写明**预期产物与验证判据**；goose 不共享本会话上下文
- **判据只看「验没验证过」，不看「谁写的」**；成熟后同一件事**只留 goose 一处实现**（重叠区禁令照样适用）
- **例外**：`tools\goose_mcp.py` 的**守卫层归 DSH** —— 约束不能由被约束方维护；其余 `tools\*.py` 照旧归 goose


**两条纪律**：
1. **产物框架无关**：成果只落普通文件（docx / pptx / pdf / py），不落框架内部状态、插件数据、会话快照。
2. **回收机制**：DSH 里试稳的流程 → 沉淀成 `tools\*.py` 或 skill → 两边都能用。**DSH 是孵化器，goose 是仓库。**

**接缝（只记路径；配置改动照样走第四条铁律）**：
- DSH 的 MCP 挂在 `C:\Users\36578\.dsh\profiles\desktop\cordis.patch.yml` 的 `insert:` 块里（`mcp-goose` → `tools\goose_mcp.py`；`mcp-rag` → `D:\rag\mcp_rag_bridge.py`）。**裸 id 写不进去**（只会覆盖已有条目、多出的条目被忽略），要写就包在 `insert:` 里；**改完不必重启**（HMR 约 3 s 生效），验收跑只读探针 `python D:\Clearn\tools\dsh_mcp_preflight.py`（真握手：initialize → tools/list → tools/call，故意用最坏环境）。
- DSH 的工作区必须是 `D:\Clearn`，否则读不到本文件；DSH 读本文件 ＋ skills 目录（**实际位置 `C:\Users\36578\.agents\skills\`**：`find-skills` / `tavily-first` 两个自定义；`goose-doc-guide` / `web-search` 是 goose 内置），所以这里的口径对两个入口同时生效。

## 我的备注
