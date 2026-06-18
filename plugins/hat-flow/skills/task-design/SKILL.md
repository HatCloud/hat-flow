---
name: task-design
user-invocable: false
description: "Use when executing Phase 2 (Design) of a task. Explores code, proposes solutions, writes design.md. Can be called standalone or via /task orchestrator. 触发词: \"开始设计\", \"task design\", \"设计阶段\", \"进入设计\""
---

# Task Design — Phase 2: Design

任务设计阶段的**编排薄层**：announce、加载 runtime context、嵌入 DESIGN_PROTOCOL、调用 hooks、TODO sync、resume、配置精调、过渡。完整设计流程（步骤、模板、复杂度矩阵、原则）的单一来源是下方 `!cat` 嵌入的 DESIGN_PROTOCOL.md——本文件不重述其内容。

**Announce at start:** "Using task-design for Phase 2: Design."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

## DESIGN_PROTOCOL (pre-loaded):

设计流程的步骤、模板、复杂度矩阵、原则全部定义在此协议中。按 Step 1-8 顺序执行。

<DESIGN_PROTOCOL>
!`cat ${CLAUDE_PLUGIN_ROOT}/skills/task/DESIGN_PROTOCOL.md`
</DESIGN_PROTOCOL>

## Red Flags

| If you think... | Reality |
|---|---|
| "I know enough to design without exploring" | Explore first. Unknown unknowns are the most dangerous. |
| "Skip design review, the design looks fine" | Self-assessment bias is real. Medium/High complexity requires reviewer subagent. |
| "The user implied approval, move on" | Implied approval is not approval. Require explicit affirmative ("好", "可以", "LGTM"). |
| "I'll design features not in the requirements" | YAGNI. Design only what was asked. |
| "This task is too simple to design" | 简单任务恰是未审假设致返工的高发区。设计可短，但必须展示并获批准（见 DESIGN_PROTOCOL Anti-Pattern）。 |

---

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），**先**从 phases.md 重建概览行（确保拿到最小 ID 以固定在首行）并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。每个 Step 完成后将对应 phases.md 行标记为 `[x]`。

---

## Resume Support

如果 phases.md 存在且 Phase 2 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 2 步骤对应（DESIGN_PROTOCOL 的 Step）：**
- `探索项目上下文` → Step 1
- `澄清问题` → Step 2
- `提案` → Step 3
- `逐节展示设计` → Step 4
- `编写 design.md` → Step 5（Step 2e 配置精调折叠在此步之后执行，phases.md 无独立步——从本步恢复即覆盖 2e）
- `自我 review + Review 策略确认` → Step 6 + 6.5
- `独立 review` → Step 7
- `确认设计` → Step 8

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取（或由编排器传入）。

---

## Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议，后续所有停止点按协议自动决策
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守模式的激活（unattended.json 创建）：当前阶段在配置精调 / 过渡处询问 activate_after（见下方 Activation Timing）；其余创建路径由 `/task` 编排器处理。各阶段 skill 读取已有状态。

### Step 2/3/4 的 Unattended 分支

DESIGN_PROTOCOL 的交互停止点在无人值守模式下的处理：

- **Step 2（澄清问题 + 确认循环）**：按 UNATTENDED_PROTOCOL.md 第 7 节（Self-Discussion Protocol）执行——派发 Requirements Analyst subagent（Agent tool，general-purpose，非后台），将问题和答案写入 `{task-folder}/unattended-decisions.md`，通过 Telegram 通知关键假设后继续；跳过纯文本确认循环的等待。

<rule>
Unattended mode MUST get clarification answers from an external source (subagent). Main agent inline answers are PROHIBITED, even if the answer seems obvious.
Reason: Self-Discussion Protocol requires an independent perspective.
</rule>

- **Step 3（提案）**：按推荐选项自动选择（标注 "Recommended" 的，或综合判断的最优组合），发送 Telegram 通知"自动选择方案：[方案名]"，不等待用户响应。
- **Step 4（逐节展示）**：跳过每节的用户确认，自我检查通过即继续下一节。
- **Step 8（确认设计）**：reviewer 通过（Critical = 0 且 Important = 0）后自动批准。

