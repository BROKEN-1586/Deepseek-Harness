# CHANGELOG · D:\Clearn 资产层

> **规则真身**：`DEEPCODE.md`「🏷️ 版本号规则」（用户 2026-10-28 定）。
> **版本号真身**：`D:\Clearn\VERSION`（单行，机器读）—— 本文件是**给人读的历史**，最新在最上面。
> 每条必带四样：**改了什么 / 涉及文件 / 验证 / 备份**。没验证的改动标 `⚠️ 未验证` 且**不占版本号**。

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
