---
name: task-test
user-invocable: false
description: "Use when executing Phase 5 (Test) of a task. Runs full verification, updates Linear status, and shows acceptance checklist. Can be called standalone or via /task orchestrator. 触发词: \"测试阶段\", \"task test\", \"验收\", \"验证阶段\""
---

# Task Test — Phase 5: Test

任务测试阶段。运行完整验证，更新 Linear 状态，逐项引导用户验收。

**Announce at start:** "Using task-test for Phase 5: Test."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Check (light): !`r=$(grep -A1 '轻量' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`
- Check (full): !`r=$(grep -A1 '完整' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`

## Red Flags

| If you think... | Reality |
|---|---|
| "All checks passed, skip to Phase 6" | Never skip per-item confirmation. Each manual test item must be individually walked through with the user before proceeding to Phase 6. |
| "Verification passed, skip Linear update" | Linear visibility matters to the team. Don't skip. |
| "The fix is obvious, commit without user confirmation" | During test phase: analyze → fix → user tests → user confirms → THEN commit. |

---

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），**先**从 phases.md 重建概览行（确保拿到最小 ID 以固定在首行）并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。

---

## Resume Support

如果 phases.md 存在且 Phase 5 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 5 步骤对应：**
- `5a. 完整验证` → Step 5a
- `5b. Linear 状态更新` → Step 5b
- `5c. 验收清单` → Step 5c

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：
   - 执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
   - 读取全局配置（按第 0 节）：若 `task-defaults.json` 不存在，先从 `task-defaults.json.example` 复制创建，再 `cat` 读取，解析为 `task_config`（字段缺失时使用默认值）
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守模式的激活（unattended.json 创建）统一由 `/task` 编排器的 Step 2A.1 处理。各阶段 skill 仅负责读取已有状态。

---

### P5 起始时间戳（core timing，内联）

内联记录 phase_start（helper 自带顶层 `observability.enabled` 门控，关闭档 → no-op）：

```bash
hat-timing-stamp {task-folder} phase_start P5
```

### 5a. Full Verification

<rule>
声称验证通过前，必须先取得新鲜证据：① fresh 运行验证命令（Check (full)，不依赖记忆 / 上次结果）；② 读完整输出 + 退出码；③ 确认输出确实对应"验证通过"这一声明，方可标记通过。禁止基于"应该通过""上次通过了""改动很小"等做完成声明。
Reason: 证据优先于主张——未经新鲜验证的完成声明是虚假的，会让未测试的改动流向下游。依据见 `${CLAUDE_PLUGIN_ROOT}/skills/hatflow-verification-before-completion/SKILL.md`（Read 该文件获取完整 Iron Law 与失败案例库）。
</rule>

**快速路径**：如果 Check (light) 和 Check (full) 均为 `NOT_CONFIGURED`（验证命令为 none），且 design.md `## Acceptance Tests` 中没有手动测试项（全为自动化验证），则 5a-5b 标记为 `[x]` 并跳到 5c 验收清单的自动化结果展示。

运行 **Full verification**（Runtime Context 中的 Check (full) 命令）。

如果通过，将 commit hash 记录到 `{task-folder}/.last-verified`。

（NO_GIT 模式下跳过 `.last-verified` 写入）

完成后：更新 phases.md，将 `5a. 完整验证` 标记为 `[x]`。

### 5b. Linear 状态更新

> **由 `P5.post-acceptance` hook 中 linear plugin 执行。** 本步骤仅保留触发入口。

linear plugin 启用时，在验收完成后由 hook 将状态更新为 "In Review"。关闭时跳过。

完成后：更新 phases.md，将 `5b. Linear 状态更新` 标记为 `[x]`。

### Phase 5 Stop — Acceptance Checklist

**p5_auto_only 支持**：读取 `{task-folder}/task-config.json` 的 `p5_auto_only` 字段。
- `true` → 跳过手动测试项，仅执行自动化验收，acceptance-checklist.md 手动区域为空
- `false` / 不存在 → 正常流程（含手动测试项）

<rule>
Never skip user confirmation for manual test items (unless p5_auto_only). Automated tests run with results pre-filled; manual tests require user to fill in the checklist file.
Reason: premature closure skips user acceptance testing and risks shipping unverified changes.
</rule>

从 `{task-folder}/design.md` 的 `## Acceptance Tests` 提取验收项（唯一来源），**分类**为自动化和手动两组：

- **可自动验证**：grep 匹配、命令行检查、文件存在性、构建/测试通过等——机器可判定结果
- **需人工判断**：UI 行为、主观体验、跨系统集成效果、运行时交互流程等——需要人类确认

**Step 1: 批量执行自动化验收测试**

运行 5a 中的 light/full verification 结果 + design.md 中所有可自动验证的验收项。

