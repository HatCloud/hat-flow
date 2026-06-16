---
name: task-init
user-invocable: false
description: "Use when initializing a new task (Phase 1: Setup). Handles git branch, task folder creation, Linear setup, and requirement confirmation. Can be called standalone or via /task orchestrator. 触发词: \"初始化任务\", \"task init\", \"开始初始化\""
---

# Task Init — Phase 1: Setup

任务初始化阶段。解析用户输入、确认需求、设置 git 分支、创建任务文件夹、处理 Linear 集成，并生成 `phases.md`（跨 session 恢复的状态文件）。

**Announce at start:** "Using task-init for Phase 1: Setup."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Dirty: !`git status --porcelain 2>/dev/null | head -5`
- User input: $ARGUMENTS

## NO_GIT Mode

如果 Branch 值为 `NO_GIT`，跳过以下步骤：1c（Git 规范 + Dirty 检查）、1d（分支决策，直接在 CWD 下创建任务文件夹）、1d-wt（Worktree 隔离，依赖 git）、1c 中的 phases.md git commit。其余步骤正常执行。

---

## Red Flags

| If you think... | Reality |
|---|---|
| "Let me explore the codebase to understand the request before confirming" | Init does NOT explore code. Exploration belongs to Phase 2 (Design). Confirm the requirement first. |
| "The requirement is clear enough, skip the structured restate" | Step 1b.1 is mandatory for ALL input types. Implicit understanding is where rework starts. |
| "User implied which branch they want, I'll just create it" | Interactive mode: never create a branch without an explicit AskUserQuestion answer (1d Iron Law). Quiet/unattended: follow `branch.mode` config (default keep), do NOT ask. |
| "I'll pick the tier myself, no need to ask" | 1b.3 tier choice is a mandatory stop point (except Unattended). Recommend, then confirm. |
| "Let me write the task folder before the branch is settled" | All filesystem writes happen in 1f, AFTER branch setup. Writing early strands files on the wrong branch. |
| "Linear creation failed, I'll silently continue" | On Linear failure, AskUserQuestion (retry / skip). Do NOT silently drop the integration. |

---

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），**先**从 phases.md 重建概览行（确保拿到最小 ID 以固定在首行）并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。

---

## Resume Support

**如果由 `/task` 编排器调用** 且已有 `phases.md`：在每个步骤开始前检查 phases.md 中对应步骤是否已标记 `[x]`。如果是，跳过该步骤，继续下一步。

**phases.md 中步骤名称对应：**
- `1a. 检查现有任务` → 步骤 1a
- `1b. 解析参数 + 需求确认` → 步骤 1b + 1b.1
- `1b.2 Prompt 质量分析` → 步骤 1b.2
- `1b.3 档位粗选` → 步骤 1b.3
- `1c. Git 规范 + 工作目录` → 步骤 1c
- `1d. 分支决策` → 步骤 1d
- `1e. Linear 上下文` → 步骤 1e
- `1f. 创建任务文件夹 + prompt.md` → 步骤 1f

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议，后续所有停止点按协议自动决策
3. **若文件不存在或 enabled != true**：正常交互流程
4. **恢复场景检测**：若 `{open[0].path}/unattended.json` 存在（即恢复任务时），后续停止点按协议自动决策：
   - Git 规范不存在 → 自动使用 Conventional Commits
   - Dirty 文件 → 忽略继续
   - 分支决策 → 留在当前分支
   - Linear issue → 自动创建；Linear 失败 → 跳过

> 无人值守模式的激活（unattended.json 创建）有两条入口：① **Quiet 入口**——编排器 Step 0 由显式信号确立 `quiet_mode` 时，由 task-init **1f** 直接物化 `unattended.json`（`_source:"headless"` 的 config + `enabled:true`），使 Init 之后全程无人值守；② **交互延后入口**——非 quiet 时，由编排器 Step 2A.1 / task-design Activation Timing 询问激活时机后创建。各阶段 skill 读取已有状态。

---

### 1a. Check Existing Tasks

从 Runtime Context 读取 Tasks JSON。

