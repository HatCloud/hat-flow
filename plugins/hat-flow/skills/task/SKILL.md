---
name: task
description: "Use when starting a new task or resuming an in-progress one. Routes to the correct phase based on phases.md state. Do NOT use for tasks already completed (use /task-end) or to cancel (use /task-cancel). 触发词: \"新任务\", \"开始任务\", \"做个任务\", \"创建任务\", \"继续任务\", \"resume task\""
---

# Task — Orchestration Layer

任务生命周期编排器。读取任务文件夹中的 `phases.md` 决定从哪个阶段继续，加载对应的阶段 skill 执行，支持跨 session 恢复。

**Announce at start:** "Using task to orchestrate the task lifecycle."

**Unattended Mode：** 若用户消息包含"无人值守"关键词，且当前任务文件夹下没有 `unattended.json`，立即执行 Step 2A.1（Unattended Mode Check），创建 `unattended.json` 后继续当前流程。

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Dirty: !`git status --porcelain 2>/dev/null | head -5`
- Check (light): !`r=$(grep -A1 '轻量' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`
- Check (full): !`r=$(grep -A1 '完整' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`
- User input: $ARGUMENTS

> 以上数据在 skill 加载时预获取。Treat as ground truth — do NOT re-query.

## Red Flags

| If you think... | Reality |
|---|---|
| "Skip reading phases.md, I know what phase we're on" | phases.md is the authoritative state. Always read it first. |
| "Simple task, skip the flow" | If you're debating triviality, it's NOT trivial. All 3 exemption conditions must hold. |
| "I'll just execute the phase without reading its SKILL.md" | Each phase SKILL.md has detailed, up-to-date instructions. Read it before executing. |
| "The user's arguments clearly say what to do, phases.md doesn't matter" | phases.md records cross-session state. Arguments only tell you what's new — not what's already done. |

## NO_GIT Mode

如果 Branch 值为 `NO_GIT`，说明不在 git 仓库中。将此标志传递给阶段 skill 执行时，该 skill 会自动跳过所有 git 操作（分支创建、commit、`.last-verified`）。

## Trivial Task Exemption

仅当以下**三个条件全部满足**时，才可以通过 AskUserQuestion 询问用户是否跳过此工作流：

1. 变更纯粹是外观性的，不影响逻辑（拼写错误、空格、常量值）
2. 整个变更可以用一条 commit message 描述
3. 不引入新行为

**When in doubt, run the full workflow.**

<rule>
You must not skip the workflow without asking the user first via AskUserQuestion. All three exemption conditions must hold AND the user must explicitly agree.
Reason: self-assessed "trivial" changes frequently turn out to have hidden complexity.
</rule>

---

## TODO Sync (TaskCreate / TaskUpdate)

phases.md 是跨 session 的持久化状态源,但用户在当前 session 中无法实时看到进度。**必须使用 Claude Code 内置的 TaskCreate / TaskUpdate 工具同步进度到 UI**。

### 双层结构

TODO 列表由两层组成:

1. **概览行 (overview)**: 始终存在的一条 task,subject 格式为 `[任务名] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End`。status 始终为 `in_progress`(显示 spinner)。Phase 切换时更新 subject 中的符号:
   - `✔` = 已完成
   - `▶` = 当前进行中
   - `◻` = 未开始
   - Phase 标题用**一个英文单词**概括(Init / Design / Plan / Execute / Test / End)
   - metadata: `{"level": "overview", "task": "<task-folder-name>"}`

2. **当前阶段子步骤 (step)**: 当前 phase 的每个步骤一条 task,subject 前缀 `→`。Phase 切换时:**删除旧阶段所有 step 级 task,创建新阶段的 step 级 task**。metadata: `{"level": "step", "phaseNum": N, "stepId": "Na"}`

### 显示效果

```
◼ [M0] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End
◻ → 3a. 生成 plan
◻ → 3b. Plan 忠实度评估
◻ → 3c. 提交任务文档
◻ → 3d. Linear 同步
```

### 生命周期规则

