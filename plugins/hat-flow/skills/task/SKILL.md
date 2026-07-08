---
name: task
description: "Use when starting a new task or resuming an in-progress one. Routes to the correct phase based on phases.md state. Do NOT use for tasks already completed (use /task-end) or to cancel (use /task-cancel). 触发词: \"新任务\", \"开始任务\", \"做个任务\", \"创建任务\", \"继续任务\", \"resume task\""
self-evolving: true
word-budget: exempt
---

# Task — Orchestration Layer

任务生命周期编排器。读取任务文件夹中的 `phases.md` 决定从哪个阶段继续，加载对应的阶段 skill 执行，支持跨 session 恢复。

**Announce at start:** "Using task to orchestrate the task lifecycle."

**Unattended / Quiet Mode：** 入口 **Step 0** 统一解析 `$ARGUMENTS`，由显式信号（`-q` / `--quiet` / `--headless` / 「无人值守」关键词）确立 `quiet_mode` 与 `flag_overrides`。quiet_mode=true 时在进入 Init 前即按无人值守语义执行，并由 task-init 1f 物化 `unattended.json`（新任务）；恢复既有任务时若 `unattended.json` 已存在则静默沿用。非 quiet 的交互路径下，Step 2A.1（Phase 过渡、仅文件不存在时询问）为交互激活主入口（入口序见 `UNATTENDED_PROTOCOL.md` §5）。

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Dirty: !`git status --porcelain 2>/dev/null | head -5`
- Check (light): !`r=$(grep -A1 '轻量' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`
- Check (full): !`r=$(grep -A1 '完整' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'`
- Lessons (编排经验库): !`cat "${CLAUDE_SKILL_DIR}/references/lessons.md" 2>/dev/null || echo "(暂缺)"`
- 自进化准则（受管注入）: (本分发版已停用自进化，无注入)
- User input: $ARGUMENTS

> 以上数据在 skill 加载时已预获取，视为权威事实，无需重新查询。

## NO_GIT Mode

如果 Branch 值为 `NO_GIT`，说明不在 git 仓库中。将此标志传递给阶段 skill 执行时，该 skill 会自动跳过所有 git 操作（分支创建、commit、`.last-verified`）。

## Trivial Task Exemption

仅当以下**三个条件全部满足**时，才可以通过 AskUserQuestion 询问用户是否跳过此工作流：

1. 变更纯粹是外观性的，不影响逻辑（拼写错误、空格、常量值）
2. 整个变更可以用一条 commit message 描述
3. 不引入新行为

不确定时默认走完整工作流。

> **与 lite/hotfix 档位的分界**（避免混淆）：**Trivial = 完全跳过工作流**（不建任务文件夹、直接改+commit），仅限上述三条全中的外观性改动；**lite/hotfix = 仍走工作流但精简档位**（建任务、跑裁剪后的 phase），用于"小但有逻辑/新行为"的改动。拿不准是否 Trivial 时选 lite，而非跳过。本节三条件是 Step 1 Step 1B「Trivial Task Check」的唯一判据来源，勿在别处另立。

<rule>
跳过工作流的前提是先发起一次 AskUserQuestion：三个免除条件全部成立、且用户明确同意。两者缺一时，走完整工作流。
Reason: 自我判定为「trivial」的变更经常隐藏着未被察觉的复杂度。
</rule>

---

## TODO Sync (TaskCreate / TaskUpdate)

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的确定性触发点表 + 4 命名模板执行——三档语义、双层结构、显示效果、全生命周期触发契约均以该文件为唯一权威。

本 skill（orchestrator）触发点：
- **phase 切换**（Step 3）：`update_overview` 更新概览符号（`full`/`overview`）；`off` no-op。
- **Bootstrap / 跨 session RESUME**（Step 2B）：先 `TaskList`——有 overview→`TaskUpdate` 刷新符号到 phases.md 当前态，无→重建（首个 TaskCreate 取最小 ID）+ `in_progress`（`full` 再按 phases.md 重建当前 phase step）；`off` no-op（不重建、不刷新、不清理）。

---

## Hook Execution Routing

