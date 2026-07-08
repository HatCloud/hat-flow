---
name: task-init
user-invocable: false
self-evolving: inbox
description: "Use when initializing a new task (Phase 1). Can be called standalone or via /task orchestrator. Do NOT use to resume an existing task (orchestrator routes that). 触发词: \"初始化任务\", \"task init\", \"开始初始化\""
word-budget: 2000
---

# Task Init — Phase 1: Setup

任务初始化阶段：解析用户输入、确认需求、设置 git 分支、创建任务文件夹、处理 Linear 集成，生成 `phases.md`（跨 session 恢复的状态文件）。

工具落点按 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/harness-tools.md` 映射。

**Announce at start:** "Using task-init for Phase 1: Setup."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Dirty: !`git status --porcelain 2>/dev/null | head -5`
- User input: $ARGUMENTS

> 若上方任一探测/注入行未展开（显示字面 `!` 前缀原文），先当场执行该命令 / Read 该文件取结果，再继续。

## NO_GIT Mode

如果 Branch 值为 `NO_GIT`，跳过以下步骤：1c（Git 规范 + Dirty 检查）、1d（分支决策，直接在 CWD 下创建任务文件夹）、1d-wt（Worktree 隔离，依赖 git）及一切 git commit。其余步骤正常执行。

---

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**1f 末**（建 overview / P1 step，按档动作见触发点表）；后续步骤完成同步 phases.md（`full` 另 `维护进度清单，状态置 `completed``）。

---

## Resume Support

**如果由 `/task` 编排器调用** 且已有 `phases.md`：在每个步骤开始前检查 phases.md 中对应步骤是否已标记 `[x]`。如果是，跳过该步骤，继续下一步。

**phases.md 中步骤名称对应：**
- `1a. 检查现有任务` → 步骤 1a
- `1b. 解析参数 + 需求确认` → 步骤 1b + 1b.1
- `1b.2 Prompt 质量分析` → 步骤 1b.2
- `1b.2b 头脑风暴补完` → 步骤 1b.2b
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

> 无人值守的激活入口与契约（quiet→本 skill 1f 物化 / 交互主入口→编排器 Step 2A.1 / standalone 后备→task-design Step 2e；activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 只读取已有状态。

---

### 1a. Check Existing Tasks

从 Runtime Context 读取 Tasks JSON。

**若 `open` 数组非空：**

使用 向用户提问（结构化选项优先） 列出现有任务。选项：**继续现有任务** / **创建新任务**

如果选择继续，按状态路由（与编排器「phases.md 不存在」fallback 判据同表）：
- 有 `phases.md` → 由 `/task` 编排器处理路由
- 有 `plan.md`：含未勾选项 → Phase 4（Execution）；全部勾选 → Phase 5（Test，执行已完成）
- 有 `design.md` 无 `plan.md` → Phase 3（Plan）
- 两者都没有 → 从 Phase 2（Design）开始

继续现有任务时本 skill 在此结束，由编排器接管。

### 1b. Parse `$ARGUMENTS`

| Pattern | Type | Action |
|---|---|---|
| 参数开头匹配 `(full\|standard\|lite\|hotfix)` 关键词，或含 `--tier <preset>` | Tier argument | 暂存档位值，从参数中移除该关键词后继续解析剩余部分。示例：`/task lite 修复拼写` → tier=lite, desc="修复拼写" |
| 包含 `<issue identifier="...">` | Linear prompt | 解析 XML 提取 issue 元数据，暂存 issue ID 供 P1.phase-end hook 使用。 |
| 匹配 `[A-Z]+-\d+` | Issue ID | 暂存 issue ID 供 P1.phase-end hook 使用。 |
| 自然语言或为空 | Free description | Linear issue 创建在 1e 可选。 |

### 1b.1 Requirement Confirmation（所有输入类型必经）

<rule>
Step 1b.1 仅确认需求；代码探索、文件分析、方案讨论与 Explore subagent 派发均属 Phase 2 (Design) Step 1 的职责，不在本步骤范围内。
Reason: Init 阶段过重的探索会污染上下文，且在需求未对齐前的探索是浪费。
</rule>

**目的：完善 prompt，而非诊断问题。** 此步骤只确保双方就用户的诉求达成一致。

解析输入后：

1. 若有歧义维度，先用 向用户提问（结构化选项优先） 提出澄清问题，等用户回答
2. 展示最终结构化理解：**Goal**（要实现什么）/ **Scope**（受影响范围）/ **Symptoms**（观察到什么，bug 时）/ **Suspected cause**（用户假设，若提及）/ **Expected result**（成功的样子）
3. 纯文本询问："以上理解是否准确？有需要修改的地方吗？"
4. 用户说"继续" → 推进到 1b.2；用户提出建议 → 澄清 → 修复 → 重新展示理解 → 回到步骤 3

**[Unattended/quiet]** quiet_mode（编排器 Step 0 确立，**早于** 1f 物化 unattended.json，故此处按 quiet_mode 判定、不依赖文件存在）下不调 向用户提问（结构化选项优先），跳过纯文本确认：歧义维度按 prompt 最保守、最小范围的解释自行假设，逐条记入 `{task-folder}/unattended-decisions.md`（文件夹未建则暂存内存、1f 落盘），以假设的结构化理解直接推进 1b.2；关键歧义（影响方向、无法从 prompt 推导）→ 按 `UNATTENDED_PROTOCOL.md` §8「低置信澄清问题」暂停 + Telegram，等 `/task` 恢复。

确认后将结构化结果暂存内存（prompt.md 在 1f 中写入文件）。

### 1b.2 Prompt Quality Analysis

**目的：用结构化维度评估 prompt 质量，在设计阶段之前暴露问题。**

按以下 7 维度快速评估需求（不探索代码，基于 prompt 本身判断）：

| 维度 | 检查项 | 问题信号 |
|------|--------|---------|
| **清晰度** | 需求是否具体、可执行？ | "优化性能"等无量化目标的描述 |
| **可验证性** | 能否判断"做完了"？ | 无验收标准或仅有主观标准 |
| **完整性** | 信息是否足够开始设计？ | 缺少技术栈、入口、依赖等关键上下文 |
| **项目匹配度** | 需求是否与当前 repo 匹配？ | 要求的技术栈/功能与项目不一致 |
| **外部依赖** | 是否需要外部资源？ | 依赖 API Key、外部服务、特定硬件 |
| **歧义度** | 是否有多种合理理解？ | "适当处理"、"合理的"等模糊用语 |
| **范围界定** | 边界是否清晰？ | "相关功能也要改"等开放式范围 |
| **模型能力** | 任务是否包含调研/报告子任务且将由较弱模型生成？ | 有 report/research/调研 子任务（Design 阶段再规划事实核查步骤） |

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

**模型能力维度 ⚠️ 触发规则**：若"模型能力"评为 ⚠️，在"Suggestions"段加入：
> Design 阶段在 Acceptance Tests 中加入"报告核心事实核查"项：手动核对报告关键数值、引用代码路径与实际代码/配置的一致性，执行阶段由实现者对照代码验证。人工提示，不自动执行。

**注意：** 此分析基于 prompt 本身，不引入环境限制；环境问题在 Phase 2 探索阶段处理。

### 1b.2b 头脑风暴补完

**目的：低分或用户主动时，经头脑风暴把模糊 / 初级需求扩充为详尽需求，再进档位选择。** 本步是**恒执行的门控评估步**——每次都评估门控、记录结果，phases.md 正常 `[ ]→[x]`，不引入第三态。

**触发判据（沿用 1b.2 现有门槛）**：1b.2 评为"低分" = `2+ ❌` 或 `❌/⚠️ 合计 ≥3`；或用户主动表达"想头脑风暴 / 完善需求"。原"2+ ❌ → 建议重新描述"出口升级为"建议头脑风暴"。

- **[Interactive]** 低分 → 向用户提问（结构化选项优先）：**进入头脑风暴** / **跳过继续**；非低分不打扰，门控记"未进入"直接完成。
- **[Unattended/quiet]** 低分默认进入（不询问，记 `unattended-decisions.md`）；非低分跳过。

**进入分支**：存内存态结构化需求快照 → `Read ${CLAUDE_PLUGIN_ROOT}/skills/brainstorm/SKILL.md` inline 执行 → 收敛时 brainstorm 原子替换内存态 Structured Requirement + 追加内存态 `## Brainstorm Results`（prompt.md 仍由 1f 落盘）→ **重跑 1b.2 评分**（基于扩充后需求）→ 标 `[x]`。**未进入 / 中途退出**：门控评估完成即标 `[x]`（结果记"未进入"或"中途退出"），不重入 brainstorm，直接进 1b.3。

