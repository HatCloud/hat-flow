---
name: task-revise
user-invocable: false
description: "Use when a systemic issue found during Phase 4/5 needs an adaptive fix cycle. Triggered by task-execute (4b) or task-test (5d), routed by the orchestrator. Do NOT use for feature-sized additions (start a new task). 触发词: \"revise cycle\", \"修订循环\", \"修复系统性问题\""
word-budget: 1000
---

# Task Revise — Revise Cycle

Revise Cycle 处理器。在 Phase 4/5 内部执行一个**自适应单循环**：根因分析 →（按需）调整 design/plan → 执行修复 → 验证收尾，处理 code review 或 testing 发现的系统性问题。不再有 Full/Partial/Lite 深度档位——是否动 design/plan 由根因分析决定。

工具落点按 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/harness-tools.md` 映射。

**Announce at start:** "Using task-revise for Revise Cycle."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点（phase 内子循环，概览符号停留当前 phase 不变）：`full`——按 Revise section 步骤建/更新 step（`update_step`）；`overview`/`off`——no-op。恢复时同步 phases.md 中 Revise section 对应步骤。

---

## Resume Support

单循环 resume：如果 phases.md 中当前 Revise section 已有已完成的步骤（`[x]`），从第一个未完成（`[ ]`）的步骤继续。section 里**存在的步骤都是需要执行的**——按需跳过的 design/plan 步骤根本不会出现在 section 中（不使用 `[~]` 标记）。

---

## Unattended State

1. **读取状态**：`cat "{task-folder}/unattended.json" 2>/dev/null`（task-folder 从 Initialization 步骤 1 中解析 phases.md 所在路径获取，而非 open[0].path）
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议。后续停止点按协议自动决策。
3. **若文件不存在或 enabled != true**：正常交互流程

> **本文件所有「Telegram 通知」均经 `UNATTENDED_PROTOCOL.md` §4 发送**：Telegram 为 opt-in（companion 插件 `telegram@claude-plugins-official`）；未配置 chat_id / 插件未装 / MCP 不可用时静默降级（打印告警、不阻断 revise 流程），自动推进不依赖通知送达。

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

- Revise cycle 不嵌套：执行期间新冒出的问题不在当前 revise 内开第二层 revise，先把当前 revise 走完（DONE / DEFERRED），新问题留给回归阶段或后续 revise 处理。

### Initialization

1. 读取 phases.md，找到 `Status: IN_PROGRESS` 的 `## Revise RN` section（N 为编号，从标题 `## Revise R1` / `## Revise R2` 中提取数字。文档中 `RN` 泛指"当前 revise"，实际执行时替换为具体编号如 R1、R2）
   > Revise section 的**路由判定**（哪个 section 该执行——多 IN_PROGRESS 取最大编号、DONE 回归、DEFERRED 终结）权威表在 `task/SKILL.md` Revise 路由段；本 skill 只读已选中的 IN_PROGRESS section、不重复该决策。
2. 解析字段：Trigger, Return, Reason, Started
3. 读取 `{task-folder}/design.md` 和 `{task-folder}/plan.md` 了解原始设计和计划上下文

### RN-rootcause（根因分析）

接入 hatflow-systematic-debugging，先定位根因再决定改什么。

1. `Read ${CLAUDE_PLUGIN_ROOT}/skills/hatflow-systematic-debugging/SKILL.md`（Iron Law：无根因不修——先复现/定位，再判断）
2. 基于 code review findings 或 test failures 做根因分析：问题出在哪一层？是实现细节、计划遗漏，还是设计假设被证伪？**若 Revise section 含 `Rootcause hint`（5d 架构判别已给出层级+根因），以它为起点验证/细化，而非从零重做**——验证后若推翻则按实际改判。
3. 据根因判定本次 revise 需要触及哪些步骤，**按需把对应步骤插入 section**（在 RN-rootcause 之后、RN-execute 之前）：
   - 根因是**设计假设错误**（仍可在本 revise 内修） → 插入 `- [ ] RN-design` 与 `- [ ] RN-plan`
   - 根因是**计划遗漏/任务拆分不当**（设计仍成立） → 仅插入 `- [ ] RN-plan`
   - 根因是**实现细节** → 不插入，直接进入 RN-execute
   - 根因是**根本性问题**（框架不可用 / 核心假设被完全证伪 / 修复远超当前 revise scope） → 不插入任何步骤，**直接触发 Root-Problem Handling**（见 RN-execute 章节）：跳过 design/plan/execute，commit 已有半成品后标 DEFERRED
4. 标记 `RN-rootcause` 为 `[x]`，更新 phases.md

### RN-design（仅当根因需要设计调整）

精简版设计讨论，聚焦于 Reason 与根因分析定位的问题区域。