每个 phase skill 运行 `hat-plugin-hook {task-folder} {hook-point}` 后，编排器对其 **stdout 逐段同步 inline 执行**：每段以注释头 `<!-- plugin:P hook:H on_error:E -->` 开头、后随指令正文，按输出顺序在主线程执行。`hat-plugin-hook` 无状态、不检测任何环境变量——每次按当前 frontmatter config 重新解析路由；所有 hook 均为 inline。`on_error: blocking` 的 hook 失败即中止，`graceful` 记录后继续。

---

## Phase Routing

<rule>
Phase 选择先读 phases.md；一旦某个 phase skill 加载，其指令就覆盖编排器的通用指引。
Reason: phases.md 是唯一的跨 session 状态源，每个 phase SKILL.md 持有该 phase 权威的逐步指令。`$ARGUMENTS` 只说明有什么新输入，而非已经做了什么；即便参数看起来已把工作交代清楚，phases.md 仍是权威。
</rule>

### Step 0: Quiet Mode & Flag Parsing（入口，先于一切）

在 Step 1 之前解析 `$ARGUMENTS`，确立 **quiet_mode** 与 **flag_overrides**，使无头/参数化贯穿全程（Init 之前即生效）。

**双信号判定 `quiet_mode`（OR）：**

| 信号 | 来源 | 结果 |
|------|------|------|
| **显式（兜底保证）** | `$ARGUMENTS` 含 `-q` / `--quiet` / `--headless`，或「无人值守」关键词 | `quiet_mode = true` |
| **自动探测（尽力，仅参考）** | 无稳定信号——实测交互会话 `CLAUDE_CODE_ENTRYPOINT=cli` 且工具内 `test -t 0` 恒非 TTY，`claude -p` 无官方专用环境变量 | **不据此翻转** `quiet_mode`（避免误把交互会话判为无头而静默吞掉交互） |

<rule>
quiet_mode 只由显式信号确立（`-q`/`--quiet`/`--headless`/「无人值守」）；自动探测 env/TTY 不会将其翻开。
Reason: 实测没有稳定的无头信号——交互会话同样会显示 `CLAUDE_CODE_ENTRYPOINT=cli`、且工具调用内 stdin 非 TTY，因此自动探测会产生误报，在有用户在场的会话里静默吞掉交互。`claude -p` 用户会传 `-q`（README 已记载）。显式信号才是有保证的契约。
</rule>

**flag 解析（从 `$ARGUMENTS` 剥离后，剩余文本作需求/Linear ID/tier 关键词交给 task-init 1b 继续解析）：**

| flag | 写入 `flag_overrides` | 备注 |
|------|----------------------|------|
| `-q` / `--quiet` | — | `quiet_mode=true`；`degrade_policy → conservative` |
| `--headless` | — | `quiet_mode=true`；`degrade_policy → headless`（M1 先按 conservative 行为执行，完整 headless 档后续） |
| 「无人值守」关键词 | — | `quiet_mode=true`；`degrade_policy → conservative` |
| `--worktree on\|off\|ask` | `branch.worktree = true\|false\|"ask"` | 显式控制 worktree（任何模式生效） |
| `--no-worktree` | `branch.worktree = false` | `--worktree off` 简写 |
| `--branch keep\|new` | `branch.mode = "keep"\|"new"` | 显式控制分支策略 |

- `flag_overrides` 是稀疏 JSON（如 `{"branch":{"worktree":false}}`），作为第 ④ 层经 task-init 1b.3 第 5 步传给 `hat-task-config-resolve --flags`。
- `degrade_policy`（由 `-q`/`--headless` 映射）随 quiet 写入：task-init 1f 物化 `unattended.json` 时落 `degrade_policy` 字段；非 quiet 模式恒为 `standard`（不写、按缺省）。
- tier 关键词（`full`/`standard`/`lite`/`hotfix`/`--tier`）与 Linear ID **不在此剥离**——保留给 task-init 1b 解析。