---

## P2 起始时间戳（core timing，内联）

内联记录 phase_start（须在本 phase 任何 `hat-plugin-hook` 调用之前；helper 自带顶层 `observability.enabled` 门控，关闭档 → no-op）：

```bash
hat-timing-stamp {task-folder} phase_start P2
```

---

## Step 2e: 配置精调

design.md 初稿（DESIGN_PROTOCOL Step 5）完成后执行。task-config.json 已在 P1 Step 1b.3 写入并据此选定 preset；此处仅在**复杂度与已选 preset 明显偏离时**才弹面板修正，一致则静默沿用。

**Step 2e.1: 复杂度评估**

基于 design.md 内容，用 DESIGN_PROTOCOL 的 Complexity Assessment 信号矩阵评估复杂度（Low/Medium/High）。

**Step 2e.2: 偏离判断（轻量化条件触发）**

**[Quiet] headless 短路（最先判断）**：读取 `{task-folder}/task-config.json` 的 `_source` 字段。若 `_source == "headless"`（由无头入口在 1f 物化）→ **永不弹面板**，静默沿用现有 task-config.json，复杂度评估仍照常跑（结果写入下面 2e.3 的 design.md 策略段），直接进入 2e.3。无头流程不在此引入交互。

将评估出的复杂度与 P1 Step 1b.3 已选 preset 对应的复杂度对比：

- **一致 / 仅小幅偏离** → 静默沿用现有 task-config.json，不弹面板，直接进入 2e.3 写 design.md 策略段。
- **明显偏离**（如 preset 为 lite 但 design.md 评估为 High，或反之）→ 弹 AskUserQuestion 配置面板修正：

  | 配置项 | 当前值 | 推荐值 | 说明 |
  |--------|--------|--------|------|
  | 执行模式 | auto/inline/parallel-agents | ... | 基于复杂度推荐；auto 按 plan Depends 拓扑分批派发 |
  | 引擎 | auto/sonnet/opus | ... | auto 时按难度 + TDD 加权 + 架构 override 自动分流模型 |
  | Design review 轮次 | auto/0/1/2 | ... | 基于复杂度 |
  | Reviewer 模型 | claude | ... | 按矩阵 |
  | Plan review 模型 | sonnet/opus | ... | 按维度×难度 |
  | Code review 级别 | skip/light/medium/full | ... | 基于复杂度 |
  | Per-task review 粒度 | each/checkpoint | ... | each 缺省（质量优先）；prose-only 多-task 重构可选 checkpoint 降派发数，仅 medium/full 下有意义 |

  用户确认或调整后执行 2e.3。

**Step 2e.3: 变更执行**（仅当面板触发且有变更并经用户确认时执行前 2 步）

1. 就地更新 `{task-folder}/task-config.json`
2. 重生成 `{task-folder}/phases.md` 步骤列表（使用与 P1 Step 1b.3 相同的动态生成逻辑：按 `phase_merge` 合并 Phase 节、按 `plugins.*.enabled` 裁剪步骤）
3. 无论是否弹面板，将 `## Execution Strategy` + `## Review Strategy` 写入 design.md
4. **验证命令前置**（约定 9 Interaction Front-Loading）：把 Acceptance Tests 阶段确认的 light / full 验证命令写入 `{task-folder}/task-config.json` 的 `check` 字段（如 `"check": {"light": "...", "full": "..."}`），供 Execute 直接读、无需再问。无可自动验证项则写空/省略，Execute 视为「无 light 验证」静默跳过。

**配置校验**（变更时执行）：
- `tdd.mode != "none"` 自动设置 `tdd.enabled = true`

**[Unattended]** 合理时自动沿用，明显偏离时按推荐值自动修正，不询问。

**Step 2e.4: Codex capability 持久化**（reviewer/engine 含 codex/auto 时，**不依赖面板是否触发**）

当 `task-config.json` 的 `plugins.review.reviewer` ∈ {`codex`, `auto`} 或 `execution.engine` ∈ {`codex`, `auto`} 时，运行 `codex-check`（额度门已内含），把结果写入 `task-config.json` 的 `capabilities.codex`（**由本 phase skill 写入，非 `hat-task-config-resolve`**）：