**Step 2: 生成验收清单文件**

将自动化 + 手动测试结果写入 `{task-folder}/acceptance-checklist.md`。该文件是用户填写测试结果的**唯一界面**——对话可能因 context 推进而看不到测试项，文件不会丢失。

文件模板（极简 inline 格式——用户在箭头后填 PASS/FAIL + 可选备注）：

```markdown
# Acceptance Checklist

**Task**: {task-folder-name}
**Generated**: YYYY-MM-DD HH:MM

## Round 1

### 自动化测试（已预填，无需修改）

1. [MUST|SHOULD|MAY] 测试项描述
   → PASS
2. [MUST|SHOULD|MAY] 测试项描述
   → PASS
...

### 手动测试（请填写）

> 在 → 后填 PASS 或 FAIL（备注可选，写在结果后面）
> 例：→ PASS
> 例：→ FAIL 球还在动

1. [MUST|SHOULD|MAY] 测试项描述
   测试方法：具体操作步骤
   →
2. [MUST|SHOULD|MAY] 测试项描述
   测试方法：具体操作步骤
   →
...

### 追加修改（可选）

> 基于测试体验，如果有需要追加的修改或改进建议，请填写在下方。

-
```

**生成规则：**
- 首轮使用 `## Round 1` 显式编号（与后续 Round 结构统一）
- 自动化测试项：`→` 独占一行，预填 `PASS` 或 `FAIL`
- 手动测试项：`→` 独占一行留空，上方附 `测试方法：` 行
- Linear 同步状态附加到自动化测试区域
- 追加修改区域预留空行供用户填写

生成后告知用户：**"验收清单已生成到 `{task-folder}/acceptance-checklist.md`，请在模拟器上测试后填写手动测试项，填好后回复我。"**

**Step 2.5: 读取用户填写结果**

生成清单后，告知用户回复约定：
> "验收清单已生成。测试完成后请回复：
> - **`done`** — 我已在文件中填写了测试结果，请读取文件
> - **直接描述结果** — 如「全部通过」「XX没通过，表现为XXX，其他全通过」，我来帮你更新文件"

收到用户回复后，按以下方式处理：
- **用户回复 `done`**：读取 `acceptance-checklist.md` 文件解析结果
- **用户回复文本描述结果**（如"全部通过"、"XX没通过"等）：
  1. 读取当前 `acceptance-checklist.md`
  2. 根据用户描述代为填写所有 `→` 结果
  3. 保存文件后展示修改摘要，请用户确认

然后继续原有的解析逻辑：

等待用户回复后，读取 `{task-folder}/acceptance-checklist.md`：

1. 解析手动测试区域每行箭头后的结果（`→ PASS` / `→ FAIL ...`）+ 读取每项的 `[MUST|SHOULD|MAY]` 标签
2. **按标签门控**：`[MUST]` 或 `[SHOULD]` 的 FAIL → 读取备注文字，进入 5d（Handling Test Feedback）处理、**阻断 Phase 5 完成**（Interactive 下用户可显式接受现状跳出该项）；`[MAY]` 的 FAIL → **仅记录、不阻断**、不进修复循环
3. 解析"追加修改"区域 → 若有内容，逐条确认是否在当前 task 处理（简单修改直接做，复杂改动建议 defer）
4. 全部 MUST/SHOULD PASS（MAY 可 FAIL）且无追加修改 → 继续 Step 3
5. 有 MUST/SHOULD FAIL 项或追加修改需要代码变更 → 修复后进入 **Step 2.6**

**Step 2.6: 追加轮次**

修复完成后，**先重跑自动化验证**（light/full verification + 单元测试），确认新代码未引入回归。然后在同一文件末尾追加新的 Round section。前序轮次的结果保留作为历史记录。

追加格式：

```markdown
---

## Round N

### 自动化回归（已预填）

> 修改后重跑的自动化验证结果。

1. [—] `pnpm lint && pnpm typecheck`
   → PASS
2. [—] `pnpm test` (N/N passed)
   → PASS

### 手动测试（请填写）

> 包含上轮 FAIL 项的回归测试 + 追加修改的新测试项。

1. [MUST|SHOULD|MAY] 原测试项描述（上轮 FAIL / 回归）
   测试方法：具体操作步骤
   →
2. [SHOULD] 追加修改描述
   测试方法：具体操作步骤
   →

### 追加修改（可选）

-
```

**追加规则：**
- Round 编号从 2 开始递增（首轮隐含为 Round 1）
- 回归测试：上轮 FAIL 的项（含修复后的重测）
- 追加修改测试：上轮追加修改区域中需要代码变更的条目，转为测试项
- 前序轮次不修改——保留完整的测试历史
- 用户填写后再次执行 Step 2.5 读取结果，循环直到全部 PASS 且无追加修改