**quiet_mode 贯穿：** quiet_mode=true 时——
1. 在进入 Init **之前**即按无人值守语义执行（task-init 各停顿点走 `[Unattended]` 分支，值取 effective config 的 `headless.*` / `branch.*`）；
2. task-init 1b.3 第 5 步解析 config 时追加 `--quiet`（使 `branch.worktree` 的 `"ask"` 解析为 true）；
3. task-init 1f 物化 `task-config.json`（`_source:"headless"`）+ `unattended.json`（`enabled:true, activate_after:"now", task_type:"self_test", degrade_policy, end_decisions` 取 config 默认），使 Init 之后全程无人值守（详见 task-init 1f 与 `UNATTENDED_PROTOCOL.md`）。

**[Unattended]** 本步骤无交互——纯解析 `$ARGUMENTS`，无 AskUserQuestion。quiet_mode 与 flag_overrides 在后续 Init/Design/... 全程可用。

### Step 1: Determine State

**A. Check open tasks** (from Runtime Context Tasks JSON):

- **No open tasks** AND `$ARGUMENTS` 为空 → AskUserQuestion 询问任务描述
- **No open tasks** → 新任务，跳到 Step 2A（Init）
- **1 open task** → 读取该任务文件夹的 `phases.md`（如果存在），跳到 Step 2B（Resume）
- **多个 open tasks** → 先拿 `$ARGUMENTS` 与各 open task 的文件夹名 / 任务名做子串匹配：**唯一命中 → 直接选中，跳到 Step 2B（Resume），不询问**（新会话交接命令自带任务名，恢复时不多问一次）；无命中或多重命中 → AskUserQuestion 让用户选择；选定后跳到 Step 2B（Resume）

**B. Trivial Task Check** (仅对新任务): 如果 `$ARGUMENTS` 满足全部 3 个免除条件，AskUserQuestion 确认后跳过工作流。

### Step 2A: New Task — Phase 1

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md
```

读取完成后，按照 `task-init/SKILL.md` 的指示执行 Phase 1 的全部步骤。

Phase 1 完成后（task-init SKILL.md 指示 DONE），执行 **Step 2A.1**，然后继续 Step 3。

### Step 2A.1: Unattended Mode Check（Phase 过渡时）

> **主要激活入口已移至 P2 Step 2e 配置面板。** Phase 过渡时的询问为后备入口，仅当 Phase 1/2/3 完成且 unattended.json 不存在时触发。
>
> **与 Step 3 步骤 3 的关系（单一机制，勿各自演化）**：Phase 过渡时的无人值守判定权威序列（declined 短路 → activate_after 激活 → 文件不存在则询问 → 否则静默）定义在 **Step 3 步骤 3**；本 Step 2A.1 是其中「文件不存在 → 询问激活时机」分支的**询问子过程**（拥有下方 AskUserQuestion 选项），同时供 Step 2A（新任务 Init 完成后）直接调用。两处的 declined 短路 / 「已存在则静默」语义必须一致——改其一须同步改另一。

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
被拒绝/取消而没有语义回答的 AskUserQuestion 不推断任何默认值，等同于「未选任何选项」；用户意图先以纯文本确认。
Reason: 被取消的提问不是一个选择——推断「用户指的是推荐选项」会静默落定一个用户从未做出的决定（分支策略、无人值守激活、范围）。这适用于整个工作流的所有 AskUserQuestion 调用，包括 Interactive 模式下「UI 拒绝」不同于「真实回答」的停顿点。
</rule>

### Step 2B: Resume Existing Task

**Step 2B.0: Worktree 回切（worktree 隔离任务的跨 session 恢复，先于读状态文件）**

若选定的 open task 含 `worktree` 字段（来自主仓库 stub 的 `.worktree` 指针，由 `hat-task-detect` 读出）且当前 CWD 不在该 worktree 内（正从主仓库恢复）：

1. `EnterWorktree(path="{worktree 指针路径}")` 切入已注册的 worktree（session CWD 随之切换）。
2. 切入后重新 `hat-task-detect .tasks` 定位 worktree 内真实任务文件夹（含 phases.md / design.md / task-config.json / unattended.json）。
3. **追加当前 session-id 到 worktree 内的 session.json**（见下方第 4 步逻辑）。后续所有状态读取均针对 worktree 内的任务文件夹。

若指针路径不存在（worktree 被手动删除）→ **[Interactive]** AskUserQuestion：在主仓库继续（放弃隔离）/ 中止；**[Unattended]** 按 `UNATTENDED_PROTOCOL.md` §8 暂停 + Telegram 通知（无法自动重建隔离环境，不擅自在主仓库续跑）。

**[Unattended]** worktree 回切无交互——指针有效则自动 `EnterWorktree`；失效才暂停通知。

读取恢复所需的状态文件：

1. 读取 `{task-folder}/phases.md`（进度状态）
2. 读取 `{task-folder}/task-config.json`（插件配置）— 不存在时降级：
   - 从 `{task-folder}/design.md ## Execution Strategy` 推断基本配置
   - 仍无法推断 → 使用 standard preset 默认值
   - 降级时**不**写入 task-config.json（留给 P2 Step 2e 正式生成）