```json
"capabilities": { "codex": { "checked_at": "<ISO>", "status": "ready|fallback", "reason": "<codex-check stdout/stderr 文本>", "quota_state": "ok|stale|unknown|low", "cwd_control": "unknown" } }
```

- `cwd_control` 此处先留 `"unknown"`，由 P4 task-execute 首个 codex execute 前的 cwd spike 回填 `verified|unsupported`。
- **失效规则**：`checked_at` 超 30min 或进入新 phase 即视为过期，由各派发点（P2/P3/P4 dispatch）二次 `codex-check` 刷新覆盖（design Component C）。
- reviewer/engine 均不含 codex/auto 时跳过本步（不写 capabilities）。

### Activation Timing（unattended activate_after，与编排器共享契约 SC3）

在 Step 2e（及下方过渡处）询问无人值守激活时机。

**守卫（先判，与"已激活时跳过"并列）**：读取 `{task-folder}/unattended.json`。若文件存在且 `declined == true`（用户此前已拒绝无人值守）→ 跳过激活时机询问，静默继续、不进激活分支（declined 短路优先于 activate_after，见 `UNATTENDED_PROTOCOL.md` §5）。若已 `enabled:true`（已激活，**含 quiet 入口在 1f 物化的 headless 状态**）→ 同样跳过询问。

否则用 AskUserQuestion 提供四个选项：

| 选项 | 含义 | 动作 |
|------|------|------|
| 现在启用 | 立即进入无人值守 | 写 `unattended.json`（`enabled: true`, `activate_after: "now"`） |
| Design 阶段结束后启用 | 本阶段仍交互，过渡后激活 | 写 `unattended.json`（`enabled: false`, `activate_after: "design"`） |
| Plan 阶段结束后启用 | Design + Plan 交互，Plan 后激活 | 写 `unattended.json`（`enabled: false`, `activate_after: "plan"`） |
| 否 | 全程交互 | 写拒绝哨兵 `unattended.json`（`{"enabled": false, "declined": true}`），使后续过渡点不再重复询问 |

`unattended.json` 字段 `activate_after: "now" | "design" | "plan"`（缺省视为 `now`）。激活动作（把 `enabled` 翻为 true）由编排器在对应阶段过渡时按 `activate_after` 触发。

**[Unattended]** 已激活时跳过此询问。

---

## Step 6/7/8 Hooks 与 Review 循环

DESIGN_PROTOCOL 的 Step 6 / 6.5 通过 hook 委托 review plugin；Step 7 独立 review 与 Step 8 确认循环的编排细节如下。

### Step 6 — P2.post-design-draft Hook

```bash
hat-plugin-hook {task-folder} P2.post-design-draft
```

hook 输出可能包含多段指令，**必须逐段全部执行**（review plugin: 自我审查 + 独立 review）。**review plugin 关闭时**：执行最小化自我检查（placeholder scan + internal consistency），跳过独立 review。

### Step 7 — Independent Review 循环

<rule>
design_rounds > 0 时必须派发至少一个 reviewer subagent。不能仅标记步骤 [x] 而不执行实际 review。
Reason: dogfooding 发现 design_rounds > 0 时 review 被静默跳过，导致设计缺陷流入执行阶段。
</rule>

**review plugin 关闭时**：跳过本步骤，直接标记 `独立 review` 为 `[x]`。

**Reviewer 解析（codex-aware，派发前先判）**：按 `review.md ## P2.post-design-draft` 的「Reviewer-aware 派发（codex 分支）」解析 reviewer（读 `task-config.json` `plugins.review.reviewer` + `capabilities.codex`；过期/跨 phase → 派发点二次 `codex-check` 刷新）。
- **解析为 `claude`/`sonnet`/`opus`** → 走下面 native design-reviewer 收敛循环（并行 R1/R2 矩阵）。
- **解析为 `codex`**（`auto` 且 codex-first 成立亦归此）→ 改走 review.md codex 分支：经 `/codex:rescue`（read-only）**串行** R1/R2（codex 不并发），输出 `## Critical/Important/Minor` + 末行计数，`codex-findings-count` 判 **C=0 & I=0** 收敛，round≥2 `SendMessage(to: agentId)` 续接。下面第 2–5 步的批判评估/修复/收敛检查逻辑**不变**，仅派发载体（codex vs native）与并发性（串行 vs 并行）不同。中途 `FALLBACK:`/quota → 降级 native design-reviewer（见 review.md，写 `fallback-log.jsonl`）。