**If `open` array is not empty:**

使用 AskUserQuestion 列出现有任务。选项：**继续现有任务** / **创建新任务**

如果选择继续，按状态路由（在主 session 中）：
- 有 `phases.md` → 由 `/task` 编排器处理路由
- 有 `plan.md` 且包含未勾选项 → 跳到 Phase 4（Execution）
- 有 `design.md` 但没有 `plan.md` → 跳到 Phase 3（Plan）
- 两者都没有 → 从 Phase 2（Design）开始

**End this skill here for continuation — the orchestrator handles routing.**

完成后：将 phases.md 中 `1a. 检查现有任务` 标记为 `[x]`（见 phases.md Sync）。

### 1b. Parse `$ARGUMENTS`

| Pattern | Type | Action |
|---|---|---|
| 参数开头匹配 `(full\|standard\|lite\|hotfix)` 关键词，或含 `--tier <preset>` | Tier argument | 暂存档位值，从参数中移除该关键词后继续解析剩余部分。示例：`/task lite 修复拼写` → tier=lite, desc="修复拼写" |
| 包含 `<issue identifier="...">` | Linear prompt | 解析 XML 提取 issue 元数据，暂存 issue ID 供 P1.phase-end hook 使用。 |
| 匹配 `[A-Z]+-\d+` | Issue ID | 暂存 issue ID 供 P1.phase-end hook 使用。 |
| 自然语言或为空 | Free description | Linear issue 创建在 1e 中是可选的。 |

### 1b.1 Requirement Confirmation (mandatory for ALL input types)

<rule>
Step 1b.1 仅确认需求，不做代码探索、文件分析或方案讨论。探索和分析属于 Phase 2 (Design) 的 Step 1 职责。不得在此步骤派发 Explore subagent。
Reason: Init 阶段过重的探索会污染上下文，且在需求未对齐前的探索是浪费。
</rule>

**目的：完善 prompt，而非诊断问题。** 此步骤只确保双方就用户的诉求达成一致。

解析输入后：

1. 若有歧义维度，先用 AskUserQuestion 提出澄清问题
2. 等待用户回答
3. 展示最终结构化理解：
   - **Goal**: 需要实现什么
   - **Scope**: 用户当前认为受影响的范围
   - **Symptoms**: 用户观察到了什么（如果是 bug）
   - **Suspected cause**: 用户的假设（如果提到了）
   - **Expected result**: 成功是什么样的
4. 纯文本询问："以上理解是否准确？有需要修改的地方吗？"
5. 用户说"继续" → 推进到 1b.2
6. 用户提出建议 → 澄清 → 修复 → 重新展示理解 → 回到步骤 4

确认后将结构化结果暂存内存（prompt.md 在 1f 中写入文件）。

完成后：将 phases.md 中 `1b. 解析参数 + 需求确认` 标记为 `[x]`。

### 1b.2 Prompt Quality Analysis

**目的：用结构化维度评估 prompt 质量，在设计阶段之前暴露问题。**

对用户的需求按以下 7 维度进行快速评估（不需要探索代码，基于 prompt 本身判断）：

| 维度 | 检查项 | 问题信号 |
|------|--------|---------|
| **清晰度** | 需求是否具体、可执行？ | "优化性能"等无量化目标的描述 |
| **可验证性** | 能否判断"做完了"？ | 无验收标准或仅有主观标准 |
| **完整性** | 信息是否足够开始设计？ | 缺少技术栈、入口、依赖等关键上下文 |
| **项目匹配度** | 需求是否与当前 repo 匹配？ | 要求的技术栈/功能与项目不一致 |
| **外部依赖** | 是否需要外部资源？ | 依赖 API Key、外部服务、特定硬件 |
| **歧义度** | 是否有多种合理理解？ | "适当处理"、"合理的"等模糊用语 |
| **范围界定** | 边界是否清晰？ | "相关功能也要改"等开放式范围 |

**输出格式（内联在结构化确认之后）：**

