# CHANGELOG · D:\Clearn 资产层

> **规则真身**：`DEEPCODE.md`「🏷️ 版本号规则」（用户 2026-10-28 定）。
> **版本号真身**：`D:\Clearn\VERSION`（单行，机器读）—— 本文件是**给人读的历史**，最新在最上面。
> 每条必带四样：**改了什么 / 涉及文件 / 验证 / 备份**。没验证的改动标 `⚠️ 未验证` 且**不占版本号**。

## Alpha 0.3.1 · 2026-10-28 · 三件收尾落地（脚本归档 / 记忆分卷 / 详版备案）＋ DSH 重启核验

- **改了什么**：① **U6** `_diag` 的 125 个一次性脚本 → `_diag\archive\scripts-20261028\`（只移不删，移动前做过活引用核对，仅剩问题汇总台账里的历史提及），根目录保留 8 个常备工具 ② **U12** `lessons-recent.md` 触发自己的滚动上限（完整条目只留 5 条）→ 6 条（10-24 ~ 10-27）整段切进 `memory\archive\lessons-2026-10-24_to-2026-10-28.md`，热区 341 → 228 行、留 5 条全文 ＋ 6 条一行索引 ③ **U21** 新建 `07-备案库\02-每日任务记录\2026-10-28.md`（详版备案，8 段），并把 `01-我的记录\2026-10.md` 里 5 处「🔗 详版：未建」改成指向本页 ④ **DSH 重启核验**（用户授权）：进程全清后重启 `D:\DSH Next\DSH NEXT.exe`
- **涉及文件**：`D:\Clearn\_diag\`（125 个脚本移动）、`D:\AgentData\memory\lessons-recent.md`、`D:\AgentData\memory\archive\lessons-2026-10-24_to-2026-10-28.md`（**新**）、`Obsidian\07-备案库\02-每日任务记录\2026-10-28.md`（**新**）、`Obsidian\07-备案库\01-我的记录\2026-10.md`、`CHANGELOG.md`、`VERSION`、`AGENTS.md`
- **验证**：① 移动后 `_diag` 根目录只剩预期的 8 个 `.py`（脚本内 `assert`）② 热区标题数 = 5（`assert`）、分卷 135 行纯 CRLF ③ 详版 65 行纯 CRLF；`archive-rag` 重建 **196 段**（8 个文件），探针 2 条均 top 命中新页 ④ 重启后 DSH 进程 5 个、`desktop-next.log` 新段 **0 条 `patch: … not found`**（对比 08:49 那次的 2 条）→ `insert:` 块被正常应用；进程表里 `goose_mcp.py`（PID 16584）与 `mcp_rag_bridge.py` 均在跑 → 两个 MCP client 真的拉起了服务
- **备份**：`D:\backup\u12-<ts>\`、`D:\backup\u21-<ts>\`、`D:\backup\v031-<ts>\`

## Alpha 0.3.0 · 2026-10-28 · 清单链路收口：recipe 重写 ＋ syncflow 修 bug/扩教务页 ＋ 每日 07:30 零 token ＋ git 入库

- **改了什么**：
  1. **`read-the-night.yaml` 整份重写**（recipe 版本 1.0.0 → **1.1.0**）：标题改成「读 流水日记 → 任务清单（作业池 + 教务页）」，instructions 从旧的 `D:\日程规划` / `02-按日期` 快照 / `92-作业清单` / `93-日程规划` 全量改成 `D:\任务清单` 口径（取材表、四行式、剩余天数、核对关卡、镜像并集），并补「先跑 `daily_gate.py` 取判据」「`cw_extract.py` 抽课件文字」两步
  2. **`syncflow.py` 三处改**：① ③ 的扫描范围从 `01-作业清单` 扩到 **`01-作业清单` ＋ `02-教务清单`**（教务页的剩余天数以前从来没人重算）② **修「折叠静默删行」bug** —— 没到「完成＋提交都勾」的条目原来只留首行、把 `完成 / 提交 / 截止` 三个子行丢掉，`--apply` 会真删 ③ 把重算提成 `due_new()`，已勾条目的 `- 截止：` 子行也过一遍（以前被折叠 while 吞掉）
  3. **`daily_gate.py` 加 `_diag\flow-log.tsv` 留痕**：每天写「日期 · VERDICT · 时刻」，给 `followup.py` 的「素材缺口」判据一个自增长的事实源
  4. **`followup.py` 两处改**：§2 素材缺口判据从「已取消的每日快照」改成三处留痕（作业池出处 / `flow-log.tsv` / `07-备案库\02-每日任务记录`）；§5 索引新鲜度从只查 note-rag 扩到**全部 9 个库** ＋ 孤儿索引目录检测
  5. **新建 `tools\daily_0730.bat` ＋ 计划任务 `ClearnDailyGate`**：每天 07:30 顺序跑 `daily_gate.py` ＋ `followup.py`，**0 token**，日志追加 `_diag\daily-0730.log`
  6. **`git init D:\Clearn`**（首次纳入版本管理）：`.gitignore` 排除 `_diag` / `_backup*` / `_work` / `tools\_retired`；`.gitattributes` 写 `* -text` **保字节原样**（仓库混有 CRLF 规则文件与 LF 脚本），首提交 43 个文件
- **涉及文件**：`.goose\recipes\read-the-night.yaml`、`tools\syncflow.py`、`tools\daily_gate.py`、`tools\followup.py`、`tools\daily_0730.bat`（**新**）、`.gitignore`（**新**）、`.gitattributes`（**新**）、`CHANGELOG.md`、`VERSION`、`AGENTS.md`、`DEEPCODE.md`、`问题汇总\问题汇总.md`、`D:\任务清单\` 的 6 个作业池 ＋ 6 个教务页（剩余天数重算 ＋ 已完成折叠）、`Obsidian\92-任务清单\`（镜像同步）
- **验证**：`goose recipe validate` ✓ valid；`_diag\check_days.py` 扫真身 **17 处带剩余天数 → 不一致 0 处**；`daily_gate.py` 镜像 **两侧一致 ✅**；计划任务实跑（`schtasks /run`）`daily_gate rc=0` / `followup rc=0`，日志已落盘；`git status` 干净、43 文件入库；`syncflow.py` `py_compile` 通过、无 CR 混入
- **备份**：`D:\backup\syncflow-patch-<ts>\`（扩教务页前）、`D:\backup\syncflow-bugfix-<ts>\`（修折叠前）、`D:\backup\syncflow-duef-<ts>\`（提 `due_new` 前）、`D:\backup\syncflow-20261028-180442\` / `-180624\`（两次 `--apply` 前的真身）、`D:\backup\recipe-20261028-180432\`、`D:\backup\sched-<ts>\`、`D:\backup\v030-<ts>\`（本次文本改动）

## Alpha 0.2.0 · 2026-10-28 · 定下「有效改动必升号」规则 ＋ 版本号机制落地

- **改了什么**：新增版本号制度（格式 `Alpha 0.MINOR.PATCH`、有效改动两条件、一任务一号、升号三件事、不升号清单、回滚口径）；建立 `VERSION` ＋ `CHANGELOG.md` 两个**框架无关**文件（goose 与 DSH 都直接读）；`DEEPCODE.md` 新增「🏷️ 版本号规则」节，§C 路由表、§D 收尾清单、文末节索引同步；`AGENTS.md` 第一屏挂「当前版本 ＋ 指针」
- **涉及文件**：`D:\Clearn\VERSION`（**新**）、`D:\Clearn\CHANGELOG.md`（**新**）、`D:\Clearn\DEEPCODE.md`、`D:\Clearn\AGENTS.md`
- **验证**：`VERSION` 与本节条首行版本一致；新节标题在全文唯一；`DEEPCODE.md` / `AGENTS.md` 行尾纯 CRLF（`LF == CRLF`）
- **备份**：`D:\backup\version-rule-20261028-<ts>\`

## Alpha 0.1.0 · 2026-10-28 · 基线（版本机制启用那一刻的现状快照）

收录当天已经做完的两次有效改动：

- **① 重写 `DEEPCODE.md`「📥 作业 / 教务清单 + 🔄 同步链路」整节**：旧节 312 行（1081–1392）写于 10-08～10-19，仍指向已删的 `D:\日程规划` / `02-按日期` / `93-日程规划`；换成按 `D:\任务清单` 现状的 8 小节（事实基础＋工具清单 / 取材 / 六条硬规则 / 四行式 / 截止＋剩余天数 / 每日复查与顺延 / 镜像同步含 T36 盲区 / 修订记录）；散落死引用 7 处改口；1537 → 1382 行
- **② 全身审核修复**：重建落后索引 `novel-rag`（141 段）、`aiout-rag`（73 段）；`AGENTS.md` 补 `goose_mcp.py` / `dsh_mcp_preflight.py` 两行 ＋ 技能真实路径 ＋ recipe 8/8 验证记录；`问题汇总` 新增 **T39**（goose `edit` 多行块带孤立 LF，同族 T24 第 3 次）
- **验证**：CRLF 1381 == LF 1381、无 BOM、新节标题唯一；两库探针 top1 命中 0.409 / 0.365；`goose recipe validate` 8/8 valid；`MEMORY.md` 64 条索引 0 失效
- **备份**：`D:\backup\deepcode-rewrite-20261028-173304\`、`D:\backup\eol-20261028-173417\`、`D:\backup\insert-20261028-173809\`、`D:\backup\insert-20261028-173814\`、`D:\backup\insert-20261028-173840\`、`D:\backup\insert-20261028-173845\`