**收敛模式核心循环：**

1. **并行派发** R1（结构审查）+ R2（对抗审查），均用 `subagent_type: design-reviewer`（保留 model override，按下方矩阵在派发时指定）：

   | 轮次类型 | Low | Medium | High |
   |----------|-----|--------|------|
   | 常规轮次 (R1) | Sonnet | Sonnet | Opus |
   | 对抗轮次 (R2) | Sonnet | Opus | Opus |

   R2 prompt 追加"对抗审查员"角色说明 + R1 findings + design.md diff。

2. **主 agent 批判性评估**所有发现：逐条 Accept/Reject，每条必须附理由。不得全盘接受也不得无理由拒绝。
3. 对接受的问题修复 design.md，对拒绝的问题记录反驳理由。
4. **检查收敛**：分别记录 R1 和 R2 是否仍有未解决的 C/I：
   - 两者都无 C/I → 收敛完成，进入 Step 8
   - 仅 R1 有 C/I → 下轮只重跑 R1
   - 仅 R2 有 C/I → 下轮只重跑 R2
   - 两者都有 → 下轮并行重跑两者
5. **下轮 prompt** 注入上轮 findings + 修复/反驳清单（防止已反驳问题反复出现）。
6. 循环直到收敛或达 `max_rounds`。
7. **max_rounds 退出**时：
   - **[Interactive]** 展示剩余 findings + AskUserQuestion 确认是否接受当前状态推进。
   - **[Unattended · `degrade_policy` standard 或缺省]** 不询问，发送 Telegram 通知后暂停（任务保留，等待 `/task` 恢复人工决策）。
   - **[Unattended · `degrade_policy` conservative / headless]** 走 §9 **A4 accept-with-findings**：把剩余未解决 findings 原文写入 design.md 的 `## Unresolved Review Findings` 段 + `unattended-decisions.md` 的 `## Headless Degraded Decisions`，续跑推进；**同点同 phase 至多一次**——若本 phase 已因 A4 续跑过一次（unattended-decisions.md 已有该记录），第二次退回 standard（暂停 + Telegram）。兜底：P4 code review + P5 验收双网。

轮次数量由 `review.design_rounds` 决定（auto 按复杂度：Low:0, Medium:1, High:2），`max_rounds` 上限兜底（**reviewer-aware**：`max_rounds` 为标量则两 reviewer 共用；为对象 `{claude:N, codex:M}` 时 claude 取 `.claude`、codex 取 `.codex`，缺省 claude 3 / codex 8——codex 更严、收敛更慢）。`design_rounds: 0` 时跳过本步骤。

### Step 6.5 — P2.post-design-approved Hook

```bash
hat-plugin-hook {task-folder} P2.post-design-approved
```

按输出指令执行（review plugin: 确认 Review Strategy 在 design.md 中已正确记录）。

### Step 8 — User Review 确认循环

**[Unattended] 前置分支（不依赖是否执行 Step 7）**：
- 若存在 reviewer 结果且 `Critical = 0` 且 `Important = 0` → 自动批准并推进。
- 若无 reviewer 轮次（Low 复杂度跳过 Step 7）→ 直接自动批准并推进。
- 上述两种情况均**不输出**“是否有补充/回复继续”的纯文本确认。