```
### Prompt 健康度

| 维度 | 评估 | 说明 |
|------|------|------|
| 清晰度 | ✅ / ⚠️ / ❌ | 一句话说明 |
| ... | ... | ... |

{如有 ⚠️ 或 ❌ 项，在 Step 2 的澄清问题中优先覆盖}
```

如果出现 2+ 个 ❌，向用户建议重新描述需求后再继续。

**注意：** 此分析基于 prompt 本身，不引入环境限制（如"能否在 Linux 运行"）。环境问题在 Phase 2 探索阶段处理。

完成后：将 phases.md 中 `1b.2 Prompt 质量分析` 标记为 `[x]`（在内存中）。

### 1b.3 Tier Pre-Selection

**目的：在需求确认后立即确定任务档位，写入 task-config.json，使后续所有步骤可读取配置。**

**1. 检查暂存档位：**
- 若 Step 1b 已解析出 tier 参数（如 `/task lite ...`）→ 直接使用该档位，跳到第 5 步

**2. 自动推荐 preset（无暂存档位时）：**

| 信号 | 推荐档位 |
|------|---------|
| Linear issue 含 `hotfix`/`urgent`/`bug` 标签 | Hotfix |
| Prompt 质量全 ✅ + 预计修改文件 ≤ 2 | Lite |
| 复杂度 Medium | Standard |
| 复杂度 High 或含架构关键词 | Full |
| 以上均不匹配 | task-defaults.json 的 preset 字段（默认 standard） |

**3. 读取 manifest 建议规则：**
遍历 `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.manifest.json`，读取每个插件的 `recommend_disable_when` 和 `recommend_enable_when` 字段。对比任务描述（prompt.md 的结构化需求），生成逐插件的裁剪建议。例如：
- 任务是纯 SKILL.md 修改 → tdd 的 `recommend_disable_when` 匹配 → 建议关闭 TDD
- 任务涉及核心业务逻辑 → tdd 的 `recommend_enable_when` 匹配 → 建议开启 TDD（即使 preset 未启用）

**4. 展示推荐（AskUserQuestion）：**
展示推荐的 preset + 裁剪建议，选项：推荐的 preset（Recommended）/ 其他 3 个 preset / 自定义。
裁剪建议附在推荐理由中，用户可采纳或忽略。

**5. 解析 effective config（三层合并，内存）：**

运行三层配置解析器（默认模板 ① < 全局用户 local ② < 项目本地 ③ < 调用 flag ④）：

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
hat-task-config-resolve --preset {chosen-preset} --project-root "$ROOT" \
  [quiet_mode 为真时追加 --quiet] [有 flag overrides 时追加 --flags '<json>']
