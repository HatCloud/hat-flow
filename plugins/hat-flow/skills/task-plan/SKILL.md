---
name: task-plan
user-invocable: false
description: "Use when executing Phase 3 (Plan + Commit) of a task. Writes plan.md, runs review rounds, commits task documents, syncs Linear. Can be called standalone or via /task orchestrator. 触发词: \"开始规划\", \"task plan\", \"规划阶段\", \"写 plan\", \"生成计划\""
---

# Task Plan — Phase 3: Plan + Commit

任务规划阶段。按模板编写 plan.md、运行 review 轮次、提交任务文档、同步 Linear。

**Announce at start:** "Using task-plan for Phase 3: Plan + Commit."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

## Red Flags

| If you think... | Reality |
|---|---|
| "The plan looks good, no need for review" | Review rounds are determined by complexity, not by how good the plan looks. |
| "I can skip Linear sync, it's optional" | If linear.json exists, Linear sync is NOT optional. |
| "All tasks are similar, I'll use vague step descriptions" | Every step must be a specific action with exact file paths. No placeholders. |
| "I'll commit selectively to save time" | Use the archive script or git add specific files — never git add -A for the plan commit. |

---

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），**先**从 phases.md 重建概览行（确保拿到最小 ID 以固定在首行）并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。

---

## Resume Support

如果 phases.md 存在且 Phase 3 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 3 步骤对应：**
- `3a. 生成 plan` → Step 3a
- `3b. Plan 忠实度评估` → Step 3b
- `3c. 提交任务文档` → Step 3c
- `3d. Linear 同步` → Step 3d

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取（或由编排器传入）。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守模式的激活（unattended.json 创建）统一由 `/task` 编排器的 Step 2A.1 处理。各阶段 skill 仅负责读取已有状态。

---

### P3 起始时间戳（core timing，内联）

内联记录 phase_start（helper 自带顶层 `observability.enabled` 门控，关闭档 → no-op）：

```bash
hat-timing-stamp {task-folder} phase_start P3
```

### 3a. Generate Plan

Do NOT use superpowers:writing-plans or any skill that generates plans directly. Planning MUST follow PLAN_PROMPT 模板。

主 agent 按下方嵌入的 PLAN_PROMPT 模板直接编写 plan.md：
- **参考**: 完整 design.md、项目文件结构、git 规范、复杂度层级、验证命令（light + full）、commit 指南（git 启用时由 P3.phase-end hook 注入）

#### PLAN_PROMPT (pre-loaded):

plan 模板（Plan Format / File Structure 职责图 / Dependency 并行切割 / Bite-Sized / TDD / Verification / Commit Checkpoint / Forbidden Patterns / Self-Review）的单一来源是下方 `!cat` 嵌入的 PLAN_PROMPT.md——本文件不重述其内容。

<PLAN_PROMPT>
!`cat ${CLAUDE_PLUGIN_ROOT}/skills/task/PLAN_PROMPT.md`
</PLAN_PROMPT>

---

### P3.post-plan Hook

plan.md 编写完成后，运行：

```bash
hat-plugin-hook {task-folder} P3.post-plan
```

按输出指令执行（review plugin: Plan 忠实度评估，含 design 一致性检查）。review plugin 关闭时跳过。

hook 完成后：在终端输出可视化任务清单：

```
## 执行任务清单
- [ ] Task 1: [标题]
- [ ] Task 2: [标题]
...（共 N 个任务）
```

> **注意**：此处仅文本展示，不创建 Exec 级 TaskCreate。各 plan task 的 TODO 拆分在 Phase 4 (Execute) Bootstrap 时统一创建——避免 Phase 3 还未提交就在终端显示大量 pending 任务。

完成后：更新 phases.md，将 `3a. 生成 plan` 标记为 `[x]`。

### 3b. Plan Fidelity Review

> **review 派发由上方 `P3.post-plan` hook 委托 review plugin 执行**（单个 `plan-reviewer` subagent，注入 plan.md + design.md，跑一次 single-pass review）。本节是 hook 返回后的**编排循环薄层**：读 Verdict、收敛、确认。review plugin 关闭时跳过本节，直接标记 `3b` 为 `[x]`。

**SC2 二元契约**：plan-reviewer 返回 `Verdict: Approved | Issues` + `## Advisory Recommendations` 桶。**不做数值评分、不算分数阈值、不按 model 分层矩阵分配、不按 dimension 派多个 subagent**。判据为 `Verdict == Approved`。

**判断逻辑（收敛循环）：**

- **[Unattended] 前置分支**：
   - `Verdict == Approved`（Issues 桶为空）→ **跳过确认循环**，直接推进到 3c。
   - `Verdict == Issues` → 修复后重跑一次，仍 Issues → Telegram 通知暂停。
- **[Interactive] Verdict == Approved**（Issues 桶为空）→ 进入确认循环。Advisory 桶（如有）仅供参考，不阻断。
- **Verdict == Issues** → 主 agent 批判性评估 Issues 桶每条 Critical / Important 发现（Accept/Reject 附理由），修复接受的问题后重跑 hook 评估。循环直到 Verdict == Approved 或达 `max_rounds`。
- max_rounds 退出时：
   - **[Interactive]** AskUserQuestion：**接受当前状态推进** / **重新生成 plan** / **手动修改**
   - **[Unattended · `degrade_policy` standard 或缺省]** 不询问，发送 Telegram 通知后暂停（任务保留，等待 `/task` 恢复人工决策）
   - **[Unattended · `degrade_policy` conservative / headless]** 走 `UNATTENDED_PROTOCOL.md` §9 **A4 accept-with-findings**：剩余未解决 Issues 原文写入 plan.md 的 `## Unresolved Review Findings` 段 + `unattended-decisions.md` 的 `## Headless Degraded Decisions`，续跑推进；**同点至多一次**——本 phase 已 A4 续跑过则第二次退回 standard（暂停 + Telegram）。兜底：P4 review + P5 验收双网。