1. 与用户讨论修订方案（向用户提问（结构化选项优先） 提出 2-3 个选项）
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
触及 design 或 plan 的 revise，在 RN-design / RN-plan 步骤标记完成前都带一个确认循环；推进到 RN-execute 需要用户对修订方案的显式批准。
Reason: 缺少用户 review 的 revise 会得到只治标、错过根因的临时补丁，task-workflow-fixes 的 R1 已观察到这一现象。
</rule>

### RN-execute

执行 revise 任务。

1. **Pre-execute Checkpoint**（NO_GIT 模式下跳过）：如有未提交的代码变更，先 commit（保持工作树干净，便于后续按 commit 边界回归）
2. 读取 `{task-folder}/task-config.json` 获取执行模式和引擎选择
3. 逐个执行 revise tasks（复用主流程的引擎选择逻辑）
4. 每个 task 完成后 commit（git 启用时由 git plugin hook 提供 commit 规范）
5. 更新 phases.md：标记 `RN-execute` 为 `[x]`

**Root-Problem Handling**：如果**根因分析（RN-rootcause）判定**、或**执行中新暴露**了**根本性问题**（框架不可用、核心假设完全错误、修复需要远超当前 revise scope 的改动），无论问题在哪个步骤被发现，都走以下处理（rootcause 阶段触发时跳过 design/plan/execute）：

<rule>
revise execute 期间出现根本性问题会终止循环并触发 向用户提问（结构化选项优先）。选项：
1. **升级转人工** — 当前 revise 标记 DEFERRED，移交给人工处理。
2. **转为新任务** — 当前 revise 标记 DEFERRED，新开一个任务来处理该根本性问题。
代码从不 reset。标记 DEFERRED 前，半成品以 `chore: WIP [DEFERRED Rn] <原因>` 提交，该 commit SHA 记入 Revise section 的 **WIP Commit** 字段。
Reason: reset 代码会丢弃部分进度、并在恢复时污染工作树；DEFERRED 把 WIP 留在一个带标记的 commit 后面，让人工或新任务能从恰好停下的地方接着干。
</rule>

### RN-verify

标记 Revise Cycle 完成，返回编排器。

1. 更新 phases.md：标记 `RN-verify` 为 `[x]`
2. 将 Revise RN 的 `**Status**: IN_PROGRESS` 改为 `**Status**: DONE`
3. 声明：**"Revise RN 完成。"**

**注意**：RN-verify 的含义是"revise 执行完毕，等待回归验证"，而非"revise 自身验证通过"。实际验证由回归阶段的原 phase skill 执行（task-execute 重跑 4b 或 task-test 重跑相关测试项）。

---

## Chain Detection

<rule>
当 Revise 编号达到 R3 或更高（已完成 2 个以上 revise cycle），流程停止并触发一个 向用户提问（结构化选项优先） 警告。选项：
1. **继续 R3** — 已理解风险，继续
2. **拆分为新任务** — 当前任务 scope 可能过大，开新 task 处理
3. **重新审视整体设计** — 回到 Phase 2 重做设计
Reason: 反复 revise 意味着原始设计存在根本性缺陷；重新设计优于持续打补丁。
</rule>

---

## Error Handling

| 异常场景 | 处理方式 |
|----------|----------|
| Revise execute 中卡壳/根本性问题 | 接 hatflow-systematic-debugging 定位根因；确为根本性问题 → Root-Problem Handling（DEFERRED + WIP commit + 转人工/新任务） |
| Revise design 讨论无法达成共识 | 向用户提问（结构化选项优先）：简化 revise 范围 / 转新任务（DEFERRED） / 取消 revise + patch in place |

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
revise 完成后，控制权交还编排器；该过渡不会提示用户去调用任何 skill，也不会自行决定下一步。
Reason: revise 不具备 Return 步骤的完整上下文（回归模式、phase_merge 等）；自行路由会跳过编排器的检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| RN-design | 方案选择 | 选择修订方案 |
| RN-plan | 任务列表确认 | revise 任务列表是否完整 |
| RN-execute | 发现根本性问题 | 升级转人工 / 转新任务（均标 DEFERRED，不 reset 代码） |
| Chain R3+ | 第 3 次以上 revise | 继续 / 拆分 / 重新设计 |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/plan.md`, `{task-folder}/phases.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/design.md`（按需追加 Revise section）, `{task-folder}/plan.md`（按需追加 Revise section）, `{task-folder}/phases.md`
- **References**: `hatflow-systematic-debugging`（根因分析，RN-rootcause 步骤）, `task/SKILL.md`（Revise 路由权威表，Initialization 读取）
- **Invokes**: subagent for execute（按 task-config.json execution 配置）
- **Git**: WIP commit on DEFERRED（无 git tag / 无 git reset）