**验收项回写（修代码前执行）：**

追加修改是测试阶段发现的新需求，必须先回写到 `design.md` 的 `## Acceptance Tests` 再改代码——保持 design.md 为验收标准的单一事实源。

1. 为每条需要代码变更的追加修改在 design.md `## Acceptance Tests` 末尾追加新验收项
2. 形态 `[SHOULD] 可执行/可观察的验收项`（测试阶段发现的追加需求默认 `[SHOULD]`，用户可覆盖为 `[MUST]` / `[MAY]`）；按需附变体 / 反模式纯文字注记
3. 新 round 的追加修改测试项引用这些新验收项（而非 `[NEW]`）

**基础设施问题分流**（适用于 FAIL 项）：
- 环境/配置问题 → 标记 NOT_APPLICABLE，不触发修复
- Baseline 已有问题 → 标记 NOT_APPLICABLE
- 本次改动引入 → 标记 FAIL，触发修复流程

若所有验收项均为自动化（无手动测试项），跳过文件中的手动区域，直接进入 Step 3（仍生成文件，但手动区域为空）。

**Step 3: P5.post-acceptance Hook（Linear 同步）**

验收完成后运行：

```bash
hat-plugin-hook {task-folder} P5.post-acceptance
```

> **Subagent**：linear 在 P5.post-acceptance 为 `subagent:linear-sync` hook。`hat-plugin-hook` 输出 DISPATCH 指令，编排器据此派一次性后台 subagent 异步执行（见 task/SKILL.md Subagent Async Dispatch）。

hook 输出可能包含多段指令，**必须逐段全部执行**（linear: 状态更新为 In Review）。

更新 phases.md，将 `5c. 验收清单` 标记为 `[x]`，Phase 5 `**Status**: DONE`。

验收完成后是硬停，不自动推进 Phase 6（权威规则见「Test 完成 → 过渡」）。

**[Unattended]** 若无人值守模式激活：
- `task_type == "self_test"` → 跳过手动测试区域，仅评估**可机判**的自动化验收项：
  - 可机判 `[MUST]` / `[SHOULD]` FAIL → 进修复循环（重试一次 Opus）；仍无解 → Telegram 通知人工 + **暂停**（任务保留、等 `/task` 恢复，**非 auto-cancel**——区别于"验证命令失败 → auto-cancel"，见 UNATTENDED_PROTOCOL 第 8 节）
  - 不可机判的 `[SHOULD]` / `[MAY]` 项（无人填 PASS/FAIL）→ 记录为 deferred、不阻断
  - 全部可机判 MUST/SHOULD PASS（含 deferred）→ 发送 Telegram 通知 `[task-name] Phase 5 完成，自动推进到 Phase 6...` → 更新 phases.md Phase 5 Status = DONE → 返回编排器
- `task_type == "user_test"` → 生成完整清单文件 → 发送 Telegram 通知 `[task-name] 验收清单已生成到 acceptance-checklist.md，请填写后回复` → 停止，等待用户

---

### 5d. Handling Test Feedback

如果用户在测试后报告 bug：

1. **先分析，后行动** — 复现 → 找到根因 → 向用户解释 → 修改前获得确认
2. **Do NOT commit after modifying** — 告知用户变更内容，让他们再次测试
3. **多轮反馈** — 每轮：分析 → 修改 → 用户确认 → 然后提交

Do NOT commit before user confirmation. Unverified fixes may introduce new problems.

#### P5.test-feedback Hook（架构级问题时触发）

测试发现架构级问题时，运行：

```bash
hat-plugin-hook {task-folder} P5.test-feedback
```

按输出指令执行（review: Revise 触发检测）。review 关闭时跳过，走下方手动判别。

#### Architectural Issue Triage（架构级问题判别）

<rule>
5d 测试发现的问题分两类：**局部 bug**（在 design 前提之内，原地修复）和 **架构级问题**（与 design 前提相悖，原地修复会让 task 边界失控）。后者必须 STOP 当前修补，AskUserQuestion 决定走向。

判别一个问题是否属于架构级 — 满足任一即是：
- 根因落在 design.md 显式或隐式假设之外（例如 design 假设"X 由 A 模块负责"，实际 X 落在 B）
- 修复方案需要扩展 design.md 才能合理表达
- 修复跨越当前 task 的模块边界（涉及未在 plan.md task 列表中的模块）
- 修复引入新的长期运行实体（进程、守护、bot、cron、外部依赖）
- 修复改变跨进程 / 跨 session / 跨服务的契约（路由、状态语义、消息格式）