3. 读取 `{task-folder}/unattended.json`（无人值守状态，可选）
3.5. **戳运行态信号**：`hat-task-state running "{task-folder}"`（外部驱动可机读的状态文件，契约见 `references/headless-driving.md`；graceful——失败仅 stderr 告警，不阻断恢复）。
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
- phases.md 格式损坏（无法解析 Revise section）→ **[Interactive]** AskUserQuestion：手动修复 / 忽略 Revise 继续正常路由；**[Unattended]** 暂停 + Telegram 通知，等 `/task` 恢复（状态文件损坏属 §9 HARD-STOP：自动「忽略 Revise 续跑」可能丢 IN_PROGRESS 的 revise 半成品，倾向暂停而非 auto-cancel，见 `UNATTENDED_PROTOCOL.md` §8/§9）
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

**如果 phases.md 不存在**（任务文件夹存在但没有 phases.md）——phases.md 是 Phase Status 的唯一来源，缺失时改用可观测产物信号路由（与 task-init 1a「继续现有任务」判据同表）：
- 有 `plan.md`：含未勾 `[ ]` → 路由 Phase 4（执行未完成）；全部 `[x]`（无未勾）→ 路由 Phase 5（执行完成，待测试/验收）
- 无 `plan.md` 但有 `design.md` → 路由 Phase 3
- 两者都没有 → 路由 Phase 2

<HARD-GATE>
执行某 phase 的任何步骤都要求在当前 turn 内 Read 该 phase 的 SKILL.md；记忆或对话 summary 不能替代。
Reason: 每个 phase SKILL.md 携带产出该 phase 产物的 hook 调用（review/git/linear）。漏读会静默跳过这些 hook，任务带着缺失的产物归档——失败一直隐形到 task-end 才暴露。真实案例：bin-unit-tests L866 声称「读了 task-end SKILL.md」却从未真正读，于是 P5/P6 hook 从未运行、conversation.md 从未生成。它是 HARD-GATE，因为一次漏读会毒化每一个下游产物。
</HARD-GATE>

**Rationalization 表**（执行任何 phase 前自检——命中任意一条即停下，先 Read 当前 phase SKILL.md）：

| Rationalization | Reality |
|---|---|
| "我记得这个 phase 的步骤，不用再读 SKILL.md" | 记忆会漏掉 hook 调用；phase SKILL.md 是当前权威，当前 turn 重读。 |
| "summary / 上下文里已经有 phase 内容了" | summary 是压缩产物，hook 命令常被省略；读原文。 |
| "上一个 session 我读过这个 SKILL.md" | 跨 session 记忆不可靠，且 SKILL.md 可能已更新；重读。 |
| "这个 phase 很简单，直接做就行" | 觉得简单正是漏 hook 的高发场景（bin-unit-tests 元 bug 即如此）。 |

<rule>
经 Read 加载的 phase SKILL.md 中动态注入行不会展开——正文出现字面 `!`cat <路径>`` 时当场 Read 该路径文件，出现字面 `!`<命令>`` 时当场用 Bash 执行取结果，再继续该步骤。
Reason: `!` 注入只在技能经 Skill / 斜杠激活时由 harness 展开；编排器用 Read 工具路由 phase skill，注入行原样留在正文——DESIGN_PROTOCOL / PLAN_PROMPT 等协议正文与 Runtime Context 探测结果会静默缺失，而按「协议单一来源」约定 SKILL.md 不重述这些内容，缺了等于整段流程丢失（ISSUE 审计 F5 实证）。
</rule>

