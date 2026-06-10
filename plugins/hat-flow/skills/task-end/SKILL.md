---
name: task-end
description: "Use when the user confirms a task is done and testing has passed. Closes the active task in .tasks/open/. 触发词: \"结束任务\", \"任务完成\", \"关闭任务\", \"归档任务\""
---

# Task End — Lifecycle Closure

生命周期关闭 skill。编写完成报告、更新项目文档、归档任务文件夹。

**Announce at start:** "Using task-end to close this task."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Every message you show to the user MUST be written in Chinese (中文).
This includes status updates, analysis results, questions, error reports, and summaries.
Technical terms (e.g., CSS, Tailwind, scoped CSS) and code identifiers stay in English.
Do NOT write English sentences like "Let me check..." or "Light verification passed...".
Write "让我检查..." or "轻量验证通过..." instead.

## Red Flags — If You Are Thinking Any of These, You Are Making a Mistake

| If you are thinking...                                          | The reality is...                                                        |
| --------------------------------------------------------------- | ------------------------------------------------------------------------ |
| "User said tests passed, no need to run verification commands"  | Verbal confirmation ≠ mechanical verification. Step 0 is non-negotiable. |
| "`.last-verified` exists so it must be verified, skip it"       | You must compare commit hashes. Different hash = must re-verify.         |
| "It's just docs changes, no need for pre-commit check"          | Code changes mixed into doc commits is a common mistake. Must check.     |
| "Linear update failed but doesn't affect local work, skip it"   | Team visibility matters more than local convenience.                     |
| "final.md is good enough, no need to be thorough"               | final.md is the only completion record. Future you will thank thorough notes. |
| "Sub-issues look fine, no need to check each one"               | Looks fine ≠ confirmed fine. Go through each one.                        |

## Mandatory Stop Points

<rule>
Each Mandatory Stop Point requires AskUserQuestion. You MUST NOT proceed past a stop point without explicit user confirmation.
Reason: autonomous progression past decision points leads to wasted work when user preferences differ from defaults.
</rule>

| Step | When | What to Ask | Type |
|------|------|-------------|------|
| Step 0 | 验证命令未配置 | 配置方式：调研并配置 / 不需要 / 手动输入 | Decision |
| Step 0 | 验证失败 | STOP — 报告错误，不继续 | Gate |
| Step 1 | 多个打开的任务 | 选择要关闭的任务 | Decision |
| Step 1.5 | 识别到技术债务（记录新债） | 是否记录到 debt.md | Decision |
| Step 1.5 | debt 对账（关闭已解决） | 确认哪些 open 候选确属本任务解决（标 `[x]`） | Decision |
| Step 3.0e | 有未完成的子 issue | 逐个确认：标记 Done / 返回 Backlog / 保持不变 | Decision |
| Step 3.2 | CLAUDE.md 需要更新 | 确认更新内容 | Decision |
| Step 3.3 | 发现意外代码变更 | 先单独提交 / 暂存 / 丢弃 | Decision |
| Step 3.5 | 在非 main 分支上 | 4 选项菜单（merge / PR / keep / discard），discard 需 typed 确认 | Decision |

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），**先**从 phases.md 重建概览行（确保拿到最小 ID 以固定在首行）并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：先运行 `hat-task-detect .tasks` 获取 open[0].path（若尚未知晓），再执行 `cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：
   - 执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
   - 解析 `end_decisions` 字段（若存在）：`branch`/`claude_md` 用于覆盖 Step 3.2/3.5 的自动决策。字段缺失时使用默认值（见 UNATTENDED_PROTOCOL 第 6 节）
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守模式的激活（unattended.json 创建）统一由 `/task` 编排器的 Step 2A.1 处理。各阶段 skill 仅负责读取已有状态。

---

### P6 起始时间戳（core timing，内联）

内联记录 phase_start（须在本 phase 任何 `hat-plugin-hook` 调用之前；helper 自带顶层 `observability.enabled` 门控，关闭档 → no-op）：

```bash
hat-timing-stamp {task-folder} phase_start P6
```

### Step 0: Mechanical Verification

<rule>
Never skip mechanical verification based on verbal confirmation alone.
Reason: user saying "tests passed" does not substitute for running the actual verification commands — human memory is unreliable.
</rule>

**检查 `.last-verified` 文件：**

1. 读取 `.tasks/open/YYYY-MM-DD-topic/.last-verified`（确切路径在 Step 1 确定，但先运行验证）
2. 获取当前 HEAD：`git rev-parse HEAD`
3. 比对：
   - **Hash 匹配** → 输出"自上次验证以来无变更，跳过完整验证。" → 继续 Step 1
   - **Hash 不匹配或文件不存在** → 继续下方验证

**读取验证命令：**

从项目 `CLAUDE.md` 的 `## 验证命令` 章节读取。