### 1b.3 Tier Pre-Selection

**目的：需求确认后立即确定任务档位，写入 task-config.json 供后续步骤读取。**

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
遍历 `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.md`，读取每个插件 frontmatter 的 `recommend_disable_when` / `recommend_enable_when` 字段，对比任务描述（prompt.md 结构化需求）生成逐插件裁剪建议（如纯 SKILL.md 修改 → 匹配 tdd `recommend_disable_when` → 建议关闭 TDD；涉核心业务逻辑 → 匹配 `recommend_enable_when` → 建议开启，即使 preset 未启用）。

**4. 展示推荐（向用户提问（结构化选项优先））：**
展示推荐的 preset + 裁剪建议，选项：推荐 preset（Recommended）/ 其他 3 个 preset / 自定义。裁剪建议附在推荐理由中，用户可采纳或忽略。

**5. 解析 effective config（内存，三层合并：默认模板 ① < 全局用户 local ② < 项目本地 ③ < 调用 flag ④）：**

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
hat-task-config-resolve --preset {chosen-preset} --project-root "$ROOT" \
  [quiet_mode 为真时追加 --quiet] [有 flag overrides 时追加 --flags '<json>']
```

- `{chosen-preset}` = 第 1-4 步选定的档位。`--quiet` 与 `--flags` 取自编排器 Step 1 的双信号判定与 flag 解析；独立调用时按编排器 Step 1 同一规则自行判定。
- 脚本输出 = 合并后的 effective config：已叠加 ②③④ 层、已按 quiet_mode 解析 `branch.worktree` 的 `"ask"` 哨兵（quiet→`true`；交互→保持 `"ask"` 待 1d 询问），但**不解析** `"auto"`。在此基础上**应用第 4 步确认的裁剪覆盖**，并**解析所有 `"auto"`**：`linear.enabled`/`git.enabled` 检测 MCP/仓库可用性解析为 `true`/`false`（`execution.engine: "auto"` 等保持运行时解析）。
- 新顶层段 `branch` / `headless` / `end_decisions` 一并进入 effective config。档位与配置在内存确定，`task-config.json` 实际写盘移到 1f，此处不写文件。
- **Codex capability 预检（首次门控）**：effective config `plugins.review.reviewer` 或 `execution.engine` ∈ {`codex`,`auto`} 时运行 `codex-check`，据结果锁定/保留 codex 选项，检测结果随 1f 写入 `task-config.json` 的 `capabilities.codex`。分支细节（FALLBACK/READY 处理、字段结构、二次检测归属）见 `references/notes.md`。

**6. 计算 phases.md 步骤列表（内存，不写盘，实际写入在 1f）：**
- `phase_merge` 决定哪些 Phase 合并为一节（如 `[[3,4]]` → "Phase 3+4: Plan + Execute"）
- 各 `plugins.*.enabled` 决定哪些插件步骤出现（如 tdd disabled → P4 不含 TDD 步骤）
- Phase 1 列表恒含 `1b.2b 头脑风暴补完`（1b.2 与 1b.3 之间，恒执行门控步、非插件裁剪项）
- 已完成的 P1 步骤（1a-1b.3，含 1b.2b）标记为 `[x]`

> **档位建议 + P1 hook 时序**：含大体量只读分析/复盘的任务宜把分析阶段拆独立 session（轻量 guidance）；本阶段全部文件系统写与 P1 hook 统一推迟到 1f 文件夹创建之后（`hat-plugin-hook` 需已存在的 `{task-folder}` 才能解析）。理由与实证见 `references/notes.md`。

### 1b.4 Debt Linkage Check (Lightweight)

读取 `docs/debt.md`（不存在则跳过），按 **issue-id + 文件路径重叠 + 关键词** 筛出与本任务范围相关的 **open（`- [ ]`）** 条目，简要带入上下文供 Design 参考。

- 只筛**相关**项、不全量塞入（debt 可能很长），无相关项静默跳过。这是**轻量上下文带入、非强制 scope**——是否纳入由 Design 决定。
- 与 task-end Step 1.5 的「debt 对账」形成 init→end 闭环：Init 带出相关项，End 核对是否解决。

### 1c. Git Conventions + Working Directory

> **git plugin 启用时**：git 规范检测在本步骤运行（不依赖任务文件夹）；dirty file 检查与处理（**Interactive** stash/commit/继续；**Unattended** 忽略继续）由 `P1.phase-start` hook 承载（1f 之后运行，仍早于任何 task commit）。**关闭时**跳过本步骤。

（NO_GIT 模式下跳过）

- 运行 `hat-git-conventions .` — 如果没有找到规范，向用户提问（结构化选项优先）：**Define now** / **Use implicit conventions** / **Use default Conventional Commits** / **Skip**

### 1d. Branch Decision

（NO_GIT 模式下跳过，直接在 CWD 下创建文件夹）

从 effective config（1b.3 第 5 步）读取 `branch.mode`（`keep`/`new`，默认 `keep`）与 `branch.name`（`null` = 按任务文件夹名自动生成分支名）。

<rule>
Interactive 模式下分支创建以 向用户提问（结构化选项优先） 为门控，不自动创建任何分支。Quiet/unattended 下门控解除，由 `branch.mode` 确定性决定、不询问（默认 `keep` = 留在当前分支）。
Reason: 交互用户可能想用特定分支策略，而无人值守无人作答，必须依 config 确定性解析。默认 `keep` 让多任务共用一棵工作树协作。
</rule>

**[Interactive]** 向用户提问（结构化选项优先）：**留在当前分支（Recommended）** / **创建新分支**（推荐项对齐 config `branch.mode`，默认 keep）。
**[Unattended / quiet]** 不询问，按 `branch.mode` 自动决定（默认 `keep` = 留在当前分支）。

执行所选：`keep` → 留在当前分支；`new` → `git checkout -b {branch.name 或自动生成的任务名}`。git plugin 关闭时跳过分支创建。

> **worktree 隔离（`branch.worktree`）**：物理隔离与交互追问由下方 `### 1d-wt. Worktree Isolation` 承载；取值已在 1b.3 第 5 步按模式解析。

