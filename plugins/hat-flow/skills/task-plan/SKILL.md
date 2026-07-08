---
name: task-plan
user-invocable: false
self-evolving: inbox
description: "Use when executing Phase 3 (Plan + Commit) of a task. Can be called standalone or via /task orchestrator. Do NOT use before the design is approved. 触发词: \"开始规划\", \"task plan\", \"规划阶段\", \"写 plan\", \"生成计划\""
word-budget: 1000
---

# Task Plan — Phase 3: Plan + Commit

任务规划阶段。按模板编写 plan.md、运行 review 轮次、提交任务文档、同步 Linear。

**Announce at start:** "Using task-plan for Phase 3: Plan + Commit."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**phase 入口**（`full` 删上一 phase step + 建本 phase step；`overview`/`off` 不动 step——概览符号由 orchestrator 在 phase 切换时更新）；步骤完成同步 phases.md（`full` 另 `TaskUpdate(completed)`）。

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

> 无人值守的激活入口与契约（quiet / 交互主入口 / 后备入口、activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 只读取已有状态。

---

### 3a. Generate Plan

plan.md 由主 agent 按下方嵌入的 PLAN_PROMPT 模板直接编写；superpowers:writing-plans 等直接生成 plan 的 skill 不在此流程内。规划唯一依据是 PLAN_PROMPT 模板。

- **参考材料**: 完整 design.md、项目文件结构、git 规范、复杂度层级、验证命令（light + full）、commit 指南（git 启用时由 P3.phase-end hook 注入）

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

- review 是否运行由 review plugin 启用状态决定，而非 plan 看起来好不好：plugin 启用时一律跑 hook 派发的 review，不以「plan 已经很好」为由跳过。

**SC2 二元契约**：plan-reviewer 返回 `Verdict: Approved | Issues` + `## Advisory Recommendations` 桶。判据为 `Verdict == Approved`——纯二元，无数值评分、无分数阈值、无 model 分层矩阵、单个 subagent（不按 dimension 拆分派发）。

**Reviewer 解析（codex-aware，派发前先判）**：按 `review.md ## P3.post-plan` 的「Reviewer-aware 派发（codex 分支）」解析 reviewer（读 `plugins.review.reviewer` + `capabilities.codex`；过期/跨 phase → 派发点二次 `codex-check` 刷新）。
- **解析为 `claude`/`sonnet`/`opus`** → 上述 SC2 二元 `Verdict` 契约不变，下方收敛循环按 Verdict 判。
- **解析为 `codex`**（`auto` 且 codex-first 成立亦归此）→ 经 `/codex:rescue`（read-only）派，注入 `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/PLAN_REVIEW.md` 维度 + 项目约定 + plan.md/design.md。输出格式覆盖（仅 codex 路径）：改用 `## Critical/Important/Minor` 三段 + 末行 `Critical=N Important=M Minor=K`，`codex-findings-count` 判 `C=0 & I=0` 收敛。映射到下方循环：`C=0 & I=0` 等价 `Verdict==Approved`，`C>0 或 I>0` 等价 `Verdict==Issues`。派发为串行（无并发）；`max_rounds` reviewer-aware（对象取 `.codex`，缺省 8）；round≥2 经 `SendMessage(to: agentId)` 续接。中途遇 `FALLBACK:`/quota → 降级 native plan-reviewer（恢复 SC2 verdict 判据）并写 `{task-folder}/fallback-log.jsonl`（`phase=P3, integration_point=plan-review, ...`）。claude plan-reviewer 的 SC2 verdict 契约不受此路径影响。

**判断逻辑（收敛循环）：**

- **Verdict == Approved**（Issues 桶为空）→ 进入确认循环。Advisory 桶（如有）仅供参考，不阻断。
- **Verdict == Issues** → 主 agent 批判性评估 Issues 桶每条 Critical / Important 发现（Accept/Reject 附理由），修复接受的问题后重跑 hook 评估。循环直到 Verdict == Approved 或达 `max_rounds`。
- max_rounds 退出时：AskUserQuestion：**接受当前状态推进** / **重新生成 plan** / **手动修改**

**确认循环（Plan review 收敛后）：**

1. Verdict == Approved 后，展示**本轮 review 修改的变更差异**（仅本轮，非累积）
2. 纯文本询问用户是否有补充："以上是 Plan review 的修改内容，是否有补充？回复「继续」推进到提交。"
3. 用户说"继续" → 推进到 3c
4. 用户给建议 → 澄清 → 修改 plan.md → 判断是否重跑 Plan review：
   - 修改涉及步骤结构、依赖关系、文件路径 → 必须重跑 review
   - 仅描述文字调整 → 可跳过
   - 若重跑：展示新一轮差异 → 回到步骤 2

**变更差异显示规则**：每轮重置，只展示从上次确认点到现在的改动。

完成后：更新 phases.md，将 `3b. Plan 忠实度评估` 标记为 `[x]`。

### 3c + 3d: P3.phase-end (Commit + Linear Sync)

由 `P3.phase-end` hook 统一处理 git 提交 + Linear 同步：

```bash
hat-plugin-hook {task-folder} P3.phase-end
```

hook 输出可能包含多段指令，**必须逐段全部执行**（git: 提交任务文档；linear: 同步状态）。插件关闭时对应操作自动跳过。

**产物验证（hook 执行完毕后）：**

git plugin 启用时，验证 commit 是否成功创建：`git log --oneline -1` 确认最新 commit 包含任务文档。若 commit 缺失，主 agent 手动执行 `git add` + `git commit`——手动提交时只 `git add` 任务文档的具体文件路径，不用 `git add -A`（避免把无关改动一并提交）。

<rule>
P3.phase-end hook 完成后，commit 产物经验证才算落地：git plugin 启用而 commit 未创建时，由主 agent 手动 fallback 提交补齐。
Reason: 未提交的任务文档在 context compact 后会丢失，且 Phase 4 subagent 无法读取未提交的文件。
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

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
Phase skill 完成后的去向是返回编排器 Step 3；过渡路由归编排器，transition section 不提示用户调用其它 skill。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、新会话交接、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 3b | plan review 收敛（Verdict==Approved）后（仅 Interactive） | 展示本轮 review 差异 + 纯文本确认是否有补充 |
| 3d | Linear 操作失败（仅 Interactive） | 重试 / 跳过 |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/plan.md`, `{task-folder}/phases.md`
- **Pre-injected**: `PLAN_PROMPT.md`（plan 模板单一来源）
- **Hooks**: `P3.post-plan`（review: 忠实度评估）, `P3.phase-end`（git: 提交, linear: 同步）
- **Scripts**: hat-plugin-hook
