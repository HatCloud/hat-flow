---
name: task-revise
user-invocable: false
description: "Use when executing a Revise Cycle within Phase 4/5. Runs an adaptive single fix loop (root-cause → optional design/plan → execute → verify) to address systemic issues found during code review or testing. Triggered by task-execute (4b) or task-test (5d), routed by the orchestrator. 触发词: \"revise cycle\", \"修订循环\", \"修复系统性问题\""
---

# Task Revise — Revise Cycle

Revise Cycle 处理器。在 Phase 4/5 内部执行一个**自适应单循环**：根因分析 →（按需）调整 design/plan → 执行修复 → 验证收尾，处理 code review 或 testing 发现的系统性问题。不再有 Full/Partial/Lite 深度档位——是否动 design/plan 由根因分析决定。

**Announce at start:** "Using task-revise for Revise Cycle."

**LANGUAGE RULE:** Write user-facing output in the user's configured language; keep technical terms and code identifiers in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

## Red Flags

| If you think... | Reality |
|---|---|
| "The fix is obvious, skip root-cause analysis" | No fix without a root cause (hatflow-systematic-debugging Iron Law). Jumping to a patch produces band-aids. |
| "I'll nest another revise inside this one" | Revise cycles do NOT nest. If new issues arise, complete current revise first. |
| "This is a root problem — let me git reset the code back" | Revise never resets code. Root problems escalate to DEFERRED: commit the WIP, record the SHA, hand off to a human or a new task. |
| "RN-verify means I should run the full regression myself" | RN-verify only marks Status = DONE. Actual regression runs in the return phase. |

---

## TODO Sync

双层 TODO 同步契约见 `task/references/todo-sync.md`。要点：每步 `TaskUpdate`（开始 `in_progress`、完成 `completed`）并同步 phases.md；session 恢复时先 `TaskList`，无 `overview` 行则从 phases.md 重建（取最小 ID）再建 step 级 task。（恢复时同步 phases.md 中 Revise section 对应步骤）

---

## Resume Support

单循环 resume：如果 phases.md 中当前 Revise section 已有已完成的步骤（`[x]`），从第一个未完成（`[ ]`）的步骤继续。section 里**存在的步骤都是需要执行的**——按需跳过的 design/plan 步骤根本不会出现在 section 中（不使用 `[~]` 标记）。

---

## Unattended State

1. **读取状态**：`cat "{task-folder}/unattended.json" 2>/dev/null`（task-folder 从 Initialization 步骤 1 中解析 phases.md 所在路径获取，而非 open[0].path）
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议。后续停止点按协议自动决策。
3. **若文件不存在或 enabled != true**：正常交互流程

> **本文件所有「Telegram 通知」均经 `UNATTENDED_PROTOCOL.md` §4 发送**：Telegram 为 opt-in（companion 插件 `telegram@claude-plugins-official`）；未配置 chat_id / 插件未装 / MCP 不可用时静默降级（打印告警、不阻断 revise 流程），自动推进不依赖通知送达。

**[Unattended] 单循环自动推进**：根因分析后若需 design/plan 调整，按推荐方案自动选择并 Telegram 通知；遇根本性问题（见 Root-Problem Handling）→ 自动转新任务（commit WIP、标 DEFERRED、记 SHA），不靠人工，Telegram 通知后停止当前 revise。

---

## Process

<rule>
Revise section 无 PENDING 状态。创建即 IN_PROGRESS。task-revise 不创建 Revise section（由触发方 task-execute/task-test 创建），仅读取和更新已有 section。
Reason: PENDING 状态会导致编排器路由歧义——IN_PROGRESS 是唯一的"需要执行"信号。
</rule>

单循环步骤序列（design/plan 两步按需产生）：

```
Initialization → RN-rootcause → [按需] RN-design → [按需] RN-plan → RN-execute → RN-verify
```

### Initialization

1. 读取 phases.md，找到 `Status: IN_PROGRESS` 的 `## Revise RN` section（N 为编号，从标题 `## Revise R1` / `## Revise R2` 中提取数字。文档中 `RN` 泛指"当前 revise"，实际执行时替换为具体编号如 R1、R2）
   > Revise section 的**路由判定**（哪个 section 该执行——多 IN_PROGRESS 取最大编号、DONE 回归、DEFERRED 终结）权威表在 `task/SKILL.md` Revise 路由段；本 skill 只读已选中的 IN_PROGRESS section、不重复该决策。
2. 解析字段：Trigger, Return, Reason, Started
3. 读取 `{task-folder}/design.md` 和 `{task-folder}/plan.md` 了解原始设计和计划上下文

### RN-rootcause（根因分析）

接入 hatflow-systematic-debugging，先定位根因再决定改什么。