```

- `{chosen-preset}` = 第 1-4 步选定的档位。`--quiet` 与 `--flags` 取自编排器 Step 1 的双信号判定与 flag 解析（quiet_mode、flag_overrides 在当前上下文可用）；独立调用时按编排器 Step 1 同一规则自行判定。
- 脚本输出 = 合并后的 effective config：已叠加 ②③④ 层、已按 quiet_mode 解析 `branch.worktree` 的 `"ask"` 哨兵（quiet→`true`；交互→保持 `"ask"`，待 1d 询问）。脚本**不解析** `"auto"` 值，保留供下面解析。
- 在脚本输出基础上**应用裁剪覆盖**（用户在第 4 步确认的逐插件禁用/启用调整）。
- **解析所有 `"auto"` 值为具体值**：`linear.enabled: "auto"` → 检测 Linear MCP 可用性解析为 `true`/`false`；`git.enabled: "auto"` → 检测 git 仓库解析为 `true`/`false`（`execution.engine: "auto"` 等保持运行时解析）。
- **`observability` 是顶层核心键**（与 `todo_sync`/`phase_merge` 同级，**不在 `plugins.*` 下**——ISSUE 下沉为核心能力）。脚本已正确合并顶层 `observability`——`hotfix` 的顶层 `observability.enabled: false` 经合并解析为 `false`（脚本从模板顶层而非 `plugins.*` 取该键）。
- 新顶层段 `branch` / `headless` / `end_decisions` 一并进入 effective config，随 1f 写入 task-config.json。
- 档位与配置在内存确定；`task-config.json` 的实际写盘移到 1f（任务文件夹创建之后），此处不写文件。

**6. 计算 phases.md 步骤列表（内存）：**
按已决定的 config 在内存计算步骤列表（不写盘，实际写入在 1f）：
- 读取 `phase_merge` 决定哪些 Phase 合并为一节（如 `[[3,4]]` → "Phase 3+4: Plan + Execute"）
- 读取各 `plugins.*.enabled` 决定哪些插件相关步骤出现在列表中（如 tdd disabled → P4 不含 TDD 步骤）
- 已完成的 P1 步骤（1a-1b.3）标记为 `[x]`

**[Unattended]** 按推荐自动选择，不弹 AskUserQuestion。

完成后：将 `1b.3 档位粗选` 标记为已完成（内存，因为 phases.md 尚未写盘——在 1f 写入）。

> **档位建议（分析/元任务拆独立 session）**：若任务含**大体量只读分析/复盘**（dogfooding、deep-research、审计、reading-triage 等），分析阶段宜**独立 session 运行**。原因：大段只读分析会显著推高单 phase token（dogfooding 实证 P2 曾达 38%）、污染主上下文。此为轻量 guidance，不强制、不引入自动检测：识别到此类任务时提示用户分析阶段另开 session 即可。

> **P1 hook 时序**：本阶段全部文件系统写（task-config.json / phases.md / prompt.md）、P1 hook（`P1.phase-start` → `P1.phase-end`）与内联 timing（phase_start/phase_end P1 经 `hat-timing-stamp`）统一在 1f 任务文件夹创建之后运行。`hat-plugin-hook {task-folder} ...` 必须有已存在的 `{task-folder}` 才能解析，故 1b.3 与 1c/1d 阶段不调用任何 P1 hook 或 timing。

### 1b.4 Debt Linkage Check (Lightweight)

读取 `docs/debt.md`（不存在则跳过），按 **issue-id + 文件路径重叠 + 关键词** 筛出与本任务范围相关的 **open（`- [ ]`）** 条目，简要带入上下文供 Design 参考（"本任务可能顺带解决/触及这些已知债务"）。

- 只筛**相关**项，不全量塞入（debt 可能很长）。无相关项 → 静默跳过。
- 这是**轻量上下文带入，非强制 scope**——不强迫本任务修旧债；是否纳入由 Design 阶段决定。
- 与 task-end Step 1.5 的「debt 对账」形成 init→end 闭环：Init 带出相关项，End 核对本任务是否解决了它们。

完成后将此步标记为已完成（内存；phases.md 无独立行，随 1f 写入）。

### 1c. Git Conventions + Working Directory

> **git plugin 启用时**：git 规范检测可在本步骤运行（不依赖任务文件夹）；dirty file 检查与处理（**Interactive** 选项 stash/commit/继续；**Unattended** 忽略继续）由 `P1.phase-start` hook 中 git plugin 承载，该 hook 在 1f 文件夹创建之后运行。git dirty check 时机仍在任何 task commit 之前，正确性不受影响。
> **git plugin 关闭时**：跳过本步骤。

（NO_GIT 模式下跳过）

- 运行 `hat-git-conventions .` — 如果没有找到规范，AskUserQuestion：**Define now** / **Use implicit conventions** / **Use default Conventional Commits** / **Skip**

完成后：将 `1c. Git 规范 + 工作目录` 标记为已完成（内存，phases.md 在 1f 写入）。

### 1d. Branch Decision

（NO_GIT 模式下跳过，直接在 CWD 下创建文件夹）

从 effective config（1b.3 第 5 步）读取 `branch.mode`（`keep`/`new`，默认 `keep`）与 `branch.name`（`null` = 按任务文件夹名自动生成分支名）。

<rule>
In Interactive mode you MUST use AskUserQuestion before creating any branch; never create one automatically. In quiet/unattended mode this Iron Law is lifted — resolve from `branch.mode` in the effective config without asking (default `keep` = stay on the current branch).
Reason: an interactive user may want a specific branching strategy, but an unattended run has no one to answer, so it must resolve deterministically from config. The default `keep` lets several tasks run in the same directory and collaborate on one working tree.
</rule>

**[Interactive]** AskUserQuestion：**留在当前分支（Recommended）** / **创建新分支**（推荐项对齐 config `branch.mode`，默认 keep）。
**[Unattended / quiet]** 不询问，按 `branch.mode` 自动决定（默认 `keep` = 留在当前分支）。

执行所选：`keep` → 留在当前分支；`new` → `git checkout -b {branch.name 或自动生成的任务名}`。git plugin 关闭时跳过分支创建。

> **worktree 隔离（`branch.worktree`）**：worktree 物理隔离与「交互模式在此追加 worktree 询问」由 Worktree Isolation 段承载（见下方 `### 1d-wt. Worktree Isolation`）。`branch.worktree` 取值已在 1b.3 第 5 步按模式解析（quiet→`true`、交互→`"ask"` 待此处询问、显式 true/false 直接生效）。

