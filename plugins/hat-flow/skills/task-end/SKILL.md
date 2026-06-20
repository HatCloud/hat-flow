---
name: task-end
description: "Use when the user confirms a task is done and testing has passed. Closes the active task in .tasks/open/. 触发词: \"结束任务\", \"任务完成\", \"关闭任务\", \"归档任务\""
---

# Task End — Lifecycle Closure

生命周期关闭 skill。编写完成报告、更新项目文档、归档任务文件夹。

**Announce at start:** "Using task-end to close this task."

**LANGUAGE RULE:** Write user-facing output in the user's configured language; keep technical terms and code identifiers in their original form.

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
| Step 3.4.4 | worktree 隔离任务归档后 | 按 `end_decisions.branch`（auto_merge/keep）merge-back + 清理；PR/Discard 永不自动 | 核心，无交互（worktree 任务的分支处理在此，3.5 自然 no-op） |
| Step 3.5 | 在非 main 分支上（非 worktree 任务） | 4 选项菜单（merge / PR / keep / discard），discard 需 typed 确认 | Decision |

## TODO Sync

双层 TODO 同步契约见 `task/references/todo-sync.md`。要点：每步 `TaskUpdate`（开始 `in_progress`、完成 `completed`）并同步 phases.md；session 恢复时先 `TaskList`，无 `overview` 行则从 phases.md 重建（取最小 ID）再建 step 级 task。

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
    - 多个 →
       - **[Interactive]** AskUserQuestion 让用户选择
       - **[Unattended]** 不询问，按如下顺序自动选择：
          1) 当前 session 最近更新（`Updated` 最新）的 open task；
          2) 若无法判定（无 phases.md 或时间戳并列），发送 Telegram 通知并暂停，等待 `/task` 恢复人工选择。
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

逐相位运行（脚本已按插件启用条件化必需清单）：

```bash
for n in 1 2 3 4; do
  hat-task-artifact-check {task-folder} "$n" --config {task-folder}/task-config.json
done
```

处理结果：

- **核心产物缺失**（prompt.md / phases.md / design.md / plan.md）→ **硬阻断**：停下调查，绝不带病归档。
- **插件产物缺失**（幂等可再生）→ 先尝试幂等补齐；补不上则在 final.md `## Verification` 记录缺失原因后继续（软警告）。

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

Phase 6 DONE 定稿须在归档 commit 之前完成（权威规则见 Step 3.3.4）。

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

**[Unattended]** 无人值守模式（§9 **A3** 债务对账）：A 自动追加新债务为 `- [ ]`；B 自动把**高置信**候选（本任务直接改动的文件/issue 命中的 open 项）标 `- [x] ... — resolved: <issue-id>`，低置信项保持 open。均写 `docs/debt.md`，不询问。
- **`degrade_policy` conservative / headless 额外留痕**：把自动关闭动作 + 低置信疑似项汇总写入 `unattended-decisions.md` 的 `## Headless Degraded Decisions`，并在 final.md P6 汇总引用（使人工回看可见所有自动债务决策）。`standard` / 缺省维持原行为（仅 final.md 记"疑似解决待人工确认"），现有任务零变更。

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

> **P6 兜底**：归档前的 P6 linear 同步是 Linear 状态的最终兜底——主线程 inline 执行，**必须完成、不可静默漏掉**（状态 Done + 归档 comment）；若某步失败，graceful 记录后仍要补做 P6 Linear 收尾。

hook 输出可能包含多段指令，**必须逐段全部执行**（git: pre-commit 安全检查；linear: 状态 Done + 评论 + 文档 + 子 issue 处理）。插件关闭时对应操作跳过。

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

**3.3.4 归档前状态定稿（phases.md Phase 6 DONE，归档 commit 之前）**

归档 commit 必须捕获完整终态，故在导出/归档**之前**先定稿 phases.md——修复"归档后才写 phases.md、泄漏进后续无关 commit、归档 commit 里 Phase 6 非 DONE"的时序 bug：将 `{task-folder}/phases.md` 的 Phase 6 所有步骤标记 `[x]`、`**Status**: DONE`、更新 `**Updated**`。

<rule>
phases.md Phase 6 DONE 必须在归档 commit 之前（本步）写入，绝不放到 Step 3.4 归档之后。
Reason: 归档后再写会留下未提交的 phases.md，泄漏进后续无关 commit（如自动 `chore: update`），且归档 commit 里 Phase 6 非 DONE。前移到归档前让归档 commit 捕获完整终态、归档后工作树干净。
</rule>