1. `Read ${CLAUDE_PLUGIN_ROOT}/skills/hatflow-systematic-debugging/SKILL.md`（Iron Law：无根因不修——先复现/定位，再判断）
2. 基于 code review findings 或 test failures 做根因分析：问题出在哪一层？是实现细节、计划遗漏，还是设计假设被证伪？
3. 据根因判定本次 revise 需要触及哪些步骤，**按需把对应步骤插入 section**（在 RN-rootcause 之后、RN-execute 之前）：
   - 根因是**设计假设错误**（仍可在本 revise 内修） → 插入 `- [ ] RN-design` 与 `- [ ] RN-plan`
   - 根因是**计划遗漏/任务拆分不当**（设计仍成立） → 仅插入 `- [ ] RN-plan`
   - 根因是**实现细节** → 不插入，直接进入 RN-execute
   - 根因是**根本性问题**（框架不可用 / 核心假设被完全证伪 / 修复远超当前 revise scope） → 不插入任何步骤，**直接触发 Root-Problem Handling**（见 RN-execute 章节）：跳过 design/plan/execute，commit 已有半成品后标 DEFERRED
4. 标记 `RN-rootcause` 为 `[x]`，更新 phases.md

**[Unattended]** 自动按上述判据决定插入哪些步骤，Telegram 通知"根因：[结论]，本次将触及：[步骤]"。

### RN-design（仅当根因需要设计调整）

精简版设计讨论，聚焦于 Reason 与根因分析定位的问题区域。

1. 与用户讨论修订方案（AskUserQuestion 提出 2-3 个选项）
2. 将设计修订追加到 `{task-folder}/design.md`：

```markdown
## Revise RN: [标题]
**Trigger**: [Phase 4 code review / Phase 5 testing / 用户主动]
**Reason**: [为什么需要 revise]

### 根因分析
[hatflow-systematic-debugging 定位的根本原因]

### 设计修订
[针对问题区域的设计调整]

### 影响范围
[哪些现有模块/接口受影响]
```

3. **确认循环**：
   - 展示修订方案（根因分析 + 设计修订 + 影响范围）
   - 纯文本询问："以上修订方案是否准确？有需要调整的地方吗？"
   - 用户说"继续" → 写入 design.md，标记 `RN-design` 为 `[x]`
   - 用户给建议 → 修改 → 重新展示 → 回到确认

**[Unattended]** 按推荐选项自动选择，发送 Telegram 通知"自动选择修订方案：[方案名]"。

### RN-plan（仅当根因需要计划调整）

生成针对性的任务列表。

1. 基于根因分析（及 RN-design 修订，若有）生成 revise 任务列表
2. 追加到 `{task-folder}/plan.md`：

```markdown
## Revise RN: [标题]

### Tasks
- [ ] RN-T1: [任务描述]
- [ ] RN-T2: [任务描述]
```

3. **确认循环**：
   - 展示任务列表 + verification 标准
   - 纯文本询问："以上修复任务是否完整？有需要调整的地方吗？"
   - 用户说"继续" → 标记 `RN-plan` 为 `[x]`
   - 用户给建议 → 修改 → 重新展示 → 回到确认

<rule>
When a revise touches design or plan, the RN-design / RN-plan step MUST include a confirmation loop before marking complete. Do NOT advance to RN-execute without explicit user approval of the revision plan.
Reason: Revise without user review leads to band-aid fixes that miss the root cause, as observed in R1 of task-workflow-fixes.
</rule>

**[Unattended]** 跳过等待，按生成的任务列表直接推进。

### RN-execute

执行 revise 任务。

1. **Pre-execute Checkpoint**（NO_GIT 模式下跳过）：如有未提交的代码变更，先 commit（保持工作树干净，便于后续按 commit 边界回归）
2. 读取 `{task-folder}/task-config.json` 获取执行模式和引擎选择
3. 逐个执行 revise tasks（复用主流程的引擎选择逻辑）
4. 每个 task 完成后 commit（git 启用时由 git plugin hook 提供 commit 规范）
5. 更新 phases.md：标记 `RN-execute` 为 `[x]`

**Root-Problem Handling**：如果**根因分析（RN-rootcause）判定**、或**执行中新暴露**了**根本性问题**（框架不可用、核心假设完全错误、修复需要远超当前 revise scope 的改动），无论问题在哪个步骤被发现，都走以下处理（rootcause 阶段触发时跳过 design/plan/execute）：

<rule>
On a root problem during revise execute, stop and AskUserQuestion. Options:
1. **升级转人工** — current revise marked DEFERRED, hand off to a human.
2. **转为新任务** — current revise marked DEFERRED, open a fresh task to handle the root problem.
Never reset code. Before marking DEFERRED, commit the work-in-progress as `chore: WIP [DEFERRED Rn] <原因>` and record that commit SHA in the Revise section's **WIP Commit** field.
Reason: resetting code throws away partial progress and pollutes the working tree on recovery; DEFERRED preserves the WIP behind a labelled commit so a human or the new task can pick up exactly where this left off.
</rule>