> **选「创建新分支」前的分叉告警（ISSUE，非阻塞）**：创建前比对 `git merge-base HEAD main` 与 `git rev-parse main`——若 `main` 有 HEAD 未含的 commit（当前 HEAD 落后 main、新分支 base 过旧）→ **非阻塞告警**：**[Interactive]** 纯提示「当前 HEAD 落后 main，新分支将基于较旧基线，建议先 rebase/merge main」后继续（**不加停止点、不阻塞**）；**[Unattended]** 记录该告警后继续。`NO_GIT` / git plugin 关闭时跳过本检查。

任务文件夹名格式：`YYYY-MM-DD-kebab-description`（10-20 字符的 kebab-case 描述）。存入内存——do NOT create directory yet.

完成后：将 phases.md 中 `1d. 分支决策` 标记为 `[x]`（在内存中，因为 phases.md 还未创建）。

### 1d-wt. Worktree Isolation

（NO_GIT / git plugin 关闭时跳过——worktree 依赖 git。）

读取 effective config `branch.worktree`（已在 1b.3 第 5 步解析：quiet 模式已定为 true/false；交互模式可能残留 `"ask"`）。

**决定是否隔离：**

| `branch.worktree` 值 | 处理 |
|---|---|
| `true` | 启用 worktree 隔离（见下方物理创建） |
| `false` | 不隔离，留在当前工作树（按 1d 的分支决策） |
| `"ask"`（仅交互模式残留） | **[Interactive]** AskUserQuestion 追加询问：**不隔离（Recommended，默认）** / **启用 worktree 隔离**；选不隔离→false、选启用→true。**[Unattended]** 不会到此分支（quiet 已解析为 true/false） |

**启用 worktree 时的物理创建**（worktree 必挂 task 专用分支、主目录 HEAD 不动，隔离落在 worktree 内）：

1. 记主仓库根与目标：`MAIN_ROOT="$(git rev-parse --show-toplevel)"`；`WT="$MAIN_ROOT/.claude/worktrees/{task-folder-name}"`；分支名 `task/{task-folder-name}`（config `branch.name` 非 null 时用之）。
2. 基于当前 HEAD 创建并注册 worktree（不动主目录工作树/HEAD）：
   ```bash
   git worktree add -b "task/{task-folder-name}" "$WT" HEAD
   ```
3. 切入 worktree（`path` 进入已注册 worktree → session CWD 随之切换，`.tasks/` 天然隔离在 worktree 内）：
   `EnterWorktree(path="$WT")`
4. 将 `MAIN_ROOT` 与 `WT` 暂存内存，供 1f 写主仓库指针 stub。

> **与 1d 分支决策的关系**：启用 worktree 时 task 专用分支已由本步 `git worktree add -b` 创建，**1d 不再在主目录 `git checkout -b`**（主目录 HEAD 保持不动）。`branch.mode==new` 的语义由 worktree 专用分支取代；`branch.mode==keep` 时 worktree 仍建独立 task 分支（隔离需要）——主目录始终不动。