<rule>
一切 subagent / codex / headless worker 派发都带超时上限（缺省 10 分钟，长任务在派发时显式放宽）；超时或瞬时 infra 错误（529 / 网关超时）退避重试至多 1 次，仍失败即转 fallback（主 agent 自验 / 降级路径）并留痕（unattended-decisions.md 或 fallback-log.jsonl），不无限等待。
Reason: 派发无超时曾致 codex review 续接挂起超过 10 分钟无信号、review subagent 连续 529 空转约 25 分钟，全靠人工发现（ISSUE / ISSUE 实证）；待验内容多数可由主 agent 机械自验，无限等待的代价远高于降级。
</rule>

### Step 3: Continue to Next Phase

**Phase 过渡类型表**（各边界的交互程度，用语义描述以避免 phase_merge 后序号变化）：

| 过渡边界 | 产物检查 | 新会话交接建议 | Unattended 检查 | 停顿类型 |
|---------|----------|-------------|----------------|----------|
| Init 完成后 | ✓ | — | ✓ | 有交互点（unattended 询问） |
| Design 完成后 | ✓ | 降级时* | ✓ | 有交互点（unattended 询问） |
| Plan 完成后 | ✓ | **✓（必触发）** | ✓ | **软停顿**（交接建议等待用户回复） |
| Execute 完成后 | ✓ | — | — | 产物检查通过后推进 |
| Test 完成后 | **✓（P5 门控）** | — | — | **硬停**（用户必须调用 `/task-end`） |

*降级：phase_merge 将 Plan 和 Execute 合并时，交接建议前移到 Design 完成后

每个阶段完成后，该阶段的 SKILL.md 会负责更新 `phases.md`。返回此处：
1. 读取更新后的 `phases.md`，确认当前阶段已标记为 DONE
1.1. **phase_merge 检查**：读取 `{task-folder}/task-config.json` 的 `phase_merge` 字段。检查当前完成的阶段和下一个阶段是否在某个 merge 组中。
   - **匹配且下一阶段不是 End** → 跳过步骤 1.5（产物检查）、步骤 2（新会话交接）、步骤 3（unattended），直接加载下一阶段的 SKILL.md
   - **不匹配** → 正常执行后续步骤
   - **硬约束**：Test→End 永不可合并——即使 phase_merge 包含该组合，仍执行 End 准入检查（硬停）
1.5. **产物完整性门控**：运行 `hat-task-artifact-check {task-folder} {完成的phase编号}` （如 task-config.json 存在，追加 `--config {task-folder}/task-config.json`）。
   - **PASS** → 继续
   - **FAIL** → 尝试 fallback 补齐缺失文件（主 agent 按 task-config 与 design.md 补齐）。**补齐仅一轮**（不循环补齐——补齐→重跑一次即终态判定）。
   - 重跑仍 FAIL → 阻断推进（终态），告知用户缺失的文件清单；不再反复补齐（幂等约束同 task-end 3.3.7）
2. **新会话交接建议**（仅 Plan 完成后、且 Interactive 模式触发）：
   - **前置门（最先判断）**：读取 `{task-folder}/unattended.json`。若 `enabled == true`（已是无人值守），**或** `enabled == false` 且 `activate_after` 匹配当前过渡点（本过渡点步骤 3 即将激活无人值守）→ **完全跳过本步，不输出任何交接命令块**，直接进入步骤 3。这是前置条件判断，不是"先输出再说跳过"。
   - **触发条件**（仅 Interactive）：刚完成的阶段是 Plan
   - **降级规则**：若 phase_merge 将 Plan 和 Execute 合并，触发点前移至 Design 完成后
   - **Hotfix 例外**：若 `task-config.json` 中 `todo_sync == "off"` 或 `p5_auto_only == true`，跳过交接建议
   - **其他过渡**：不给交接建议
   - 触发时无条件给出交接建议（不评估上下文大小）：任务状态已全量落盘（phases.md / task-config.json / plan.md），新会话从文件态恢复比压缩后续跑更干净（无摘要失真、无残留上下文计费）。输出一个可直接复制的命令块：

     ```bash
     cd {项目根绝对路径} && claude -n "{task-folder-name}" "/task 继续任务「{任务名}」：任务目录 {task-folder}，Plan 已完成、从 Execute 开始。先读该目录下 phases.md 与 task-config.json 恢复进度，按 Resume 流程继续。任务目标：{一句话摘要}"
     ```

     占位符取值：{项目根绝对路径} = 当前 session 的项目根（worktree 任务即 worktree 根）；{task-folder} = 相对项目根的任务目录路径；{一句话摘要} 从 prompt.md 提炼、一句以内。
   - 建议后等待用户回复。用户在新终端执行该命令 → 本会话直接弃用（状态已落盘，无需收尾动作）；用户回复"继续" → 留在当前会话推进