**3.3.5 对话导出**

运行 `hat-conversation-export "{task-folder}/conversation.md"`。脚本会同时在同目录生成 `consumption-report.md`（阶段消耗分析）。若脚本失败（退出码非 0），记录警告但不阻塞。

**3.3.6 消耗数据回填**

读取 `{task-folder}/consumption-report.md`，用 Edit 工具将数据回填到 final.md 的 `## Consumption Summary` 占位符处：
1. 提取阶段消耗表和高消耗行为分析
2. 根据数据给出 1-3 条改进建议（面向用户展示，用用户配置语言）
3. 导出失败时保留 `[待导出后填充]` 占位符并在 `## Verification` 中记录

**3.3.7 终端产物门控（归档前 HARD-GATE）**

归档不可逆。归档前对终端阶段产物（P5+P6）做强门控：

```bash
hat-task-artifact-check {task-folder} 5 --config {task-folder}/task-config.json
hat-task-artifact-check {task-folder} 6 --config {task-folder}/task-config.json
```

必需清单已由脚本按插件条件化（conversation.md/consumption-report.md/final.md 始终必需）。

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
Reason: conversation/consumption are reporting nice-to-haves — blocking archive on them strands a finished task. Core artifacts are the task record itself — passing without them silently archives a broken task. Different artifacts warrant different blocking strength.
</HARD-GATE>

**[Unattended]** 门控 FAIL（补齐后核心仍缺失）→ **不归档**、停下 + 发送 Telegram 通知 `[task-name] 归档前产物门控失败：[缺失清单]`。

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

**3.4.4 Worktree Teardown（核心，仅 worktree 隔离任务）**

worktree 由 core config `branch.worktree` 门控、用内置工具创建（task-init 1d-wt），其拆解同属核心（不是某插件能力）。归档 commit 完成后、P6.post-archive 之前执行。

**检测是否在 worktree 内**（linked worktree 的 `--git-dir` 与 `--git-common-dir` 不同）：

```bash
[ "$(git rev-parse --git-dir 2>/dev/null)" != "$(git rev-parse --git-common-dir 2>/dev/null)" ] && echo IN_WORKTREE
```

非 worktree（输出空）→ 跳过本步（普通分支由 3.5 P6.post-archive 的 git plugin 处理）。

**在 worktree 内时**：记 `WT="$(git rev-parse --show-toplevel)"`、`BR="task/{folder}"`、`MAIN_ROOT`（`git worktree list` 首行的主工作树路径）。读 `end_decisions.branch`（unattended.json；交互模式则取 Step 3.5 用户决策；缺省 `keep`）。

1. **先把归档后的任务文件夹物理同步回主仓库**（无论 `.tasks/` 是否被 git 跟踪都不丢记录）：
   ```bash
   mkdir -p "$MAIN_ROOT/.tasks/done"
   cp -R "$WT/.tasks/done/{folder}" "$MAIN_ROOT/.tasks/done/" 2>/dev/null || true
   rm -rf "$MAIN_ROOT/.tasks/open/{folder}"   # 清除主仓库 stub 指针
   ```
2. **退出 worktree 回主目录**：`ExitWorktree(action="keep")`（path 进入的 worktree，keep 仅返回原目录、不删；删除由下方按 end_decisions 决定）。CWD 现在主仓库。
3. **按 `end_decisions.branch` 处理**（读 `end_decisions.squash`，缺省 `true`）：

   | 值 | 动作 |
   |---|---|
   | `auto_merge` | 主目录合并 task 分支：`squash==true`（缺省）→ `git merge --squash "$BR" && git commit -m "{conventional msg} [{folder}]"`（worktree 内全部改动压成单 commit）；`squash==false` → `git merge --no-ff "$BR" -m "merge: {folder} (worktree)"`。成功 → `git worktree remove "$WT"` + `git branch -D "$BR"`（squash 后用 `-D`；no-ff 可 `-d`）。merge 冲突 → **不强 merge**：保留 worktree + 分支，登记 `docs/unmerged-branches.md`，**[Unattended]** Telegram 通知冲突需人工。 |
   | `keep`（缺省） | 不 merge、不删 worktree/分支；登记 `docs/unmerged-branches.md`（分支名 + worktree 路径），留待人工 |

   **PR / Discard**：worktree 任务**永不自动** PR/Discard——一律按 `keep` 保留 worktree，登记待人工（与 §6 一致）。