<rule>
Creating a worktree must never move the main directory's HEAD. Use `git worktree add -b <branch> <path> HEAD` to make a new branch in a separate working tree — never `git checkout -b` in the main directory when worktree is enabled.
Reason: the point of worktree isolation is that other tasks sharing the main directory keep working on their own branch. Moving the main HEAD would break same-directory multi-task collaboration, which is exactly what `branch.worktree:false` exists to preserve.
</rule>

完成后：将 `1d-wt. Worktree 隔离` 标记为已完成（内存）。

### 1e. Linear Context

> **由 `P1.phase-end` hook 中 linear plugin 执行。** 本步骤仅保留触发入口。

Linear issue 创建/关联和状态更新由 `P1.phase-end` hook 处理。若 linear plugin 关闭，跳过本步骤。

若步骤 1b 已解析 Linear 信息（issue ID 或 XML），暂存到内存供 hook 使用。

完成后：将 `1e. Linear 上下文` 标记为已完成（内存）。

### 1f. Create Task Folder + prompt.md

所有文件系统写操作在此进行，在分支设置完成**之后**。

```bash
echo '<json>' | hat-task-scaffold ".tasks/open/YYYY-MM-DD-topic" --linear-stdin
```

备选方案：`mkdir -p .tasks/open/YYYY-MM-DD-topic/` + 手动写入 `linear.json`。

**写入 task-config.json：** 将 1b.3 第 5 步在内存确定的档位配置写入 `{task-folder}/task-config.json`（文件夹已创建）。**[Quiet]** quiet_mode=true 时，在写入的对象顶层追加 `"_source": "headless"`（标记本 config 由无头入口物化，供 task-design Step 2e 短路判定）。

**[Quiet] 物化 unattended.json（仅 quiet_mode=true 的新任务）：**

quiet_mode 经 Step 0 确立时，在此直接物化无人值守状态文件，使 Init 之后全程无需人工激活（不再等 Step 2A.1 询问）：

```json
{
  "enabled": true,
  "activate_after": "now",
  "task_type": "self_test",
  "telegram_chat_id": "{detected_chat_id_or_null}",
  "triggered_at": "{ISO_timestamp}",
  "degrade_policy": "{effective config 的 headless.degrade_policy，或 Step 0 flag 映射值；缺省 conservative}",
  "end_decisions": {
    "branch": "{effective config 的 end_decisions.branch，默认 keep}",
    "claude_md": "{effective config 的 end_decisions.claude_md，默认 auto_update}"
  }
}
```

- `telegram_chat_id` 按 `UNATTENDED_PROTOCOL.md` §3 探测（无则 null，通知静默降级）。
- `task_type` 缺省 `self_test`（无头自测推进到 task-end）；若 flag/config 指明需用户测试则 `user_test`。
- 写入后本阶段后续停顿点即按无人值守自动决策。`unattended.json` 已存在（恢复场景）则不覆盖。
- **非 quiet 模式**：不写 unattended.json（保持原交互流程，激活时机由 Step 2A.1 / task-design Activation Timing 询问）。

**[Worktree] 写主仓库指针 stub（仅 1d-wt 启用 worktree 时）：** 此刻 CWD 已在 worktree 内，task 文件写在 worktree 的 `.tasks/open/{task-folder}/`（天然隔离）。为支持跨 session 从主仓库恢复，在**主仓库**留一个 stub 指针（经绝对路径 `$MAIN_ROOT`，不受 CWD 切换影响）：

```bash
mkdir -p "$MAIN_ROOT/.tasks/open/{task-folder-name}"
printf '%s\n' "$WT" > "$MAIN_ROOT/.tasks/open/{task-folder-name}/.worktree"
```

主仓库 stub 仅含 `.worktree` 指针（`hat-task-detect` 读出 `worktree` 字段，编排器据此回切，见 task/SKILL.md Step 2B）；真实任务文件全在 worktree 内。