- **已配置** → 运行命令，读取完整输出
  - 失败 → Stop here. 报告错误，不继续
  - 通过 → 将当前 HEAD hash 写入任务文件夹的 `.last-verified` → 继续
- **未配置** → AskUserQuestion：
  - **调研项目并配置** — 检查 `package.json` scripts、`Makefile` 等，推荐命令，写入 CLAUDE.md `## 验证命令`
  - **不需要（不再询问）** — 写入 `验证命令: none` 到 CLAUDE.md，视为通过
  - **手动输入** — 用户提供命令，写入 CLAUDE.md，然后运行

**[Unattended]** 若无人值守模式激活：跳过配置询问，继续执行。若验证失败：重试一次（Opus 修复），仍失败 → 发送 Telegram 通知 `[task-name] 验证失败，任务已取消：[错误]` → auto-cancel。

### Step 1: Identify Task

1. 检测任务：

   **Script** (preferred): `hat-task-detect .tasks` — exit 0 → 解析 JSON。`open` 数组包含任务对象，字段有 `name`、`path`、`hasDesign`、`hasPlan`、`hasFinal`、`linear`。

   **Fallback**: 使用 Glob 工具读取 `.tasks/open/`（`.tasks/open/*/`）。

   Do NOT use `ls`, `find`, or repeated `bash` commands to search for the task folder. 脚本或单个 Glob 调用就足够了。如果两者都不行，询问用户任务文件夹名称。

   - 一个任务 → 直接使用
   - 多个 → AskUserQuestion 让用户选择
   - 没有 → 检查 `.tasks/done/` 是否有最近的文件夹（可能是部分执行的）。找到 → 询问用户是否要继续关闭。未找到 → "没有打开的任务。" **End skill.**

2. 读取任务的 `design.md` 和 `plan.md`（如果存在）

### Step 1.1: phases.md Integrity Check

归档前必须确认 phases.md 的所有阶段都已正确标记。

1. 读取 `{task-folder}/phases.md`
2. 扫描所有 Phase 的 `**Status**` 和步骤 checkbox:
   - Phase 1-3: 应为 `DONE`,所有步骤 `[x]`
   - Phase 4: 应为 `DONE`,所有步骤 `[x]`
   - Phase 5: 应为 `DONE`,所有步骤 `[x]`
3. 如果 Phase 4 或 Phase 5 步骤仍为 `[ ]` 或 Status 仍为 `PENDING`:
   - **自动修复**: 将对应 Phase 所有步骤标记为 `[x]`,Status 改为 `DONE`,Updated 改为当前时间
   - 这种情况说明 task-execute 或 task-test 阶段未正确更新 phases.md(已知 bug,通过此检查兜底)

<rule>
Never archive a task with Phase 4 or Phase 5 Status still PENDING. Either fix phases.md or stop and investigate.
Reason: phases.md is the cross-session state record. Archiving incomplete state means future analysis of this task will show it as unfinished.
</rule>

### Step 1.1.1: 早期产物完整性检查（核心硬阻断）

对**已完成阶段（P1-P4）** 的产物做脚本式检查。终端产物（final.md/conversation.md 等 P5/P6）此时尚未生成，由 Step 3.3.7 终端门控负责。