**[Unattended]** 新会话交接软停是面向交互用户的停顿——前置门跳过 `enabled:true`（已激活）与"本过渡点即将激活（`enabled:false` 且 activate_after 匹配）"两种无人值守情形，不输出任何等待用户回复的交接命令块（见上方 HARD-GATE）。

<HARD-GATE>
无人值守模式下，Plan→Execute 边界不输出任何交接命令块：先检查 unattended.json，在产生任何输出之前就整段跳过交接步骤。
Reason: 交接建议是等待用户回复的软停顿。无人值守模式下没有用户可回复，输出它会让流程无限期停滞——正是 bin-unit-tests 的失败（当时为 /compact 建议，机制同）。这道守卫是前置条件，而非事后的「[Unattended] skip」，因为后者仍有在评估跳过之前就把块输出出去的风险。
</HARD-GATE>
3. **Unattended Mode Check**（仅刚完成的是 Init、Design 或 Plan 时执行；判定顺序：先 declined 短路，再 activate_after 激活，再"文件不存在→询问"）：
   - **3-a0. declined 短路（最先判断，优先于 activate_after）**：读取 `{task-folder}/unattended.json`。若文件存在且 `declined == true` → 用户已拒绝无人值守，静默继续、不询问、不进激活分支、不推断 `activate_after`。跳过 3-a/3-b/3-c。（declined 哨兵无 `activate_after`，必须显式短路，避免 §1「缺省视为 now」误读为待激活，见 `UNATTENDED_PROTOCOL.md` §5）
   - **3-a. activate_after 激活分支（共享契约 SC3 consumer 侧，对接 task-design producer）**：读取 `{task-folder}/unattended.json`。若文件存在 且 `enabled == false` 且 `activate_after` 匹配当前过渡点（`activate_after == "design"` 且刚完成 Design / `activate_after == "plan"` 且刚完成 Plan）→ 把 `enabled` 字段写回为 `true`，并 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md` 加载无人值守协议（自此进入无人值守）。激活后发送 Telegram 通知（`[task-name] 无人值守模式已激活`；chat_id 为 null 时按 `UNATTENDED_PROTOCOL.md` §4 跳过发送并打印降级告警）。
   - **3-b. 文件不存在 → 询问分支**：若 `unattended.json` 不存在 → 执行 Step 2A.1（询问无人值守激活时机）
   - **3-c.** 其余情况（文件存在且 `enabled == true`，或存在但 `activate_after` 不匹配当前过渡点且非 declined）：静默继续，不询问

**[Unattended]** 步骤 3 的激活/询问自身可无人值守推进：activate_after 匹配 → 自动翻 `enabled`（无需人工）；已 `enabled:true` → 静默继续；仅"文件不存在 + 未给无人值守意图"才走 Step 2A.1 的交互询问（Interactive 路径）。
4. **End 准入检查**：Test 完成后，步骤 1.5 已对 phase 5 跑产物门控（`hat-task-artifact-check {task-folder} 5`，即 P5 门控——确认 Test 阶段产物齐全）。门控 PASS 后，若 End 仍 PENDING → 硬停，告知用户调用 `/task-end`。门控 FAIL → 先按步骤 1.5 补齐/阻断，不进入 End。仅 unattended self_test 模式允许自动推进。
5. 否则：先 `hat-task-state running "{task-folder}"`（graceful），再加载下一个阶段的 SKILL.md，继续执行

重复直到 Test 完成（End 由用户手动触发）。

<rule>
任何等待用户输入的回合结束前（AskUserQuestion 之前、纯文本停点之前、硬停宣告之前），先运行 `hat-task-state waiting "{task-folder}" --phase N --stop-point <语义 slug> --resume-hint approve|choice|free_text --expect "<一句人读提示>"` 再停；写失败仅 stderr 告警、照常停下（graceful，非硬依赖）。此规则为全 phase 共用的编排纪律——phase skill 停点表不重复写入指令。
Reason: 外部驱动方（E2E 回归、cron、调度器）依赖 state.json 机械判定「在等什么、回什么能推进」，不再解析输出文本猜停点（E2E 首跑实证 3 次 UNMATCHED）；契约与消费算法见 `references/headless-driving.md`。
</rule>

<rule>
普通（非无人值守）模式下，End phase 不从 Test 自动推进：进入 End 要求用户显式调用 `/task-end`。这是一个有意保留的决策点——自动化测试通过不等于用户验收。
Reason: dogfooding 期间的用户反馈发现 End phase 有时会在没有用户确认的情况下自动推进。
</rule>

<rule>
Phase 过渡都经由对应的 SKILL.md。漏掉某个 SKILL.md 会让 phases.md 未更新、TODO sync 未运行，任务带着不完整状态归档。
Reason: M0 复盘发现 Execute phase 归档时所有步骤仍为 [ ]、Status 仍是 PENDING，原因是 task-execute/SKILL.md 从未被加载。
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
- [ ] 1b.2b 头脑风暴补完
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

## 自进化

本 orchestrator `self-evolving: true`，每轮收尾沉淀**编排决策类**经验。完整自进化过程准则（裁决漏斗 / 写入闸 / 整合 / changelog 纪律）由启动时硬注入的受管全局母本 `spec-skill/references/self-evolution-canonical.md` 提供（spec-skill canonical，受管·勿改），此处不再手写以防漂移。

**Changelog 归并**：task 套件全体 skill 的 changelog 已合并进本 orchestrator 的 `references/changelog.md`（按 skill 分节，原各 worker 的 `references/changelog.md` 已删除）。受管准则中通用的 `references/changelog.md` 即指此文件——本 orchestrator 自进化条目写入 `## task (orchestrator)` 节顶部。6 个 phase worker 为 `self-evolving: inbox` 形态（lessons.md 是收件箱：retrospective 插件写入、skill-revise 消费固化，worker 自身不做运行时自进化——形态定义见 spec-skill `references/self-evolution-spec.md` 编排族节）。