**写入 session.json：** 写 `{task-folder}/session.json` = `{"sessions": ["$CLAUDE_CODE_SESSION_ID"]}`（数组形态，schema 见下），用于精确定位本任务的会话导出（修复 dogfooding 分析「抓最新 jsonl」导致的串任务）。`CLAUDE_CODE_SESSION_ID` 环境变量缺失时跳过写入（graceful）——此时 `/dogfooding` / 导出将回退到名匹配并标注「会话来源未经确认」。

```bash
[ -n "${CLAUDE_CODE_SESSION_ID:-}" ] && printf '{"sessions": ["%s"]}\n' "$CLAUDE_CODE_SESSION_ID" > "{task-folder}/session.json"
```

> **session.json schema（跨 session 追加）**：`{"sessions": ["<id1>", "<id2>", ...]}`。task-init 写入首个；编排器 Step 2B 在跨 session 恢复时把新 session-id 追加进数组（见 task/SKILL.md）。消费者：`hat-conversation-export` wrapper、`/dogfooding`、task-end 导出。

**写入 prompt.md：**

```markdown
## Original Prompt
[用户的原始输入，逐字照录]

## Structured Requirement
- **Goal**: ...
- **Scope**: ...
- **Symptoms**: ...
- **Suspected Cause**: ...
- **Expected Result**: ...

## Issues with Original Prompt
[列出具体问题]

## Suggestions
[如何把 prompt 写得更好]
```

**Checkpoint: 确认 Linear issue 已创建**。检查 `linear.json` 是否存在且包含有效 `issueUuid`。
- 成功 → 继续
- 失败 → AskUserQuestion：**重试** / **跳过 Linear 集成**

**写入 phases.md**（在任务文件夹中）：

将 1b.3 第 6 步在内存计算出的步骤列表（含 phase_merge 合并和插件裁剪）写入 `{task-folder}/phases.md`：1a-1e 标记为 `[x]`、1f 标记为 `[x]`，Phase 2-6 所有步骤保持 `[ ]`、Status 为 PENDING。

若 1b.3 被跳过的边界情况（无内存步骤列表），按 task/SKILL.md 的 `phases.md Format Reference` 默认模板创建。

**记录 P1 起始时间戳（core timing，内联）**：

任务文件夹创建完成后（task-config.json + phases.md 已写盘），**先**内联记录 phase_start（须在本 phase 任何 `hat-plugin-hook` 调用之前；helper 自带顶层 `observability.enabled` 门控，关闭档如 hotfix → no-op）：

```bash
hat-timing-stamp {task-folder} phase_start P1
```

**P1.phase-start Hook**：

接着运行：

```bash
hat-plugin-hook {task-folder} P1.phase-start
```

按输出指令执行（git plugin: dirty file 检查与处理——Interactive 选项 stash/commit/继续，Unattended 忽略继续）。git 规范检测已在 1c 完成，hook 此处不重复检测。如输出为空（插件未启用），跳过。git dirty check 在此运行仍早于任何 task commit。

### Session Name Alignment

<rule>
After the task folder is created, prompt the user to run `/rename <task-folder-name>` to align the session name.
Reason: without a manual /rename, the session name stays as the default, making it hard to identify the session in the session switcher later.
</rule>

任务文件夹创建完成后，提示用户：

> 任务文件夹已创建：`{task-folder-name}`。请手动执行一次 `/rename {task-folder-name}`（例：`/rename 2026-05-25-auth-refactor`）以对齐 session 名称，便于后续在 session 切换器中识别。

**[Unattended]** 无人值守模式下自动跳过此提示，不停顿，不执行 `/rename`。

---

## phases.md Sync

每个步骤完成后，写入 `{task-folder}/phases.md` 更新：
- 找到对应步骤，将 `[ ]` 改为 `[x]`
- 更新 `**Updated**: YYYY-MM-DD HH:MM`

**Phase 1 完成时**：将 Phase 1 的 `**Status**: PENDING` 改为 `**Status**: DONE`。

---

### P1.phase-end Hook