逐相位运行（脚本已按插件启用条件化必需清单，如 observability 关则不要求 timing.jsonl）：

```bash
for n in 1 2 3 4; do
  hat-task-artifact-check {task-folder} "$n" --config {task-folder}/task-config.json
done
```

处理结果：

- **核心产物缺失**（prompt.md / phases.md / design.md / plan.md）→ **硬阻断**：停下调查，绝不带病归档。
- **插件产物缺失**（timing.jsonl 等，幂等可再生）→ 先尝试幂等补齐；补不上则在 final.md `## Verification` 记录缺失原因后继续（软警告）。
- **timing 痕迹警告**（脚本输出 `⚠️ phase 有 start 无 end`）→ **非阻断**：说明某已完成 phase 的 phase-end hook 未触发（中途 phase-end hook 在现系统并非每次都触发）。记入 final.md `## Verification` 作为软提示，不阻断归档。真正的元 bug——hook 完全没跑——表现为**缺 phase_start**，已由脚本硬 FAIL（核心产物缺失同级）拦截。

<HARD-GATE>
Never archive when a core artifact (prompt.md / phases.md / design.md / plan.md) is missing. Stop and investigate.
Reason: core docs are the task's identity and cross-session state. Archiving without them silently produces an unrecoverable, unanalyzable task record — the failure stays invisible until someone later tries to read the task and finds nothing.
</HARD-GATE>

### Step 1.2: Phase 6 Tracking

将 Phase 6 标记为 IN_PROGRESS，更新 phases.md：
- Phase 6 `**Status**: PENDING` → `**Status**: IN_PROGRESS`
- 更新 `**Updated**` 时间

后续每个 Step 完成时同步更新 Phase 6 的步骤 checkbox。映射关系：
- `6a. 验证 + final.md` → Step 0 + Step 2
- `6b. 归档 + Linear Done` → Step 3.0 + Step 3.1 + Step 3.2 + Step 3.3 + Step 3.4 + Step 3.5

**归档 commit 之前（Step 3.3.4）**：将 Phase 6 所有步骤标记为 `[x]`，Status 改为 `DONE`，更新 `**Updated**` 时间——使归档 commit 捕获完整 Phase 6 状态，归档后工作树不再残留 phases.md 修改。

<rule>
Every step completion MUST update phases.md: mark step [x], update Updated time, update Status when all steps done.
Reason: phases.md is the cross-session state record. Missing updates mean the next session cannot correctly resume.
</rule>

### Step 1.5: Technical Debt 对账（记录新债 + 关闭已解决）

`docs/debt.md` 条目用 `- [ ]`（open）/ `- [x] ... — resolved: <出处>`（resolved）标记状态。本步双向对账，形成与 task-init「1b.4 Debt 关联检查」的 init→end 闭环：

**A. 记录新债务**：回顾此任务期间的变更——是否用了变通/临时方案？是否有已知但未修复的问题？如有，追加为 `- [ ]` open 条目到 `docs/debt.md`。

**B. 关闭已解决债务（对账）**：核对 `docs/debt.md` 中的 open 条目，找出**本任务疑似已解决**的（依据：task-init 1b.4 带入的相关项 + 本任务实际改动的文件/issue 重叠）。把它们整理为**候选清单提议**给用户，确认后才标 `- [x] ... — resolved: <本任务 issue-id>`。

<rule>
Both recording new debt and closing resolved debt MUST go through user confirmation (AskUserQuestion: which items to record / which candidates are truly resolved). Never decide on behalf of the user — neither "no debt worth recording" nor "this open item is now resolved." Marking an open item [x] without confirmation can falsely close debt that was not actually fixed.
Reason: debt visibility is a team concern — the user, not the agent, owns what to track and what counts as resolved. Auto-closing risks silently dropping unfixed debt.
</rule>