**task 专属归属补充**：往 `lessons.md` 写一条前，除受管准则的写入闸外，再追问归属——「这条下次会在 task 的哪个编排决策点（路由/分支/无人值守/跨 worker 协调）被读到？」执行细节属对应 worker（task-init/-design/… 各自的 lessons），不放这里；不给编排族另建 series 级公共经验库。

## Dependencies

- **Runtime loads**: `${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md`, `task-design/SKILL.md`, `task-plan/SKILL.md`, `task-execute/SKILL.md`, `task-test/SKILL.md`, `task-end/SKILL.md`（via Read at routing time）
- **Conditional load**: `${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`（仅当 unattended.json 存在时加载）, `${CLAUDE_PLUGIN_ROOT}/skills/task-revise/SKILL.md`（仅当 phases.md 包含 IN_PROGRESS 的 Revise section 时加载）
- **Reference files（按需 Read）**: `task/references/todo-sync.md`, `task/references/review-workflow.md`, `task/DESIGN_PROTOCOL.md`（task-design 加载）, `task/PLAN_PROMPT.md`（task-plan 加载）
- **Scripts**: hat-task-detect, hat-task-artifact-check, hat-plugin-hook, hat-task-state（状态信号写入，契约见 `references/headless-driving.md`）
- **State files**: `{task-folder}/phases.md`, `{task-folder}/task-config.json`
- **Unattended state**: `{task-folder}/unattended.json`