> **选「创建新分支」前的分叉告警（ISSUE，非阻塞）**：创建前比对 `git merge-base HEAD main` 与 `git rev-parse main`——若 `main` 有 HEAD 未含的 commit → **[Interactive]** 纯提示「当前 HEAD 落后 main，新分支基线较旧，建议先 rebase/merge main」后继续（不加停止点、不阻塞）。`NO_GIT` / git plugin 关闭时跳过。

任务文件夹名格式：`YYYY-MM-DD-kebab-description`（10-20 字符的 kebab-case 描述）。存入内存——目录创建推迟到 1f。

### 1d-wt. Worktree Isolation

（NO_GIT / git plugin 关闭时跳过——worktree 依赖 git。）

读取 effective config `branch.worktree`（已在 1b.3 第 5 步解析：quiet 已定为 true/false；交互可能残留 `"ask"`）。**决定是否隔离：**

| `branch.worktree` 值 | 处理 |
|---|---|
| `true` | 启用 worktree 隔离（见下方物理创建） |
| `false` | 不隔离，留在当前工作树（按 1d 的分支决策） |
| `"ask"`（仅交互模式残留） | **[Interactive]** 向用户提问（结构化选项优先） 追加询问：**不隔离（Recommended，默认）** / **启用 worktree 隔离**；选不隔离→false、选启用→true |