**[Unattended]** 无人值守模式：A 自动追加新债务为 `- [ ]`；B 自动把**高置信**候选（本任务直接改动的文件/issue 命中的 open 项）标 `- [x] ... — resolved: <issue-id>`，低置信项保持 open 并在 final.md 记录"疑似解决待人工确认"。均写 `docs/debt.md`，不询问。

### Step 2: Write final.md

Claude 按下方模板直接编写 `final.md`（在任务文件夹中，此时仍在 `open/`）：

```markdown
# Task Completion Report

**Task**: [task name]
**Completed**: YYYY-MM-DD
**Status**: Completed

## What Was Built

[对照 design.md 的成功标准，逐项确认]

## Problems Encountered

[来自 reports/ 目录和实际工作。每项包含：问题、解决方案、教训]

## Deviations from Plan

[与 plan.md 对比。每项包含：原始 → 实际，原因]

## Verification

- [x] Verification commands passed (or skipped) (output: [exit code])
- [x] User acceptance passed

## Changelog Entry

[要添加到 docs/changelog.md 的内容]

## Follow-up Suggestions

[可选：改进建议或后续步骤]

## Consumption Summary

[待导出后填充]
```

**Consumption Summary 填写规则**：
Step 2 写 final.md 时保留 `[待导出后填充]` 占位符。实际数据由 Step 3.3.5 导出后在 Step 3.3.6 回填。

### Step 2.5: Clean Up Todo List

归档前，确保所有 Tasks（Flow 级 + Exec 级）已标记为 completed 或已删除。扫描 TaskList 并根据实际状态更新所有剩余的 pending/in_progress 项：
- 已完成但未标记 → completed
- 有条件地跳过 → completed（附注释）
- 用户手动完成（如验收测试）→ completed

### Step 3: Closing Activities

按以下顺序执行：

**3.0 P6.pre-archive Hook（Linear + Git 安全检查）**

```bash
hat-plugin-hook {task-folder} P6.pre-archive
```

> **Subagent**：linear 在 P6.pre-archive 为 `subagent:linear-sync` hook。`hat-plugin-hook` 输出 DISPATCH 指令，编排器据此派一次性后台 subagent 异步执行（见 task/SKILL.md Subagent Async Dispatch）。归档前的 P6 同步是 Linear 状态的最终兜底——若该 subagent 失败（result 报错），主线程按 graceful 记录后**仍可主线程补做** P6 Linear 收尾（状态 Done + 归档 comment），不可静默漏掉。

hook 输出可能包含多段指令，**必须逐段全部执行**（git: pre-commit 安全检查；linear: 状态 Done + 评论 + 文档 + 子 issue 处理）。插件关闭时对应操作跳过。

> 一次性 subagent 无需 shutdown / 清理——派发即自终结，归档前无 team 生命周期收尾步骤。

**3.1 Update Changelog**

- 将 final.md 中的 changelog 条目前置到 `docs/changelog.md`
- 格式：`- **YYYY-MM-DD**: [description]`

**3.2 Update CLAUDE.md** (conditional, with stale detection)

**过时内容检测**（plan §九）：

- **完整检测触发条件**：变更涉及 `package.json`/`tsconfig.json`/`bin/`/`Makefile` 等配置文件
- **快速检查**（始终执行）：检查 CLAUDE.md 中引用的文件路径是否仍存在（本次任务删除的文件）

完整检测时扫描 CLAUDE.md 中的：
1. 验证命令是否仍有效
2. 脚本路径是否存在
3. 目录结构描述是否匹配实际
4. 依赖版本是否匹配 package.json

检测到过时内容 → AskUserQuestion 确认推荐修改。

**常规更新**：
- 仅当任务涉及架构变更、新功能、新依赖或新脚本时
- 使用 AskUserQuestion 与用户确认

**[Unattended]** 自动更新（按 `end_decisions.claude_md`）。

**3.3 Pre-commit Safety Check**

> **pre-commit 安全检查已由 `P6.pre-archive` hook 中 git plugin 执行。**