确认是架构级后，AskUserQuestion 三个选项：
1. **触发 Revise Cycle** — 结构化的 mini design→plan→execute 子循环，有完整状态追踪（phases.md 中 Revise section）。选择后进一步选择深度：Full (design+plan+execute) / Partial (plan+execute) / Lite (execute only)
2. **Defer to a new task** — 本 task 仅做最小兜底（或不做），开新 task 处理
3. **Patch in place** — 仅限真正的局部修补（无状态追踪，直接改→测→commit），涉及多文件/多步骤时应选 Revise Lite

**Revise 触发执行**（当用户选择选项 1 时）：
1. 在 phases.md 中相关验收项后追加 `[→ REVISE R1]`
2. 在 phases.md 末尾追加 `## Revise R1` section，包含字段：Trigger（5d）、Return（5c）、Depth（用户选择）、Reason（问题描述）、Started（当前时间）、Status（IN_PROGRESS）、按深度生成步骤列表（Partial 深度 R1-design 标记 `[~]`；Lite 深度 R1-design + R1-plan 标记 `[~]`）
3. 声明："Revise R1 已触发，返回编排器。"
4. **不标记 5c 为 `[x]`**——5c 在 revise 完成后的回归模式中才标记

**回归模式检测**（在 5c 验收清单中）：
- 检查 phases.md 中是否有 DONE 状态的 Revise section 且 Return 步骤为 5c
- 如有：进入回归模式——仅重跑触发 revise 的相关测试项，而非完整验收
- 回归通过后：**task-test（非编排器、非 task-revise）负责**标记 Revise RN Return 步骤完成 + 5c `[x]`

**用户主动触发**：如果用户在 Phase 5 任意时刻主动提出大 bug 或新需求（超出逐 bug 修复范围），提供 Revise Cycle 作为选项：AskUserQuestion——**触发 Revise Cycle** (Full/Partial/Lite) / **Defer to new task** / **继续逐 bug 修复**

Reason: 架构级问题若在 5d 直接原地修，会出现：commit 序列与 plan.md 脱节；final.md 难以解释偏差；后续相关 task 的 design 失去前置上下文。Revise Cycle 通过结构化子流程让偏差被显式记录而非隐式吞掉。
</rule>

---

## phases.md Sync

每个步骤完成后更新 phases.md。每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

<rule>
Every step completion MUST update phases.md: mark step [x], update Updated time, update Status when all steps done.
Reason: phases.md is the cross-session state record. Missing updates mean the next session cannot correctly resume.
</rule>

**Phase 5 完成时**（所有测试完成后）：将 Phase 5 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

---

### P5 结束时间戳（core timing，内联）

Phase 5 完成时内联记录 phase_end：

```bash
hat-timing-stamp {task-folder} phase_end P5
```

<rule>
P5 timing 经内联 `hat-timing-stamp`（phase_start/phase_end），helper 自带 `observability.enabled` 门控（关闭档 → no-op，不写、不报错）。
Reason: timing 内联后是确定动作；缺 phase_start 触发 artifact-check 硬 FAIL，缺 phase_end 仅非阻断警告，故 phase_start 内联点须前置。
</rule>

---

## Test 完成 → 过渡

Test 完成后**不自动推进**。用用户配置的语言简要宣告测试结果（自动化验证状态、Linear 同步状态、用户确认结果），然后声明：**"所有测试已完成，请调用 `/task-end` 关闭任务。"**

<rule>
Test phase is a hard stop. Never auto-advance to End phase, even when all acceptance tests are automated and passing. The user must explicitly invoke `/task-end`.
Reason: the user needs a deliberate decision point before closing a task — automated test pass does not equal user acceptance.
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 5d | 架构级问题确认后 | 触发 Revise Cycle / Defer / Patch in place |
| 5c 回归 | 回归 review 不通过 | 触发 R(N+1) / 手动修复 / 终止 |
| Phase 5 Stop | 所有测试完成后 | 硬停，告知用户调用 `/task-end`（不自动推进） |

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/phases.md`, `{task-folder}/.last-verified`, `{task-folder}/acceptance-checklist.md`
- **Hooks**: `P5.post-acceptance`（linear）, `P5.test-feedback`（review: Revise 检测）
- **Subagent（异步派发）**: `P5.post-acceptance` 的 linear 为 `subagent:linear-sync` hook —— `hat-plugin-hook` 输出 DISPATCH 指令，编排器据此派一次性后台 subagent 异步执行 Linear 状态更新（In Review）。交接契约见 task/SKILL.md「Subagent Async Dispatch」。
- **Core timing**（内联，非 hook）: phase_start P5（阶段开始）/ phase_end P5（阶段完成）经 `hat-timing-stamp`，受顶层 `observability.enabled` 门控
- **Scripts**: hat-plugin-hook, hat-timing-stamp