<rule>
For a worktree task, ExitWorktree(keep) and return to the main directory BEFORE any merge; physically copy the archived task folder back to the main repo first so removing the worktree never loses the task record. Never `git worktree remove` with unmerged work unless end_decisions is auto_merge AND the merge succeeded cleanly.
Reason: the worktree's `.tasks/` may be untracked (gitignored in a generic project), so a merge alone would not carry the task record — only the physical copy guarantees it survives removal. Force-removing an unmerged worktree discards real work, which is a HARD-STOP class action (see UNATTENDED_PROTOCOL §9).
</rule>

完成后 CWD 在主目录、on 原分支：3.5 的 git-plugin 分支处理因「已在主分支、无 task 分支 checked out」自然 no-op，不重复处理。

**3.5 P6.post-archive Hook（分支处理 + 回顾）**

归档 commit 完成后运行：

```bash
hat-plugin-hook {task-folder} P6.post-archive
```

hook 输出可能包含多段指令，**必须逐段全部执行**（git: 分支合并 + revise tag 清理 + 旧任务归档；retrospective: 流程审查）。插件关闭时对应操作跳过。

**3.6 Retrospective 显式门控（retrospective 启用时）**

post-archive hook 把 git 与 retrospective 两段一起输出，长输出下 retrospective 段易被截断/漏读——故把它提为独立、必过的步骤，不依赖「记得逐段执行」。retrospective 启用时（task-config `retrospective.enabled`），在进入 Step 4 之前必须完成 `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/retrospective.md` 的流程审查：① Process Review（workflow/skill + 配置改进提议）经 AskUserQuestion 逐条 Execute now / Record / Skip；② severity-case 评估。改进涉及改 task skill 时，按 CLAUDE.md 先过 `spec-skill`。

<HARD-GATE>
When retrospective is enabled, the retrospective process review (retrospective.md) must be completed before Step 4, separately from acting on the git segment of the post-archive hook. Do not treat "ran the hook" as "ran the retrospective".
Reason: the post-archive hook emits git + retrospective together; on long output the retrospective segment gets truncated or skipped while the git (branch-handling) segment is acted on, silently dropping the skill's only self-evolution feedback loop (real miss: 2026-06-18-tmux-agent-restore archived with the retrospective skipped). A separate gate makes the review unmissable.
</HARD-GATE>

### Step 4: Confirmation

输出最终清单：

- [x] 验证命令通过（或跳过）
- [x] final.md 已编写
- [x] changelog 已更新
- [x] CLAUDE.md 已更新（如需要）
- [x] 关闭提交中没有泄漏代码变更
- [x] 任务文件夹已归档到 done/
- [x] 分支已处理（如适用）
- [x] Retrospective 流程审查已完成（retrospective 启用时，Step 3.6）
- [x] Linear issue 已同步（如适用）
- [x] Linear 子 issue 已处理（如适用）
- [x] Git 已提交（单次关闭提交）

**[Unattended]** 发送 Telegram 通知 `[task-name] 任务已完成并归档 ✓`。

**如果要取消任务：** 使用 `/task-cancel`。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/plan.md`, `{task-folder}/task-config.json`, `{task-folder}/unattended.json`（`end_decisions.branch`/`end_decisions.squash` 驱动 worktree merge-back 与 squash）, `{task-folder}/.git-base-ref`（git plugin 在 P1 记录，main 连续提交 squash 用）
- **Writes**: `{task-folder}/final.md`, `{task-folder}/phases.md`, `{task-folder}/conversation.md`, `{task-folder}/consumption-report.md`, `docs/unmerged-branches.md`（worktree keep / 冲突时登记）
- **Worktree teardown（核心，仅 worktree 任务，Step 3.4.4）**: 内置 `ExitWorktree(action="keep")` + `git merge --no-ff` / `git worktree remove` / `git branch -d`；物理 `cp -R` 归档文件夹回主仓库、`rm -rf` 主仓库 stub
- **Hooks**: `P6.pre-archive`（git + linear）, `P6.post-archive`（git + retrospective）
- **Scripts**: hat-task-archive, hat-task-detect, hat-plugin-hook, hat-conversation-export