本步骤仅检查 hook 未覆盖的场景：意外的代码变更混入关闭 commit。

`git status --porcelain` 区分预期文件（`.tasks/`、`docs/`、`CLAUDE.md`）和意外文件。

意外变更 → AskUserQuestion：**先单独提交** / **暂存** / **丢弃**。
**[Unattended]** 意外变更自动加入当前 commit。

**3.3.4 归档前状态定稿（phases.md Phase 6 DONE + P6 phase_end，归档 commit 之前）**

归档 commit 必须捕获完整终态，故在导出/归档**之前**先定稿这两处写操作——修复"归档后才写 phases.md / timing.jsonl、泄漏进后续无关 commit、归档 commit 里任务产物残缺"的时序 bug：

1. 将 `{task-folder}/phases.md` 的 Phase 6 所有步骤标记 `[x]`、`**Status**: DONE`、更新 `**Updated**`。
2. 内联记录 P6 phase_end 时间戳（须在 3.3.5 导出之前，使 consumption-report 的 P6 时长完整、且随归档 commit 落盘）：
   ```bash
   hat-timing-stamp {task-folder} phase_end P6
   ```

<rule>
P6 phase_end 与 phases.md Phase 6 DONE 必须在归档 commit 之前（本步）写入，绝不放到 Step 3.4 归档之后。
Reason: 归档后再写会留下未提交的 timing.jsonl（+ phases.md，共两个文件），泄漏进后续无关 commit（如自动 `chore: update`），且归档 commit 里的任务产物残缺（少最后一条 timing + Phase 6 非 DONE）。前移到归档前让归档 commit 捕获完整终态、归档后工作树干净。P6 时长为归档前快照（少算其后导出/归档动作数秒），可接受。
</rule>

**3.3.5 对话导出**

运行 `hat-conversation-export "{task-folder}/conversation.md"`。脚本会同时在同目录生成 `consumption-report.md`（阶段消耗分析）。若脚本失败（退出码非 0），记录警告但不阻塞。

**3.3.6 消耗数据回填**

读取 `{task-folder}/consumption-report.md`，用 Edit 工具将数据回填到 final.md 的 `## Consumption Summary` 占位符处：
1. 提取阶段消耗表和高消耗行为分析
2. 根据数据给出 1-3 条改进建议（面向用户展示，用用户配置语言）
3. 导出失败时保留 `[待导出后填充]` 占位符并在 `## Verification` 中记录

**3.3.6.5 Plugin Breakdown（归档前写入，consumption-report.md 唯一终写点）**

解析 `{task-folder}/timing.jsonl`，生成 Plugin Breakdown 表**追加到 consumption-report.md 末尾**：

```markdown
## Plugin Breakdown

| Plugin | Invocations | Errors | Skipped |
|--------|------------|--------|---------|
| ...    |   |   |   |

Total timing entries: {N}
Phase durations: P1={duration}, P2={duration}, ...
```

**timing.jsonl 各行以 `event` 字段标识、无 `plugin` 字段**——据此区分两类：core timing 事件（`event` ∈ `phase_start`/`phase_end`/`task_start`/`task_end`）计入「Total timing entries」与「Phase durations」、**不进 Plugin 表**；`tdd_cycle` 事件归 tdd plugin 行。Plugin 维度只统计 5 个真 plugin（review/linear/git/tdd/retrospective）——observability 已下沉为核心能力、**不再作为 Plugin 行**（其 timing 仅喂 Total/durations）。

timing.jsonl 不存在（observability 关闭）→ 输出警告并跳过。

<rule>
consumption-report.md must be finalized here, before archive — this is its only write point past Step 3.3.5.
Reason: this write previously ran in the post-archive P6.phase-end hook, landing on the already-moved `done/` path and never entering the archive commit. Writing it pre-archive makes consumption-report.md complete when the Step 3.3.7 gate checks it and ensures it is committed with the task. P6 phase_end is now recorded in Step 3.3.4 (before this step), so the P6 duration here is complete; it remains a pre-archive snapshot (excludes the few seconds of export/archive mechanics), which is acceptable.
</rule>