**同树并发守卫（`"ask"` 分支的推荐翻转）**：询问前检查 Tasks JSON——若已有**其他 open task 共享当前工作树**（open 数组除本任务外非空且非 worktree stub），把推荐项翻转为**启用 worktree 隔离（Recommended）**，问题里点明「已有 N 个 open task 共享此树：commit 交错、共享文档归属串扰、P6 squash 守卫失真三类风险」。显式 `false` 配置不受此守卫覆盖。

**启用 worktree 时的物理创建**（worktree 挂 task 专用分支、主目录 HEAD 不动）：

1. 记主仓库根与目标：`MAIN_ROOT="$(git rev-parse --show-toplevel)"`；`WT="$MAIN_ROOT/.claude/worktrees/{task-folder-name}"`；分支名 `task/{task-folder-name}`（config `branch.name` 非 null 时用之）。
2. 确保主仓库忽略 worktree 目录（否则污染主树 `git status`、被 git plugin `git add -A` 误提交）；写本地 `.git/info/exclude`，不动 tracked 的 `.gitignore`：
   ```bash
   grep -qxF '.claude/worktrees/' "$MAIN_ROOT/.git/info/exclude" 2>/dev/null || printf '%s\n' '.claude/worktrees/' >> "$MAIN_ROOT/.git/info/exclude"
   ```