1. **任务启动时 (Phase 1 开始)**: **先**创建概览行 `[任务名] ▶P1:Init ◻P2:Design ◻P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End` 并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 Phase 1 的 step 级 task（概览行必须拿到最小 ID 以固定在首行）。
2. **Phase 切换时**:
   - 删除当前阶段所有 `level: "step"` 的 task (TaskUpdate status: deleted)
   - 更新概览行 subject (把完成的 phase 改 `✔`,新 phase 改 `▶`)
   - 创建新阶段的 step 级 task
3. **步骤开始时**: `TaskUpdate(status: "in_progress")`
4. **步骤完成时**: `TaskUpdate(status: "completed")` + 同步更新 phases.md
5. **跨 session 恢复时**: TaskCreate 列表丢失(session 级)。恢复时先 `TaskList` 检查是否已有 `level: "overview"` 的 task；若有则 `TaskUpdate` 更新 subject，若无则**先**从 phases.md 重建概览行（确保拿到最小 ID）并**立即** `TaskUpdate(status: "in_progress")`。**然后**再重建当前阶段 step 级 task，已完成步骤标记 completed。
6. **任务结束时 (`/task-end`)**: 概览行标记 completed,所有 step 级 task 删除。

<rule>
Every phase skill execution MUST maintain the two-layer TODO structure: one overview line + current phase steps. phases.md and TaskCreate/TaskUpdate must stay in sync at all times.
Reason: phases.md is invisible to the user during the session. The two-layer TODO is the only way the user sees both overall progress and current-step granularity.
</rule>

---

## Hook Execution Routing

每个 plugin hook 在 manifest 中声明 `execution` 模式，编排器据此路由：

| `execution` | 路由 |
|---|---|
| `inline`（缺省） | `hat-plugin-hook` 正常输出指令正文，主线程同步执行（当前行为） |
| `subagent:{name}` | 不在主线程执行；`hat-plugin-hook` 改为输出 `<!-- DISPATCH ... -->` 指令，编排器据此派一次性后台 subagent 异步执行（见 Subagent Async Dispatch） |

`hat-plugin-hook` 默认对 `execution != inline` 的 hook **不输出指令正文**，而是输出一条机器可读的 `<!-- DISPATCH ... -->` 指令（并 stderr 提示 `[subagent] ...dispatched async`）。脚本**无状态、不检测任何环境变量**——每次按当前 manifest config 重新路由。`--no-filter` 参数强制全部 hook 输出 inline 正文（降级 / 测试逃生口）。

> **subagent 模式不依赖任何实验特性 flag**：`Agent` 工具对主线程恒可用，无 agent-teams 类实验开关依赖，无常驻成员生命周期、无跨 session 蒸发问题（一次性派发，结束即自终结）。

## Subagent Async Dispatch

每个 phase skill 运行 `hat-plugin-hook {task-folder} {hook-point}` 后，编排器对其 **stdout** 的统一处理（**不下沉到各 phase skill** 的 hook 调用点逻辑）：