**[Unattended]** 遇根本性问题 → 自动选「转为新任务」：commit WIP、标 DEFERRED、记 SHA、开新 task、Telegram 通知后停止当前 revise（不靠人工应答）。

### RN-verify

标记 Revise Cycle 完成，返回编排器。

1. 更新 phases.md：标记 `RN-verify` 为 `[x]`
2. 将 Revise RN 的 `**Status**: IN_PROGRESS` 改为 `**Status**: DONE`
3. 声明：**"Revise RN 完成。"**

**注意**：RN-verify 的含义是"revise 执行完毕，等待回归验证"，而非"revise 自身验证通过"。实际验证由回归阶段的原 phase skill 执行（task-execute 重跑 4b 或 task-test 重跑相关测试项）。

---

## Chain Detection

<rule>
如果当前 Revise 编号为 R3 或更高（即已经有 2 个以上 Revise cycle），必须 AskUserQuestion 警告用户，选项：
1. **继续 R3** — 已理解风险，继续
2. **拆分为新任务** — 当前任务 scope 可能过大，开新 task 处理
3. **重新审视整体设计** — 回到 Phase 2 重做设计
Reason: 多次 revise 暗示原始设计存在根本缺陷，继续 patch 不如重新设计。
</rule>

**[Unattended]** R3+ 自动选「拆分为新任务」，Telegram 通知后停止。

---

## Error Handling

| 异常场景 | 处理方式 |
|----------|----------|
| Revise execute 中卡壳/根本性问题 | 接 hatflow-systematic-debugging 定位根因；确为根本性问题 → Root-Problem Handling（DEFERRED + WIP commit + 转人工/新任务） |
| Revise design 讨论无法达成共识 | AskUserQuestion：简化 revise 范围 / 转新任务（DEFERRED） / 取消 revise + patch in place |
| 无人值守模式下触发 revise | 根因分析自动判定触及步骤；执行卡壳 → 转新任务（DEFERRED）+ Telegram |

**[Unattended] DEFERRED→新任务流程**：commit WIP（`chore: WIP [DEFERRED Rn] <原因>`）、Revise section 标 DEFERRED 并记 WIP Commit SHA、创建后续任务的 `next-task-prompt.md`、发送 Telegram 通知后停止。

---

## phases.md Sync

每个步骤完成后更新 phases.md 中对应 Revise section 的步骤标记。

**Revise 完成时**：将 `**Status**: IN_PROGRESS` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

**Revise 升级/取代时（DEFERRED）**：将 `**Status**: IN_PROGRESS` 改为 `**Status**: DEFERRED`，保留原 `**Reason**`（原始问题），新增 `**Deferred Reason**`（为何无法在本 revise 内解决——被取代 / 转人工 / 转新任务）与 `**WIP Commit**: <SHA>`（承接半成品的 commit）。已完成步骤保持 `[x]`、未完成保持 `[ ]`，**不 reset 代码、不用 `[~]`**。字段命名与编排器 phases.md Format Reference 的 DEFERRED 模板一致。

---

## Revise → Return Transition

Revise RN 完成（Status = DONE），phases.md 已更新。

用用户配置的语言简要宣告 revise 结果（执行的步骤、修改的文件），然后声明：**"Revise RN 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

编排器检测到 Revise DONE 且 Return 步骤仍为 `[ ]`，将路由回原 phase skill 重跑触发步骤。`DEFERRED` 为终态——编排器识别为"已终结、不再路由执行"，不依赖 Return 步骤是否 `[x]`。

<rule>
Revise 完成后必须返回编排器。不得在 transition 中提示用户调用任何 skill 或自行判断下一步。
Reason: Revise 不知道 Return 步骤的完整上下文（回归模式、phase_merge 等），自行路由会跳过编排器的检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| RN-design | 方案选择 | 选择修订方案 |
| RN-plan | 任务列表确认 | revise 任务列表是否完整 |
| RN-execute | 发现根本性问题 | 升级转人工 / 转新任务（均标 DEFERRED，不 reset 代码） |
| Chain R3+ | 第 3 次以上 revise | 继续 / 拆分 / 重新设计 |

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/plan.md`, `{task-folder}/phases.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/design.md`（按需追加 Revise section）, `{task-folder}/plan.md`（按需追加 Revise section）, `{task-folder}/phases.md`
- **References**: `hatflow-systematic-debugging`（根因分析，RN-rootcause 步骤）
- **Invokes**: subagent for execute（按 task-config.json execution 配置）
- **Git**: WIP commit on DEFERRED（无 git tag / 无 git reset）