1f 完成后，先内联记录 P1 phase_end 时间戳（core timing，须在 hook 调用之前），再运行 linear hook：

```bash
hat-timing-stamp {task-folder} phase_end P1
hat-plugin-hook {task-folder} P1.phase-end
```

hook 输出按段全部执行（linear plugin: issue 创建/状态更新）。

<rule>
内联 timing 调用（`hat-timing-stamp ... phase_start/phase_end P1`）须排在本 phase 任何 `hat-plugin-hook` 调用之前。helper 自带 `observability.enabled` 门控（关闭档如 hotfix → no-op，不写、不报错）。
Reason: timing 内联后是确定动作（不再是 hook 多段文本指令中易被漏执行的一段）；但缺 phase_start 会触发 artifact-check 硬 FAIL，故内联点必须前置、先于可能 blocking 的 plugin 段执行。
</rule>

---

## Init 完成 → 过渡

Phase 1 完成，phases.md 中 Phase 1 Status 已标记为 DONE。

用用户配置的语言简要宣告初始化结果（分支、任务文件夹、Linear 状态），然后声明：**"Init 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
Phase skill 完成后必须返回编排器 Step 3。不得在 transition section 中提示用户调用任何其他 skill。过渡路由是编排器的职责。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、compact、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask | Unattended |
|------|------|-------------|-----------|
| 1a | 发现现有任务 | 继续现有 / 创建新任务 | 继续现有任务（对齐编排器单任务恢复） |
| 1b.3 | 档位推荐 | 确认 preset 和裁剪建议 | 按推荐自动选择 |
| 1c | Git 规范不存在 | 定义方式选择 | 自动使用 Conventional Commits |
| 1f（P1.phase-start hook） | 发现 dirty 文件 | 处理方式（stash/commit/继续） | 忽略继续 |
| 1d | 分支决策 | 必须询问（Interactive） | 按 `branch.mode` 自动决定（默认 keep = 留在当前分支） |
| 1d-wt | worktree 隔离（`branch.worktree=="ask"`） | 追加询问是否启用（默认否） | 按解析值自动（quiet 缺省 true；显式 true/false 直接生效） |
| 1e | 有 Linear 配置 | 是否创建 issue | 自动创建；失败则跳过 |
| 1f | Linear issue 创建失败 | 重试 / 跳过 | 自动跳过 |
| post-1f | 任务文件夹已创建 | 提示执行 `/rename <task-folder-name>` 对齐 session 名 | **[Unattended] 自动跳过，不执行 /rename** |

## Dependencies

- **Scripts**: hat-task-detect, hat-task-scaffold, hat-git-conventions, hat-plugin-hook, hat-timing-stamp, hat-task-config-resolve（三层配置合并）
- **Writes**: `{task-folder}/phases.md`, `{task-folder}/prompt.md`, `{task-folder}/linear.json`, `{task-folder}/task-config.json`, `{task-folder}/session.json`, `{task-folder}/unattended.json`（仅 quiet_mode 物化）
- **Reads（三层配置）**: `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`（①默认模板）, `~/.claude/task-defaults.local.json`（②全局用户 local，可选）, `{project-root}/task-defaults.json`（③项目本地，可选）
- **Worktree（仅 1d-wt 启用时）**: `git worktree add -b task/<folder> <path> HEAD`（创建专用分支隔离工作树，主目录 HEAD 不动）+ 内置 `EnterWorktree(path=...)` 切入；主仓库写 stub 指针 `$MAIN_ROOT/.tasks/open/<folder>/.worktree`
- **Hooks**（均在 1f 任务文件夹创建之后运行，依次）: `P1.phase-start`（git: dirty check + 处理[Interactive stash/commit/继续 · Unattended 忽略继续] + 规范确认）→ `P1.phase-end`（linear: issue setup）
- **Core timing**（内联，非 hook）: phase_start P1（1f 文件夹创建后、P1.phase-start hook 之前）/ phase_end P1（1f 完成后、P1.phase-end hook 之前）经 `hat-timing-stamp`，受顶层 `observability.enabled` 门控