3. 基于当前 HEAD 创建并注册 worktree（不动主目录工作树/HEAD）：
   ```bash
   git worktree add -b "task/{task-folder-name}" "$WT" HEAD
   ```
4. 切入 worktree（`path` 进入已注册 worktree → session CWD 随之切换，`.tasks/` 天然隔离在 worktree 内）：
   `进入隔离工作树(path="$WT")`
5. 将 `MAIN_ROOT` 与 `WT` 暂存内存，供 1f 写主仓库指针 stub。

> **与 1d 分支决策的关系**：启用 worktree 时 task 专用分支已由本步 `git worktree add -b` 创建，**1d 不再在主目录 `git checkout -b`**。`branch.mode==new` 语义由 worktree 专用分支取代；`branch.mode==keep` 时 worktree 仍建独立 task 分支（隔离需要）——主目录 HEAD 始终不动。

<rule>
创建 worktree 时主目录的 HEAD 保持不动。新分支经 `git worktree add -b <branch> <path> HEAD` 在独立工作树中创建；启用 worktree 时，在主目录执行 `git checkout -b` 不在范围内。
Reason: worktree 隔离的意义在于让共享主目录的其它任务继续在各自分支上工作。移动主目录 HEAD 会破坏同目录多任务协作，而这正是 `branch.worktree:false` 所要保留的。
</rule>

### 1e. Linear Context

Linear issue 创建/关联和状态更新由 `P1.phase-end` hook 中 linear plugin 处理；plugin 关闭则跳过。若步骤 1b 已解析 Linear 信息（issue ID 或 XML），暂存到内存供 hook 使用。

### 1f. Create Task Folder + prompt.md

所有文件系统写操作在此进行，在分支设置完成**之后**。

```bash
echo '<json>' | hat-task-scaffold ".tasks/open/YYYY-MM-DD-topic" --linear-stdin
```

备选方案：`mkdir -p .tasks/open/YYYY-MM-DD-topic/` + 手动写入 `linear.json`。`hat-task-scaffold` 不支持 `--help`（会当路径建目录）；需探测用法时读源码。

**写入 task-config.json：** 将 1b.3 第 5 步在内存确定的档位配置写入 `{task-folder}/task-config.json`。**[Quiet]** quiet_mode=true 时顶层追加 `"_source": "headless"`（供 task-design Step 2e 短路判定）。若 1b.3 做过 Codex capability 预检，把内存中的 `capabilities.codex` 一并写入顶层。