```
逐行读 hat-plugin-hook stdout：
  - inline section（注释头 `<!-- plugin:.. execution:inline -->` + 正文）
        → 主线程同步执行该指令
  - DISPATCH 指令 `<!-- DISPATCH plugin:P hook:H name:N model:M subagent_type:T section:S -->`
        → 编排器先从 `{P}.md` targeted 抽取 `## {H}` 与 `{S}`（即 `## Subagent Context`）两段 section 正文（按 `## ` 标题切片；{P}.md 仅约 200 行，抽 2 段成本极低），拼进派发 prompt；
          （**事实注入**：P3.phase-end 注入主线程从 design.md 提取的 Overview 1-2 行；P6.pre-archive 注入主线程从 final.md 提取的 3-5 行摘要——均由主线程提取后注入，subagent 不读源文档；见 B1/B2）
          Agent(subagent_type=T, model=M, run_in_background=true,
                prompt = "你是被派发的一次性 N subagent，负责插件 P 的 H 异步执行。
                          **按下方已注入的 section 正文执行，不要 Read {P}.md / design.md / plan.md / final.md**：
                          〈## {H} 正文〉…〈## Subagent Context 正文〉〈事实注入文本：P3=design Overview / P6=final.md 摘要 / 其他 hook 省略〉
                          task-folder={task-folder 绝对路径}；仅 Read {task-folder}/linear.json 取 issueUuid；
                          幂等；失败在 result 文本写明（graceful）。")
          fire-and-forget，不等待、不设超时，继续主流程
```

- **completion notification**：派发的后台 subagent 结束时回传 notification。主线程 graceful 吸收（记 timing.jsonl 或忽略），**不阻塞**——异步语义。
- **错误处理**：subagent 无 `SendMessage`，失败只在其 result 文本体现。主线程收到 notification 后按该 hook `on_error` 处理：`graceful`（Linear 全部为 graceful）→ 记 timing.jsonl 继续；`blocking` → 降级主线程 inline 重试。无响应不阻塞主流程——代价是该次同步静默丢失，由幂等性 + 下个 phase / P6 兜底覆盖。
- **resume 安全**：一次性 subagent 无跨 session 状态；resume 中途丢失顶多丢一次同步（幂等覆盖），无 team / 陈旧字段需清理或重建。

---

## Phase Routing

<rule>
Read phases.md before deciding which phase to run. The phase skill's instructions override the orchestrator's general guidance once loaded.
Reason: phases.md is the only cross-session state source. The phase SKILL.md has the authoritative step-by-step instructions for each phase.
</rule>

### Step 1: Determine State

**A. Check open tasks** (from Runtime Context Tasks JSON):

- **No open tasks** AND `$ARGUMENTS` 为空 → AskUserQuestion 询问任务描述
- **No open tasks** → 新任务，跳到 Step 2A（Init）
- **1 open task** → 读取该任务文件夹的 `phases.md`（如果存在），跳到 Step 2B（Resume）
- **多个 open tasks** → AskUserQuestion 让用户选择；选定后跳到 Step 2B（Resume）

**B. Trivial Task Check** (仅对新任务): 如果 `$ARGUMENTS` 满足全部 3 个免除条件，AskUserQuestion 确认后跳过工作流。

### Step 2A: New Task — Phase 1

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md
```

读取完成后，按照 `task-init/SKILL.md` 的指示执行 Phase 1 的全部步骤。

Phase 1 完成后（task-init SKILL.md 指示 DONE），执行 **Step 2A.1**，然后继续 Step 3。

### Step 2A.1: Unattended Mode Check（Phase 过渡时）

> **主要激活入口已移至 P2 Step 2e 配置面板。** Phase 过渡时的询问为后备入口，仅当 Phase 1/2/3 完成且 unattended.json 不存在时触发。

在以下任一时机执行（刚标记为 DONE 且 `unattended.json` 不存在）：
- Init 完成 → 进入 Design
- Design 完成 → 进入 Plan
- Plan 完成 → 进入 Execute

1. 读取 `{task-folder}/unattended.json`
   - **declined 短路（最先判断）**：若文件存在且 `declined == true` → 用户已拒绝无人值守，静默继续、不询问、不进激活分支、不推断 `activate_after`（见 `UNATTENDED_PROTOCOL.md` §5）。跳过本 Step 2A.1 剩余步骤。
2. 若文件不存在：AskUserQuestion——无人值守激活时机？（共享契约 SC3，措辞与 task-design Activation Timing 一致）
   - **现在启用** — 立即进入无人值守，写 `unattended.json`（`enabled: true`, `activate_after: "now"`）
   - **Design 阶段结束后启用** — 本阶段仍交互，写 `unattended.json`（`enabled: false`, `activate_after: "design"`），由 Step 3 在 Design 完成后激活
   - **Plan 阶段结束后启用** — Design + Plan 交互，写 `unattended.json`（`enabled: false`, `activate_after: "plan"`），由 Step 3 在 Plan 完成后激活
   - **否** — 全程交互，写拒绝哨兵 `unattended.json`（`{"enabled": false, "declined": true}`），使后续过渡点不再重复询问
3. 若选择 **现在启用**：追问任务类型（AskUserQuestion）：
   - **自测任务（Recommended）** — 自动推进到 task-end
   - **需要用户测试** — 推进到 task-test 完毕后 Telegram 通知（经 `UNATTENDED_PROTOCOL.md` §4，opt-in；未配置则静默降级）
   选 **自测任务** 时再追加 End 阶段决策收集（分支处理：自动合并到 main / 保留分支；CLAUDE.md 更新：自动更新 / 跳过），写入 `unattended.json` 的 `end_decisions` 字段
4. 按 `UNATTENDED_PROTOCOL.md` 第 5 节（How to Create unattended.json）创建文件：现在启用 → `enabled: true`；选 design/plan → `enabled: false` + 对应 `activate_after`
5. 若文件已存在：静默继续（无人值守状态已记录，不重新询问；延后激活由 Step 3 在匹配过渡点翻 `enabled`）

**[Unattended]** 此处为无人值守询问入口本身——已有 unattended.json（含延后激活的 `enabled:false`）时静默继续，不阻塞。

<rule>
When an AskUserQuestion is rejected/dismissed without a semantic answer, do NOT infer a default value or treat the rejection as selecting any option. Confirm the user's intent in plain text first.
Reason: a dismissed prompt is not a choice — inferring "the user meant the recommended option" silently commits a decision (branch strategy, unattended activation, scope) the user never made. This applies to all AskUserQuestion calls across the workflow, including Interactive-mode stop points where a UI rejection differs from an actual answer.
</rule>

### Step 2B: Resume Existing Task

读取恢复所需的状态文件：

1. 读取 `{task-folder}/phases.md`（进度状态）
2. 读取 `{task-folder}/task-config.json`（插件配置）— 不存在时降级：
   - 从 `{task-folder}/design.md ## Execution Strategy` 推断基本配置
   - 仍无法推断 → 使用 standard preset 默认值
   - 降级时**不**写入 task-config.json（留给 P2 Step 2e 正式生成）
3. 读取 `{task-folder}/unattended.json`（无人值守状态，可选）
4. **追加当前 session-id**：跨 session 恢复时，本次的 `$CLAUDE_CODE_SESSION_ID` 可能不在 `{task-folder}/session.json` 的 `sessions` 数组中。若该 id 非空且不在数组则追加（保持 `{"sessions": [...]}` schema）；`session.json` 不存在则创建。这样多 session 任务的会话导出（task-end / `/dogfooding`）能覆盖全部 session。env 缺失或写失败 → 跳过（不阻断恢复）。

   ```bash
   sid="${CLAUDE_CODE_SESSION_ID:-}"; sj="{task-folder}/session.json"
   [ -n "$sid" ] && python3 -c 'import json,sys,os
   sj,sid=sys.argv[1],sys.argv[2]
   d={"sessions":[]}
   if os.path.exists(sj):
       try: d=json.load(open(sj))
       except Exception: d={"sessions":[]}
   d.setdefault("sessions",[])
   if sid not in d["sessions"]: d["sessions"].append(sid); json.dump(d,open(sj,"w"))' "$sj" "$sid" 2>/dev/null || true
   ```

**先检查 Revise section，再检查 Phase 状态**。

#### Revise Section 路由（最高优先级）

在检查 Phase 路由表之前，扫描 phases.md 中所有 `## Revise RN` section。下表**从上到下优先匹配，命中第一条即执行**（故存在 IN_PROGRESS 时优先于任何 DONE/DEFERRED 的收尾判定）：

| Revise section 状态 | 操作 |
|---|---|
| 存在 `Status: IN_PROGRESS` 的 Revise section | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-revise/SKILL.md` → 执行该 Revise Cycle（多个 IN_PROGRESS 取编号最大的，其余标 `DEFERRED`，Reason=被取代） |
| 存在 `Status: DONE` 且 Return 步骤仍为 `[ ]` | 路由回原 phase skill（由 Return 字段指定），phase skill 进入**回归模式**重跑触发步骤。DONE 路由回原 phase **要求 Return 步骤为 `[ ]`**（待回归） |
| `Status: DEFERRED`（升级转人工 / 转新任务的终态） | **无条件终结**——识别为"已终结、不再路由执行"，**不依赖 Return 步骤是否 `[x]`**；半成品已在 `**WIP Commit**` 记录的 commit 中承接 |
| 所有 Revise section 均为 DONE/DEFERRED 且 DONE 的 Return 步骤为 `[x]` | 忽略这些 section，继续下方 Phase 路由 |

**编排器层错误处理**：
- phases.md 格式损坏（无法解析 Revise section）→ AskUserQuestion：手动修复 / 忽略 Revise 继续正常路由
- Revise section 引用的 Return 步骤不存在 → 忽略该 Revise section，按正常 Phase 路由

#### Phase 路由

根据各 Phase 的 `**Status**` 字段路由：

| phases.md 中的状态 | 操作 |
|---|---|
| Phase 1 Status = PENDING 或 IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md` → 执行 Phase 1（跳过已完成步骤） |
| Phase 1 = DONE，Phase 2 = PENDING 或 IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-design/SKILL.md` → 执行 Phase 2（跳过已完成步骤） |
| Phase 2 = DONE，Phase 3 = PENDING 或 IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-plan/SKILL.md` → 执行 Phase 3（跳过已完成步骤） |
| Phase 3 = DONE，Phase 4 = PENDING 或 IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-execute/SKILL.md` → 执行 Phase 4（跳过已完成步骤） |
| Phase 4 = DONE，Phase 5 = PENDING 或 IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-test/SKILL.md` → 执行 Phase 5（跳过已完成步骤） |
| Phase 5 = DONE，Phase 6 = PENDING（普通模式） | 告知用户："所有测试已完成，请调用 `/task-end` 关闭任务。" **硬停，不自动推进。** |
| Phase 5 = DONE，Phase 6 = PENDING（无人值守 self_test） | 读取 `unattended.json`；若 `task_type == "self_test"` → `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-end/SKILL.md` → 自动执行 Phase 6 |
| Phase 6 = IN_PROGRESS | `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-end/SKILL.md` → 继续执行 Phase 6（跳过已完成步骤） |

**如果 phases.md 不存在**（任务文件夹存在但没有 phases.md）：
- 检查是否有 `plan.md` → 路由到 Phase 4（若 Phase 4 已 DONE 则路由到 Phase 5）
- 检查是否有 `design.md` → 路由到 Phase 3
- 两者都没有 → 路由到 Phase 2

<HARD-GATE>
Before executing any step of any phase, you MUST Read that phase's SKILL.md in the current turn. Never execute a phase from memory or from a conversation summary.
Reason: each phase SKILL.md carries the hook calls (observability/review/git/linear) that produce the phase's artifacts. Skipping the read silently skips the hooks, and the task archives with missing artifacts — the failure stays invisible until task-end. Real case: bin-unit-tests L866 claimed "read task-end SKILL.md" but never actually read it, so P5/P6 hooks never ran and conversation.md was never generated. This is a HARD-GATE, not a soft rule: a missed read poisons every downstream artifact.
</HARD-GATE>

**Rationalization 表**（执行任何 phase 前自检——命中任意一条即停下，先 Read 当前 phase SKILL.md）：

| Rationalization | Reality |
|---|---|
| "我记得这个 phase 的步骤，不用再读 SKILL.md" | 记忆会漏掉 hook 调用。phase SKILL.md 是当前权威，当前 turn 必须 Read。 |
| "summary / 上下文里已经有 phase 内容了" | summary 是压缩产物，hook 命令常被省略。读原文。 |
| "上一个 session 我读过这个 SKILL.md" | 跨 session 记忆不可靠，且 SKILL.md 可能已更新。重读。 |
| "这个 phase 很简单，直接做就行" | 觉得简单正是漏 hook 的高发场景（bin-unit-tests 元 bug 即如此）。 |

### Step 3: Continue to Next Phase

**Phase 过渡类型表**（各边界的交互程度，用语义描述以避免 phase_merge 后序号变化）：

| 过渡边界 | 产物检查 | Compact 建议 | Unattended 检查 | 停顿类型 |
|---------|----------|-------------|----------------|----------|
| Init 完成后 | ✓ | — | ✓ | 有交互点（unattended 询问） |
| Design 完成后 | ✓ | 降级时* | ✓ | 有交互点（unattended 询问） |
| Plan 完成后 | ✓ | **✓（必触发）** | ✓ | **软停顿**（compact 建议等待用户回复） |
| Execute 完成后 | ✓ | — | — | 产物检查通过后推进 |
| Test 完成后 | **✓（P5 门控）** | — | — | **硬停**（用户必须调用 `/task-end`） |

*降级：phase_merge 将 Plan 和 Execute 合并时，compact 建议前移到 Design 完成后

每个阶段完成后，该阶段的 SKILL.md 会负责更新 `phases.md`。返回此处：
1. 读取更新后的 `phases.md`，确认当前阶段已标记为 DONE
1.1. **phase_merge 检查**：读取 `{task-folder}/task-config.json` 的 `phase_merge` 字段。检查当前完成的阶段和下一个阶段是否在某个 merge 组中。
   - **匹配且下一阶段不是 End** → 跳过步骤 1.5（产物检查）、步骤 2（compact）、步骤 3（unattended），直接加载下一阶段的 SKILL.md
   - **不匹配** → 正常执行后续步骤
   - **硬约束**：Test→End 永不可合并——即使 phase_merge 包含该组合，仍执行 End 准入检查（硬停）
1.5. **产物完整性门控**：运行 `hat-task-artifact-check {task-folder} {完成的phase编号}` （如 task-config.json 存在，追加 `--config {task-folder}/task-config.json`）。
   - **PASS** → 继续
   - **FAIL** → 尝试 fallback 补齐缺失文件（主 agent 按 task-config 与 design.md 补齐）。补齐后重跑检查。
   - 仍 FAIL → 阻断推进，告知用户缺失的文件列表
   - **Timing 检查**：脚本校验 timing.jsonl 含 `P{N}` 的 `phase_end`——缺 `phase_end` 为**非阻断警告**（WS-D，不挡推进），缺 `phase_start` 为**硬 FAIL**；observability 关闭时 timing 检查整体 no-op（fail-open）
2. **Compact 建议**（仅 Plan 完成后、且 Interactive 模式触发）：
   - **前置门（最先判断）**：读取 `{task-folder}/unattended.json`。若 `enabled == true`（已是无人值守），**或** `enabled == false` 且 `activate_after` 匹配当前过渡点（本过渡点步骤 3 即将激活无人值守）→ **完全跳过本步，不输出任何 `/compact` 块**，直接进入步骤 3。这是前置条件判断，不是"先输出再说跳过"。
   - **触发条件**（仅 Interactive）：刚完成的阶段是 Plan
   - **降级规则**：若 phase_merge 将 Plan 和 Execute 合并，触发点前移至 Design 完成后
   - **Hotfix 例外**：若 `task-config.json` 中 `todo_sync == false` 或 `p5_auto_only == true`，跳过 compact 建议
   - **其他过渡**：不给 compact 建议
   - 触发时无条件给出 compact 建议（不评估上下文大小），提供可直接复制的 compact 命令
   - 建议后等待用户回复。用户可选择 compact 后用 `/task` 恢复，或直接说"继续"跳过 compact

**[Unattended]** compact 软停是面向交互用户的停顿——前置门跳过 `enabled:true`（已激活）与"本过渡点即将激活（`enabled:false` 且 activate_after 匹配）"两种无人值守情形，不输出任何等待用户回复的 `/compact` 块（见上方 HARD-GATE）。

<HARD-GATE>
In unattended mode, never emit a /compact block at the Plan→Execute boundary. Check unattended.json FIRST and skip the entire compact step before producing any output.
Reason: a /compact suggestion is a soft stop that waits for a user reply. In unattended mode there is no user to reply, so emitting it stalls the flow indefinitely — exactly the bin-unit-tests failure. The guard must be a precondition, not an after-the-fact "[Unattended] skip", because the latter still risks emitting the block before the skip is evaluated.
</HARD-GATE>
3. **Unattended Mode Check**（仅刚完成的是 Init、Design 或 Plan 时执行；判定顺序：先 declined 短路，再 activate_after 激活，再"文件不存在→询问"）：
   - **3-a0. declined 短路（最先判断，优先于 activate_after）**：读取 `{task-folder}/unattended.json`。若文件存在且 `declined == true` → 用户已拒绝无人值守，静默继续、不询问、不进激活分支、不推断 `activate_after`。跳过 3-a/3-b/3-c。（declined 哨兵无 `activate_after`，必须显式短路，避免 §1「缺省视为 now」误读为待激活，见 `UNATTENDED_PROTOCOL.md` §5）
   - **3-a. activate_after 激活分支（共享契约 SC3 consumer 侧，对接 task-design producer）**：读取 `{task-folder}/unattended.json`。若文件存在 且 `enabled == false` 且 `activate_after` 匹配当前过渡点（`activate_after == "design"` 且刚完成 Design / `activate_after == "plan"` 且刚完成 Plan）→ 把 `enabled` 字段写回为 `true`，并 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md` 加载无人值守协议（自此进入无人值守）。激活后发送 Telegram 通知（`[task-name] 无人值守模式已激活`；chat_id 为 null 时按 `UNATTENDED_PROTOCOL.md` §4 跳过发送并打印降级告警）。
   - **3-b. 文件不存在 → 询问分支**：若 `unattended.json` 不存在 → 执行 Step 2A.1（询问无人值守激活时机）
   - **3-c.** 其余情况（文件存在且 `enabled == true`，或存在但 `activate_after` 不匹配当前过渡点且非 declined）：静默继续，不询问

**[Unattended]** 步骤 3 的激活/询问自身可无人值守推进：activate_after 匹配 → 自动翻 `enabled`（无需人工）；已 `enabled:true` → 静默继续；仅"文件不存在 + 未给无人值守意图"才走 Step 2A.1 的交互询问（Interactive 路径）。
4. **End 准入检查**：Test 完成后，步骤 1.5 已对 phase 5 跑产物门控（`hat-task-artifact-check {task-folder} 5`，即 P5 门控——确认 Test 阶段产物齐全、Layer 2 timing 痕迹存在）。门控 PASS 后，若 End 仍 PENDING → 硬停，告知用户调用 `/task-end`。门控 FAIL → 先按步骤 1.5 补齐/阻断，不进入 End。仅 unattended self_test 模式允许自动推进。
5. 否则：加载下一个阶段的 SKILL.md，继续执行

重复直到 Test 完成（End 由用户手动触发）。

<rule>
End phase MUST NOT auto-advance from Test in normal (non-unattended) mode. The user must explicitly invoke `/task-end` to enter the End phase. This is a deliberate decision point — automated test pass does not equal user acceptance.
Reason: user feedback during dogfooding found End phase sometimes auto-advancing without user confirmation.
</rule>

<rule>
Phase transitions MUST go through the corresponding SKILL.md. Skipping the SKILL.md means phases.md won't be updated, TODO sync won't happen, and the task will be archived with incomplete state.
Reason: M0 postmortem found Execute phase archived with all steps still [ ] and Status PENDING because task-execute/SKILL.md was never loaded.
</rule>

---

## phases.md Format Reference

各阶段 skill 创建/更新的标准格式。**步骤列表为动态生成**：P1 Step 1b.3 完成时首次按 task-config.json 动态生成（按 phase_merge 合并 Phase 节、按 plugins.*.enabled 裁剪步骤），P2 Step 2e 精调变更时可能重新生成。以下为默认模板（所有插件启用时的完整步骤）：

```markdown
# Task Progress

**Task**: YYYY-MM-DD-task-name
**Updated**: YYYY-MM-DD HH:MM

## Phase 1: Init
- [ ] 1a. 检查现有任务
- [ ] 1b. 解析参数 + 需求确认
- [ ] 1b.2 Prompt 质量分析
- [ ] 1b.3 档位粗选
- [ ] 1c. Git 规范 + 工作目录
- [ ] 1d. 分支决策
- [ ] 1e. Linear 上下文
- [ ] 1f. 创建任务文件夹 + prompt.md
**Status**: PENDING

## Phase 2: Design
- [ ] 探索项目上下文
- [ ] 澄清问题
- [ ] 提案
- [ ] 逐节展示设计
- [ ] 编写 design.md
- [ ] 自我 review + Review 策略确认
- [ ] 独立 review
- [ ] 确认设计
**Status**: PENDING

## Phase 3: Plan + Commit
- [ ] 3a. 生成 plan
- [ ] 3b. Plan 忠实度评估
- [ ] 3c. 提交任务文档
- [ ] 3d. Linear 同步
**Status**: PENDING

## Phase 4: Execute
- [ ] 4a. 执行任务
- [ ] 4b. 代码 review
**Status**: PENDING

## Phase 5: Test
- [ ] 5a. 完整验证
- [ ] 5b. Linear 状态更新
- [ ] 5c. 验收清单
**Status**: PENDING

## Phase 6: End
- [ ] 6a. 验证 + final.md
- [ ] 6b. 归档 + Linear Done
**Status**: PENDING
```

### Revise Section（触发时由 task-execute/task-test 追加）

触发方创建时为**单循环基线**（design/plan 步骤按需，由 task-revise 根因分析后插入）：

```markdown
## Revise R1
**Trigger**: 4b / 代码 review 发现系统性问题
**Return**: 4b
**Reason**: [问题描述]
**Started**: YYYY-MM-DD HH:MM
- [ ] R1-rootcause
- [ ] R1-execute
- [ ] R1-verify
**Status**: IN_PROGRESS
```

**按需步骤**：task-revise 在 `R1-rootcause` 根因分析后，若根因需要调整设计/计划，在 `R1-rootcause` 之后、`R1-execute` 之前插入 `- [ ] R1-design` 和/或 `- [ ] R1-plan`。不需要则不插入——**section 中存在的步骤都是要执行的，无 `[~]` 跳过标记**（与 task-revise 单循环一致）。

**DEFERRED 后**（升级转人工 / 转新任务，**不 reset 代码**）：
```markdown
## Revise R1 [DEFERRED]
**Trigger**: 4b
**Return**: 4b
**Reason**: [原始问题]
**Deferred Reason**: [为何无法在本 revise 内解决——被取代 / 转人工 / 转新任务]
**WIP Commit**: <SHA>
- [x] R1-rootcause
- [x] R1-execute
- [ ] R1-verify
**Status**: DEFERRED
```
已完成步骤保持 `[x]`、未完成保持 `[ ]`，无 `[~]`；半成品由 `**WIP Commit**` 的 commit 承接。

---

## Dependencies

- **Runtime loads**: `${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md`, `task-design/SKILL.md`, `task-plan/SKILL.md`, `task-execute/SKILL.md`, `task-test/SKILL.md`, `task-end/SKILL.md`（via Read at routing time）
- **Conditional load**: `${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`（仅当 unattended.json 存在时加载）, `${CLAUDE_PLUGIN_ROOT}/skills/task-revise/SKILL.md`（仅当 phases.md 包含 IN_PROGRESS 的 Revise section 时加载）
- **Scripts**: hat-task-detect, hat-task-artifact-check, hat-plugin-hook
- **State files**: `{task-folder}/phases.md`, `{task-folder}/task-config.json`
- **Unattended state**: `{task-folder}/unattended.json`
- **Subagent dispatch（条件依赖）**: `Agent`（`run_in_background=true` 派发一次性后台 subagent 执行 `subagent:{name}` 模式的 hook，见 Subagent Async Dispatch）——主线程恒可用，无实验特性依赖；无 enabled 插件声明 `subagents` 时不触发