**3.3.7 终端产物门控（归档前 HARD-GATE）**

归档不可逆。归档前对终端阶段产物（P5+P6）做强门控：

```bash
hat-task-artifact-check {task-folder} 5 --config {task-folder}/task-config.json
hat-task-artifact-check {task-folder} 6 --config {task-folder}/task-config.json
```

必需清单已由脚本按插件条件化（observability→timing.jsonl；conversation.md/consumption-report.md/final.md 始终必需）。

**FAIL → 自动补齐（仅限幂等产物再生）：**

| 缺失产物 | 幂等补齐动作 |
|---|---|
| conversation.md / consumption-report.md | 重跑 `hat-conversation-export "{task-folder}/conversation.md"`（重导出，无副作用）；重导出会覆盖 consumption-report.md，故补齐后**重跑 Step 3.3.6.5 的 Plugin Breakdown 追加**，避免丢失 breakdown 表 |
| final.md | 按 Step 2 模板重写 |

<HARD-GATE>
Auto-repair MUST regenerate idempotent artifacts only. Never re-run side-effect hooks (linear status, git staging/commit) during repair.
Reason: repair runs in a FAIL path that may execute more than once; re-running linear/git hooks would double-post comments or create duplicate/partial commits. Re-export and re-score are safe to repeat; side effects are not.
</HARD-GATE>

**补齐后重检 + 硬/软策略：** 重跑上述两条 artifact-check，然后：

- **核心产物仍缺失**（final.md、P5 核心 acceptance-checklist.md）→ **硬阻断**：不归档，停下调查。
- **conversation.md / consumption-report.md 仍缺失**：
  - 因**合法导出失败**（JSONL 未 flush 等已知可恢复原因，重导出仍失败）→ 降级**软警告**：在 final.md `## Verification` 记录缺失原因，**不死锁归档**。
  - 因**步骤被跳过**（导出从未运行）→ auto-repair 应已补上；若补齐后仍缺失则按硬阻断处理。

<HARD-GATE>
A legitimate export failure (conversation.md / consumption-report.md unrecoverable after re-export) must NOT deadlock the archive; a missing core artifact (final.md, acceptance-checklist.md) must NOT pass the gate.
Reason: conversation/consumption are observability nice-to-haves — blocking archive on them strands a finished task. Core artifacts are the task record itself — passing without them silently archives a broken task. Different artifacts warrant different blocking strength.
</HARD-GATE>

**timing 痕迹警告非阻断**：脚本对"已完成 phase 有 phase_start 无 phase_end"输出 `⚠️` 警告但**不计入 FAIL**（中途 phase-end hook 未必每次触发）。此类警告记入 final.md `## Verification` 软提示，不阻断归档；只有"缺 phase_start"（hook 完全没跑）才硬 FAIL。

**[Unattended]** 门控 FAIL（补齐后核心仍缺失）→ **不归档**、停下 + 发送 Telegram 通知 `[task-name] 归档前产物门控失败：[缺失清单]`。

> **已知限制（精简档位）**：observability 关闭时（如 hotfix 档），条件化必需清单收缩至 conversation.md + 核心产物，Layer 2（timing 痕迹校验，见 hat-task-artifact-check）fail-open，元 bug 结构检测退化为仅靠 Layer 1（编排器 HARD-GATE，prose）。该档位需人工留意 hook 是否真正执行。

**3.4 Archive and Commit** (single commit)

Do NOT use `git add -A`. Only add specific files that are part of the task closure.

**Script** (preferred):

```bash
hat-task-archive "YYYY-MM-DD-topic" done --extra-files docs/changelog.md CLAUDE.md --message "docs: complete and archive task [YYYY-MM-DD-topic]"
```

（仅在 3.2 做了修改时才在 `--extra-files` 中包含 CLAUDE.md）

**Fallback**:

```bash
git mv .tasks/open/YYYY-MM-DD-topic .tasks/done/YYYY-MM-DD-topic
git add docs/changelog.md
# 仅在 3.2 修改了 CLAUDE.md 时：
git add CLAUDE.md
git commit -m "docs: complete and archive task [YYYY-MM-DD-topic]"
```

遵循项目 git 规范（检查 CLAUDE.md 的 git 规范章节）。如果项目在 commit 中追踪 Linear issue ID，则包含它。

**3.4.1 Verify Commit Content**

提交后，立即运行 `git show --stat HEAD`。与 3.3 中预期的文件列表对比：
- 所有预期文件都在提交中 → 继续
- 缺少文件 → `git add` 缺少的文件（对 .gitignore 中的已跟踪文件使用 `git add -f`）然后 `git commit --amend --no-edit`

**3.4.2 Archive Old Tasks** (optional, independent commit)

当前任务归档提交完成后，顺带清理超过 14 天的老任务：

```bash
hat-task-detect .tasks --archive-old
```

读取输出的 `archived` 字段——若为空对象（`{"done":[],"canceled":[],"deferred":[]}`），跳过；若有条目，执行独立 commit：

```bash
git add .tasks
git commit -m "chore: archive old tasks (>14 days)"
```

**Rule**: 此归档 commit 必须与 3.4 的任务完成 commit 分离，避免将无关的历史任务移动混入 "complete task" commit。

**3.4.3 Clean Up Revise Tags** (conditional)

```bash
git tag -l 'revise-*' | xargs git tag -d 2>/dev/null
```

如果有 tag 被删除，输出清理结果。无 revise tag 则跳过。

**3.5 P6.post-archive Hook（分支处理 + 回顾）**

归档 commit 完成后运行：

```bash
hat-plugin-hook {task-folder} P6.post-archive
```

hook 输出可能包含多段指令，**必须逐段全部执行**（git: 分支合并 + revise tag 清理 + 旧任务归档；retrospective: 流程审查）。插件关闭时对应操作跳过。

### Step 4: Confirmation

输出最终清单：

- [x] 验证命令通过（或跳过）
- [x] final.md 已编写
- [x] changelog 已更新
- [x] CLAUDE.md 已更新（如需要）
- [x] 关闭提交中没有泄漏代码变更
- [x] 任务文件夹已归档到 done/
- [x] 分支已处理（如适用）
- [x] Linear issue 已同步（如适用）
- [x] Linear 子 issue 已处理（如适用）
- [x] Git 已提交（单次关闭提交）

**[Unattended]** 发送 Telegram 通知 `[task-name] 任务已完成并归档 ✓`。

### P6 结束时间戳（core timing，内联——已前移到归档前）

P6 phase_end **不再在归档后写**，已前移到 **Step 3.3.4**（归档 commit 之前），与 phases.md Phase 6 DONE 一同定稿，使二者都进入本任务的归档 commit、归档后工作树干净。此处不再有任何写操作（保留本节仅作交叉指引，防止误以为还要在末尾补写）。

> 历史背景：此 phase_end 原在归档后写、落 `done/` 路径不进归档 commit（曾被标为"已知 minor 限制"），实测会留下未提交的 timing.jsonl 泄漏进后续无关 commit、归档产物残缺。已通过前移至 Step 3.3.4 修复。

---

**如果要取消任务：** 使用 `/task-cancel`。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/plan.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/final.md`, `{task-folder}/phases.md`, `{task-folder}/conversation.md`, `{task-folder}/consumption-report.md`
- **Hooks**: `P6.pre-archive`（git + linear）, `P6.post-archive`（git + retrospective）
- **Core timing**（内联，非 hook）: phase_start P6（阶段开始）/ phase_end P6（**Step 3.3.4，归档 commit 之前**，与 phases.md DONE 一同定稿）经 `hat-timing-stamp`，受顶层 `observability.enabled` 门控
- **Scripts**: hat-task-archive, hat-task-detect, hat-plugin-hook, hat-conversation-export, hat-timing-stamp