**确认循环（Plan review 收敛后）：**

1. Verdict == Approved 后，展示**本轮 review 修改的变更差异**（仅本轮，非累积）
2. 纯文本询问用户是否有补充："以上是 Plan review 的修改内容，是否有补充？回复「继续」推进到提交。"
3. 用户说"继续" → 推进到 3c
4. 用户给建议 → 澄清 → 修改 plan.md → 判断是否重跑 Plan review：
   - 修改涉及步骤结构、依赖关系、文件路径 → 必须重跑 review
   - 仅描述文字调整 → 可跳过
   - 若重跑：展示新一轮差异 → 回到步骤 2

**[Unattended]** 跳过整个确认循环（步骤 1-4）。当 `Verdict == Approved` 时不询问“是否有补充/继续”，直接推进到 3c；当 `Verdict == Issues` 时按上文无人值守分支（修复后重跑一次，仍 Issues 则 Telegram 通知暂停）。

**变更差异显示规则**：每轮重置，只展示从上次确认点到现在的改动。

完成后：更新 phases.md，将 `3b. Plan 忠实度评估` 标记为 `[x]`。

### 3c + 3d: P3.phase-end (Timestamp + Commit + Linear Sync)

先内联记录 P3 phase_end 时间戳（core timing，须在 hook 之前），再由 `P3.phase-end` hook 统一处理 git 提交 + Linear 同步：

```bash
hat-timing-stamp {task-folder} phase_end P3
hat-plugin-hook {task-folder} P3.phase-end
```

> **Subagent**：linear 在 P3.phase-end 为 `subagent:linear-sync` hook。`hat-plugin-hook` 输出 DISPATCH 指令，编排器据此派一次性后台 subagent 异步执行（见 task/SKILL.md Subagent Async Dispatch）。

hook 输出可能包含多段指令，**必须逐段全部执行**（git: 提交任务文档；linear: 同步状态）。插件关闭时对应操作自动跳过。

**产物验证（hook 执行完毕后）：**

git plugin 启用时，验证 commit 是否成功创建：`git log --oneline -1` 确认最新 commit 包含任务文档。若 commit 缺失，主 agent 手动执行 `git add` + `git commit`。

<rule>
P3.phase-end hook 执行后必须验证 commit 产物。若 git plugin 启用但 commit 未创建，主 agent 必须 fallback 手动提交。
Reason: 未提交的任务文档在 context compact 后会丢失，且 Phase 4 subagent 无法读取未提交的文件。
</rule>

<rule>
P3 timing 经内联 `hat-timing-stamp`（phase_start/phase_end），须排在 P3.phase-end hook 调用之前。helper 自带 `observability.enabled` 门控（关闭档 → no-op）。
Reason: 内联 timing 是确定动作；缺 phase_start 触发 artifact-check 硬 FAIL，故内联点须前置、先于 P3.phase-end 的 git/linear blocking 段。
</rule>

完成后：更新 phases.md，将 `3c. 提交任务文档` 和 `3d. Linear 同步` 标记为 `[x]`。

---

## phases.md Sync

每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

**Pre-check before Phase 3 Stop**: P3.phase-end hook 执行完毕后检查结果。

**Phase 3 完成时**：将 Phase 3 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

---

## Plan 完成 → 过渡

Phase 3 完成，phases.md 已更新。

用用户配置的语言简要宣告规划结果（plan.md 位置、task 数量、Linear 同步状态），然后声明：**"Plan 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

**[Unattended]** 若无人值守模式激活：发送 Telegram 通知 `[task-name] Phase 3 完成`。

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
Phase skill 完成后必须返回编排器 Step 3。不得在 transition section 中提示用户调用任何其他 skill。过渡路由是编排器的职责。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、compact、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 3b | plan review 收敛（Verdict==Approved）后（仅 Interactive） | 展示本轮 review 差异 + 纯文本确认是否有补充 |
| 3d | Linear 操作失败（仅 Interactive） | 重试 / 跳过 |

**[Unattended]** 上表两个停顿点均不询问：
- 3b：`Verdict == Approved` 直接推进；`Verdict == Issues` 按无人值守分支执行。
- 3d：按协议做一次重试，仍失败则 Telegram 告警并暂停（不等待用户应答）。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/plan.md`, `{task-folder}/phases.md`
- **Pre-injected**: `PLAN_PROMPT.md`（plan 模板单一来源）
- **Hooks**: `P3.post-plan`（review: 忠实度评估）, `P3.phase-end`（git: 提交, linear: 同步）
- **Core timing**（内联，非 hook）: phase_start P3（阶段开始）/ phase_end P3（P3.phase-end hook 之前）经 `hat-timing-stamp`，受顶层 `observability.enabled` 门控
- **Scripts**: hat-plugin-hook, hat-timing-stamp