**[Quiet] 物化 unattended.json（仅 quiet_mode=true 的新任务）：** 使 Init 之后全程无需人工激活（不再等 Step 2A.1 询问）：

```json
{
  "enabled": true,
  "activate_after": "now",
  "task_type": "self_test",
  "telegram_chat_id": "{detected_chat_id_or_null}",
  "triggered_at": "{ISO_timestamp}",
  "degrade_policy": "{config.headless.degrade_policy 或 Step 0 flag 映射；缺省 conservative}",
  "end_decisions": {
    "branch": "{config.end_decisions.branch，默认 keep}",
    "claude_md": "{config.end_decisions.claude_md，默认 auto_update}",
    "squash": "{config.end_decisions.squash，默认 true}"
  }
}
```

- `telegram_chat_id` 按 `UNATTENDED_PROTOCOL.md` §3 探测（无则 null，通知静默降级）。`task_type` 缺省 `self_test`（推进到 task-end）；flag/config 指明需用户测试则 `user_test`。
- 写入后本阶段后续停顿点即按无人值守自动决策；`unattended.json` 已存在（恢复场景）则不覆盖。
- **非 quiet 模式**：不写 unattended.json（保持原交互流程，激活时机由 task-design Step 2e 主问、编排器 Step 2A.1 后备）。

**[Worktree] 写主仓库指针 stub（仅 1d-wt 启用 worktree 时）：** 此刻 CWD 已在 worktree 内，真实任务文件写在 worktree 的 `.tasks/open/{task-folder}/`（天然隔离）。为支持跨 session 从主仓库恢复，在**主仓库**留一个仅含 `.worktree` 指针的 stub（经绝对路径 `$MAIN_ROOT`，`hat-task-detect` 读出 `worktree` 字段供编排器回切，见 task/SKILL.md Step 2B）：

```bash
mkdir -p "$MAIN_ROOT/.tasks/open/{task-folder-name}"
printf '%s\n' "$WT" > "$MAIN_ROOT/.tasks/open/{task-folder-name}/.worktree"
```

**写入 session.json：** 写 `{task-folder}/session.json`（`{"sessions": [...]}` 数组形态，写入模板见 harness-tools.md「会话标识」行），用于精确定位本任务的会话导出。会话标识缺失时跳过写入（graceful）。schema（跨 session 追加语义）、消费者清单与回退行为见 `references/notes.md`。

写入命令模板见 harness-tools.md「会话标识」行。

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
- 失败 → 向用户提问（结构化选项优先）：**重试** / **跳过 Linear 集成**

**写入 phases.md**（在任务文件夹中）：

将 1b.3 第 6 步在内存计算出的步骤列表（含 phase_merge 合并和插件裁剪）写入 `{task-folder}/phases.md`：1a-1e 标记为 `[x]`、1f 标记为 `[x]`，Phase 2-6 所有步骤保持 `[ ]`、Status 为 PENDING。

若 1b.3 被跳过的边界情况（无内存步骤列表），按 task/SKILL.md 的 `phases.md Format Reference` 默认模板创建。

**TODO 同步（1f 末触发锚）**：任务夹 + config + phases.md 已落盘、name/tier 已定，此处执行 `## TODO Sync` 声明的 **1f 末** 触发点（按档动作见上方 section + `references/todo-sync.md` 触发点表）。

**P1.phase-start Hook**：

任务文件夹创建完成后（task-config.json + phases.md 已写盘）运行：

```bash
hat-plugin-hook {task-folder} P1.phase-start
```

按输出指令执行（git plugin: dirty file 检查与处理——Interactive 选项 stash/commit/继续，Unattended 忽略继续）。git 规范检测已在 1c 完成，hook 此处不重复；dirty check 在此运行仍早于任何 task commit。输出为空（插件未启用）则跳过。

### Session Name Alignment