1. Step 7 reviewer 收敛后（无 Critical/Important），展示**本轮 review 修改的变更差异**（仅本轮修改，非累积差异）
2. 纯文本询问用户是否有补充："以上是本轮 review 的修改内容，是否有补充？回复「继续」推进到 Plan 阶段。"
3. 用户说"继续" → 推进（须满足 DESIGN_PROTOCOL 顶部 HARD-GATE）
4. 用户给建议 → 澄清建议 → 修改 design.md → 判断是否重跑 Step 7：
   - 修改涉及架构决策、模块职责、接口定义 → 必须重跑 Step 7
   - 仅措辞/格式调整 → 可跳过 reviewer
   - 若重跑：展示新一轮差异 → 回到步骤 2
   - 若跳过：展示修改差异 → 回到步骤 2

**轮次计数**：跨确认循环累积不重置。若已达 max_rounds 则跳过 reviewer 直接进入确认。

**无 review 轮次时（Low 复杂度跳过 Step 7，仅 Interactive）**：直接询问："设计各节已确认，是否有补充？回复「继续」推进到 Plan 阶段。"

**变更差异显示规则**：每轮重置，只展示从上次确认点到现在的改动。

**[Unattended]** 已在本节前置分支短路：不进入本确认循环。

---

## phases.md Sync

每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

**Phase 2 完成时**：将 Phase 2 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

---

## P2 结束时间戳（core timing，内联）

Step 2e 完成后内联记录 phase_end：

```bash
hat-timing-stamp {task-folder} phase_end P2
```

> **B1**：P2.phase-end 的 linear 描述更新已并入 `P3.phase-end`（linear.md），故 P2 不再有 `hat-plugin-hook` 调用——P2 收尾仅内联 timing。

<rule>
P2 timing 经内联 `hat-timing-stamp`（phase_start/phase_end）。helper 自带 `observability.enabled` 门控（关闭档 → no-op）。
Reason: 内联是确定动作；缺 phase_start 触发 artifact-check 硬 FAIL，故 phase_start 内联点须前置。
</rule>

---

## Design 完成 → 过渡

Phase 2 完成，phases.md 已更新。

若 Activation Timing 选择了 "Design 阶段结束后启用"，在此过渡处确认 `unattended.json` 的 `activate_after: "design"` 已写入（实际翻 `enabled:true` 由编排器在过渡时执行）。

用用户配置的语言简要宣告设计结果（design.md 位置、复杂度评估），然后声明：**"Design 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

**[Unattended]** 若无人值守模式激活：发送 Telegram 通知 `[task-name] Phase 2 完成`。

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
Phase skill 完成后必须返回编排器 Step 3。不得在 transition section 中提示用户调用任何其他 skill。过渡路由是编排器的职责。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、compact、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 2 | 需要澄清问题 | 合并提问（最多 4 个）+ 末尾纯文本确认补充 |
| 3 | 提案完成后 | 用户选择方案 |
| 4 | 每节设计展示后 | 这部分看起来对吗？ |
| 2e | 复杂度与 preset 明显偏离时 | 配置面板修正 + activate_after 时机 |
| 6.5 | 自我 review 完成后 | Review 轮数、code review 策略、reviewer 模型 |
| 8 | 所有 review 完成后（仅 Interactive） | 等待用户明确批准 design.md（HARD-GATE） |

**[Unattended]** Step 8 不询问：有 reviewer 时按 C/I 门槛自动批准；无 reviewer 轮次（Low）时直接自动批准。

## Dependencies

- **Reads**: `{task-folder}/prompt.md`, `{task-folder}/task-config.json`（P1 已写入）, `{task-folder}/unattended.json`
- **Writes**: `{task-folder}/design.md`, `{task-folder}/task-config.json`, `{task-folder}/phases.md`, `{task-folder}/unattended.json`（activate_after 时）
- **Pre-injected**: `DESIGN_PROTOCOL.md`（设计流程单一来源）
- **Hooks**: `P2.post-design-draft`（review: self-review + independent review）, `P2.post-design-approved`（review: strategy write-back）（P2.phase-end 已无 hook——linear 描述更新并入 P3.phase-end，见 B1）
- **Core timing**（内联，非 hook）: phase_start P2（阶段开始）/ phase_end P2（Step 2e 完成后）经 `hat-timing-stamp`，受顶层 `observability.enabled` 门控
- **Scripts**: hat-plugin-hook, hat-timing-stamp