<rule>
任务文件夹创建完成后，提示用户执行 `/rename <task-folder-name>` 以对齐 session 名称。
Reason: 不手动执行 /rename，session 名会保持默认值，后续在 session 切换器中难以识别该 session。
</rule>

提示用户：

> 任务文件夹已创建：`{task-folder-name}`。请手动执行一次 `/rename {task-folder-name}`（例：`/rename 2026-05-25-auth-refactor`）以对齐 session 名称，便于后续在 session 切换器中识别。

---

## phases.md Sync

每个步骤完成后，写入 `{task-folder}/phases.md` 更新：找到对应步骤将 `[ ]` 改为 `[x]`，更新 `**Updated**: YYYY-MM-DD HH:MM`。

**在 1f 写盘前的步骤（1a–1e，含 1b.2/1b.2b/1b.3/1b.4）只在内存标记**——phases.md 尚未创建，其步骤列表由 1b.3 第 6 步在内存计算、1f 一次性写入（届时 1a–1f 全标 `[x]`）。

**Phase 1 完成时**：将 Phase 1 的 `**Status**: PENDING` 改为 `**Status**: DONE`。

---

### P1.phase-end Hook

1f 完成后运行 linear hook：

```bash
hat-plugin-hook {task-folder} P1.phase-end
```

hook 输出按段全部执行（linear plugin: issue 创建/状态更新）。

---

## Init 完成 → 过渡

Phase 1 完成，phases.md 中 Phase 1 Status 已标记为 DONE。用用户配置的语言简要宣告初始化结果（分支、任务文件夹、Linear 状态），然后声明：**"Init 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
Phase skill 完成后回到编排器 Step 3；过渡路由是编排器的职责。transition section 内提示用户调用其它 skill 属于越权，超出本 skill 范围。
Reason: 阶段 skill 不掌握完整过渡逻辑（phase_merge、新会话交接、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 1a | 发现现有任务 | 继续现有 / 创建新任务 |
| 1b.1 | 需求有歧义维度 | 澄清问题 + 确认理解 |
| 1b.2b | 1b.2 低分（2+ ❌ 或 ❌/⚠️≥3）或用户主动 | 进入头脑风暴 / 跳过继续 |
| 1b.3 | 档位推荐 | 确认 preset 和裁剪建议 |
| 1c | Git 规范不存在 | 定义方式选择 |
| 1f（P1.phase-start hook） | 发现 dirty 文件 | 处理方式（stash/commit/继续） |
| 1d | 分支决策 | 必须询问（Interactive） |
| 1d-wt | worktree 隔离（`branch.worktree=="ask"`） | 追加询问是否启用（默认否） |
| 1e | 有 Linear 配置 | 是否创建 issue |
| 1f | Linear issue 创建失败 | 重试 / 跳过 |
| post-1f | 任务文件夹已创建 | 提示执行 `/rename <task-folder-name>` 对齐 session 名 |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Scripts**: hat-task-detect, hat-task-scaffold, hat-git-conventions, hat-plugin-hook, hat-task-config-resolve（三层配置合并）
- **Writes**: `{task-folder}/phases.md`, `{task-folder}/prompt.md`, `{task-folder}/linear.json`, `{task-folder}/task-config.json`, `{task-folder}/session.json`, `{task-folder}/unattended.json`（仅 quiet_mode 物化）
- **Reads（三层配置）**: `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`（①默认模板）, `~/.claude/task-defaults.local.json`（②全局用户 local，可选）, `{project-root}/task-defaults.json`（③项目本地，可选）
- **Worktree（仅 1d-wt 启用时）**: `git worktree add -b task/<folder> <path> HEAD` + 内置 `进入隔离工作树(path=...)` 切入；主仓库写 stub 指针 `$MAIN_ROOT/.tasks/open/<folder>/.worktree`
- **Hooks**（均在 1f 之后运行，依次）: `P1.phase-start`（git: dirty check + 处理）→ `P1.phase-end`（linear: issue setup）
