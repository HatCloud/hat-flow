# hat-flow

[English](./README.md) · **中文**

面向 Claude Code 的规格驱动任务工作流——一套严谨的 **6 阶段生命周期**
（**Init → Design → Plan → Execute → Test → End**），配备插件 hook 系统、
独立的 code/design/plan review、可选的 Linear 与 Telegram 集成，以及 TDD
纪律。它把零散的编码请求变成可复用、可恢复、可审查的工程流程。

## 特性

- **6 阶段生命周期**——每个任务依次走过 Init → Design → Plan → Execute →
  Test → End，跨 session 的进度状态持久化在 `phases.md`。
- **插件 hook 系统**——review、Linear、git、TDD、retrospective 等能力在各
  phase 边界挂载，并按任务用预设档位（`full` / `standard` / `lite` /
  `hotfix`）开关。
- **独立 review**——专门的 code / design / plan reviewer 以只读 subagent
  运行，与执行任务的 agent 分离。
- **TDD 纪律**——可选的红-绿-重构强制约束，带 timing 埋点。
- **跨 session 可恢复**——编排器读取 `phases.md` 精确判断任务从何处续跑。

## 依赖要求

安装前请确保以下命令在 `PATH` 中：

- **`jq`**（必需）——hook 引擎靠它解析 manifest/config；缺失则
  review/linear/git/timing 等**所有插件 hook 静默失效**。安装：
  `brew install jq` / `apt-get install jq`。
- **`python3`**（必需，3.8+）——部分流程辅助逻辑与 bin 脚本运行其上。
- **`node`**（含 `npx`）——仅可选的 Linear 集成需要（`@hatcloud/linear-mcp`
  经 `npx` 拉起）。

运行 `/task-setup` 会执行依赖预检并报告缺失项。

## 安装

```
/plugin marketplace add HatCloud/hat-flow
/plugin install hat-flow@hat-flow
```

> **没配 GitHub SSH key？** `owner/repo` 简写走 SSH 克隆，没配 SSH key 会报
> `Permission denied (publickey)`。本仓库是 public 的——改用显式 HTTPS URL：
> `/plugin marketplace add https://github.com/HatCloud/hat-flow.git`
> （若仍报 SSH 错，说明你的 git 配了 HTTPS→SSH 的 `insteadOf` 重写，需配 SSH
> key 或移除该重写。）

随后运行 `/task-setup` 配置 Linear 身份、可选 Telegram 通知、启用哪些插件、
输出语言。

### 自助安装 prompt（让 Claude Code 帮你装好）

想让你的 Claude Code 自己完成安装 + 配置？把下面这段贴进 Claude Code 会话——
大部分会自动完成，只在需要人决策的少数几项上停下来问你：

```text
帮我安装并配置 hat-flow 任务工作流插件。

1. 安装：
   /plugin marketplace add https://github.com/HatCloud/hat-flow.git
   /plugin install hat-flow@hat-flow
   （Claude Code 提示需要重启则重启）
2. 运行 /task-setup 并完成。以下可自动做：
   - 依赖预检（jq / python3 / node）
   - 项目缺 CLAUDE.md 时写一个骨架
   - 选默认档位（standard）并写项目本地 task-defaults.json 骨架
     （以及我的跨项目默认 ~/.claude/task-defaults.local.json）
   只就以下询问我：
   - Linear：要不要用？要的话 team / project / API key
   - Telegram 无人值守通知：配置还是跳过
   - 本项目的 lint / test 验证命令
   - 本项目是否关闭 worktree 隔离（branch.worktree:false）
3. 完成后告诉我可以用 /task <描述> 开始，或跑全程无人值守：
   claude -p '/task -q <任务或 issue-id>'
```

## 升级

插件**无自动升级**——必须手动触发，且需重启 Claude Code 后新版本才会生效。

### 手动升级

终端里执行：

```text
/plugin update hat-flow
```

然后**重启 Claude Code**（插件在启动时加载，重启前新版本不生效）。

重启后**验证新版本生效**：

- `/plugin` → 查看 `hat-flow` 行显示的版本号
- 或：`cat ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json | grep version`

**`/plugin update` 失败**时（网络 / 缓存问题），重装 marketplace 条目：

```text
/plugin marketplace remove hat-flow
/plugin marketplace add https://github.com/HatCloud/hat-flow.git
/plugin install hat-flow@hat-flow
```

### AI 升级 prompt（让 Claude Code 帮你升）

把下面这段贴进 Claude Code 会话：

```text
帮我升级 hat-flow 插件。

1. 执行 `/plugin update hat-flow`。若网络 / 缓存报错：
   - `/plugin marketplace remove hat-flow`
   - `/plugin marketplace add https://github.com/HatCloud/hat-flow.git`
   - `/plugin install hat-flow@hat-flow`
2. 提示我重启 Claude Code（新版本仅在重启后加载）。
3. 重启后验证新版本已生效：
   - 跑 `/plugin` 看 hat-flow 行的版本号
   - 或：`cat ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json | grep version`
   若版本号未变，立刻停下来告诉我——哪里出问题了。
4. 若我有本地 task-defaults.json（`~/.claude/task-defaults.local.json`
   或 `<project>/task-defaults.json`），对照新版本 schema
   `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` 做 diff。标出任何
   已删除或语义变更的键——但**未经我确认不要改我的文件**。
```

## 快速开始

1. `/task-setup`——首次一次性配置（依赖预检、Linear、插件、语言）。
2. `/task <任务描述>`——启动任务；编排器驱动它走完全部六个阶段。
3. 后续 session 里 `/task`（不带参数）——从中断处恢复进行中的任务。
4. `/task-end`——收尾已完成的任务（终稿报告、retrospective、归档）。

## 配置三层体系

任务行为经三层配置解析（后者覆盖前者），再叠调用时 flag：

| 层 | 文件 | 范围 |
|---|---|---|
| ① 默认模板 | `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` | 随插件分发；只读基线 + 4 档预设 |
| ② 全局用户 | `~/.claude/task-defaults.local.json` | 你的跨项目偏好；**不被插件更新覆盖** |
| ③ 项目本地 | `<project-root>/task-defaults.json` | 项目级覆盖——**最高配置层** |
| ④ 调用 flag | 如 `/task --worktree off …` | 单次调用覆盖，优先级最高 |

合并顺序：`① 默认 < ② 全局 < ③ 项目本地 < ④ flag < 运行时`。只写你要覆盖的键
（稀疏 `overrides` 对象），各层深合并。例：多个任务共享同一工作树的仓库，在其
项目本地 `task-defaults.json` 写 `{"branch": {"worktree": false}}`，覆盖全局的
`worktree:true` 偏好。

关键项：`branch.mode`（缺省 `keep`——留在当前分支，适合同目录多任务协作——/
`new`）、`branch.worktree`（`true` / `false` / `"ask"`），以及无人值守用到的
`headless.*` 自动决策。

## 无头 / 无人值守模式

让任务从头到尾无人参与跑完：

```
claude -p '/task -q <任务描述或 issue-id>'
```

- **`-q` / `--quiet` / `--headless`**（或关键词「无人值守」）开启无人值守。它**仅**
  由这一显式信号确立——没有可靠办法自动探测 `claude -p`，所以**你必须带 `-q`**
  （交互会话和 `-p` 会话在工作流看来一模一样）。
- 无人值守下工作流绝不弹交互：Init 的每个决策都从配置解析（`headless.*`、
  `branch.*`），`branch.worktree` 缺省为 **true**（每次运行隔离在各自的 git
  worktree + task 分支里，主目录 HEAD 永不移动）。
- 可逆卡点优雅降级（`degrade_policy: conservative`）：如 design/plan review 未
  收敛时记录未决 findings 后续跑，而非卡死。不可逆 / 高风险点（验证崩溃、可机判
  MUST 失败、分支 discard）仍硬停。
- 可选 Telegram 通知汇报进度与暂停。

> 把决策前置到 Design/Plan；一旦进入 Execute 就放手不管。项目本地配置写
> `branch.worktree:false` 可让某个仓库退出 worktree 隔离（回到共享一个工作树）。

## Task 参数（参考手册）

任务行为由**命令行 flag + 三层配置文件 + 运行模式语义**共同决定。本节列出
所有可调参数、各模式下的默认值，以及 flag 解析规则。

### 命令行 flag

`/task` 编排器在 Step 0（先于任何 phase）解析 `$ARGUMENTS`。flag 覆盖是稀疏
JSON，作为第 ④ 层经 `hat-task-config-resolve --flags` 合并。

| Flag | 映射到 | 效果 |
|------|--------|------|
| `-q` / `--quiet` | （mode flag） | 开启 Quiet 模式 + `degrade_policy → conservative` |
| `--headless` | （mode flag） | 开启 Headless 模式 + `degrade_policy → headless`（M1 暂按 conservative 行为执行） |
| `--worktree on\|off\|ask` | `branch.worktree` | 显式控制 worktree 隔离 |
| `--no-worktree` | `branch.worktree = false` | `--worktree off` 简写 |
| `--branch keep\|new` | `branch.mode` | 显式控制分支策略 |
| `--preset <name>` | 顶层 `preset` | 覆盖默认档位（`full` / `standard` / `lite` / `hotfix`） |
| 首个位置参数匹配 preset 名 | 顶层 `preset` | tier 关键词快捷方式 |

### 配置参考（`task-defaults.json`）

> **图例：** `"ask"` 是哨兵值——quiet / headless 解析为 `true`，交互模式保留
> `"ask"`（1d 弹询问）。`"auto"` 插件值由 task-init 时刻探测本地环境
> （Linear / git）后决定。

#### 顶层 `preset`

| 默认 | 值域 | 功能 |
|------|------|------|
| `standard` | `full` / `standard` / `lite` / `hotfix` | 从 `presets.*` 选档位块深合并到基线。 |

#### `branch.*` — 任务专用分支与 worktree 隔离

| Key | 类型 | 交互 | Quiet | Headless | 功能 |
|---|---|---|---|---|---|
| `branch.mode` | enum | 1d 弹询问（默认 `keep`） | 沿用配置（默认 `keep`） | 沿用配置 | `keep` 留当前分支；`new` 创建任务分支 |
| `branch.worktree` | tri-state | `"ask"` 弹询问（默认 `false`） | `"ask"` → `true` | `"ask"` → `true` | 显式 `true` / `false` 任何模式覆盖 |
| `branch.name` | string\|null | `null`（按文件夹自动命名） | 同左 | 同左 | 显式分支名覆盖 |

#### `headless.*` — 仅当 `unattended.json enabled == true` 生效

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `headless.existing_task` | enum | `continue` | 有 open task 时续跑还是开新 |
| `headless.git_conventions` | enum | `default` | 找不到 git 规范时的回退（`default` / `implicit` / `skip`） |
| `headless.dirty_policy` | enum | `ignore` | dirty 文件处理（`ignore` / `stash`） |
| `headless.degrade_policy` | enum | `conservative` | 撞卡点分级处理档位（`standard` / `conservative` / `headless`）；交互模式恒 `standard` |
| `headless.linear_on_fail` | enum | `skip` | Linear API 失败处理（`skip` / `retry`） |

#### `end_decisions.*` — Phase 6 自动决策默认值

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `end_decisions.branch` | enum | `keep` | `auto_merge` 自动合并到 main；`keep` 保留分支。`PR` / `Discard` 永不自动触发 |
| `end_decisions.claude_md` | enum | `auto_update` | 是否自动更新项目 `CLAUDE.md` |
| `end_decisions.squash` | bool | `true` | End 把本任务提交压成单 commit（分支合并用 `merge --squash`；main 连续段用 `reset --soft`）；可设 `false` 关闭 |

#### `execution.*` — Phase 4 执行模式与引擎

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `execution.mode` | enum | `auto` | `auto` 按批决策（独立 2+ 互不依赖 → `parallel-agents`；耦合 / 单 → `inline`）/ `inline` 主线程串行 / `parallel-agents` 凡可隔离 task 都派 `task-executor`；legacy `subagent` 已迁移为 `auto` |
| `execution.engine` | enum | `auto` | 仅作用于被派发的 subagent：`auto` 按 (难度, TDD, 复杂度) 选 Sonnet / Opus；显式 `sonnet` / `opus` 覆盖。inline task 恒跑主 agent 当前模型，不受此影响 |

#### `plugins.review.*` — 各阶段独立 review

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `plugins.review.enabled` | bool | `true` | review 总开关 |
| `plugins.review.design_rounds` | mixed | `auto` | `auto` 按复杂度决定（Low:0, Medium:1, High:1-2）/ 数字 = 固定轮次 |
| `plugins.review.code_review` | enum | `medium` | 深度：`skip` / `light` / `medium` / `full` |
| `plugins.review.per_task_review` | enum | `each` | `each` 每个 plan task 后各派一次（最细）；`checkpoint` 仅靠 P4.post-execute 全量 review 兜底 |
| `plugins.review.reviewer` | enum | `claude` | reviewer 类型（暂只支持 `claude`） |
| `plugins.review.max_rounds` | int (1-5) | `3` | reviewer 多轮对话最大轮次 |

#### `plugins.linear.*` — Linear 集成

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `plugins.linear.enabled` | tri-state | `auto` | `auto` 由项目 CLAUDE.md ## Linear / `linear.json` / MCP 可用性决定；写 `task-config.json` 时解析为 `true` / `false` |
| `plugins.linear.update_description` | bool | `true` | 更新 issue 描述 |
| `plugins.linear.upload_docs` | bool | `true` | 上传 design / plan 文档 |
| `plugins.linear.sync_sub_issues` | bool | `true` | 同步子 issue |

#### `plugins.git.*` — git 约定

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `plugins.git.enabled` | tri-state | `auto` | `auto` = 探测 git 仓库（NO_GIT 强制 `false`） |

#### `plugins.tdd.*` — TDD 强制约束

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `plugins.tdd.enabled` | bool | `false` | preset 覆盖（`full` / `standard` → `true`；`lite` / `hotfix` → `false`） |
| `plugins.tdd.mode` | enum | `none` | `none` / `lite` / `full`；`mode != none` 时自动 `enabled = true` |

#### `plugins.retrospective.*` — 归档后流程复盘

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `plugins.retrospective.enabled` | bool | 本分发版默认 `false` | 由 `apply_export_overrides` 软关闭 |

#### 顶层非插件 keys

| Key | 类型 | 默认 | 功能 |
|---|---|---|---|
| `observability.enabled` | bool | 本分发版默认 `false` | gate `hat-timing-stamp` 写入；由导出软关闭 |
| `todo_sync` | bool | `true` | 同步 `phases.md` 到 `TaskCreate` / `TaskUpdate` UI |
| `phase_merge` | array | `[]` | 例：`[[3,4]]` 表示 P3→P4 无停顿。**P5→P6 永不可合并** |

### Preset 档位

| Preset | `execution.mode` | `tdd.mode` | `code_review` | `per_task_review` | `retrospective` | `observability` | `todo_sync` | 典型场景 |
|--------|------------------|------------|----------------|--------------------|------------------|-----------------|--------------|----------|
| `full` | `auto` | `full` | `full` | `each` | `true` | `true` | `true` | 大型重构、契约敏感 |
| `standard`（缺省） | `auto` | `lite` | `medium` | `each` | `true` | `true` | `true` | 通用默认 |
| `lite` | `inline` | `none` | `light` | `each` | `false` | `true` | `true` | 小改动、文档 |
| `hotfix` | `inline` | `none` | `skip` | （跳过） | `false` | **`false`** | **`false`** | 紧急修复（最低开销） |

> 任何字段都可经层 ②（`~/.claude/task-defaults.local.json`）、层 ③
> （`<project>/task-defaults.json`）或调用 flag（最高）覆盖。

### 模式对比

| 维度 | Normal（交互） | Quiet（`-q` / `--quiet` / 「无人值守」） | Headless（`--headless`） |
|------|----------------|---------------------------------------|--------------------------|
| `quiet_mode` | `false` | `true` | `true` |
| `degrade_policy` | `standard`（恒） | `conservative` | `headless`（M1 ≈ conservative） |
| Init 各停顿点 | 询问用户 | 从配置解析 | 从配置解析 |
| `branch.mode` 1d 询问 | 弹询问 | 沿用配置 | 沿用配置 |
| `branch.worktree = "ask"` | 弹询问（默认 `false`） | `true` | `true` |
| Compact 软停顿（Plan→Execute） | 触发 | 跳过 | 跳过 |
| Telegram 通知 | — | opt-in | opt-in |
| `unattended.json` 物化时机 | step 2A.1（交互询问） | task-init `1f` 直接 | task-init `1f` 直接 |

> 目前「Quiet」与「Headless」仅在 `degrade_policy` 语义上有区别（headless 保留
> 给未来更强行为）；两者的 stop-point 自动决策路径相同。

## 插件

| 插件 | 作用 | 缺省 |
|---|---|---|
| `review` | phase 边界的独立 code/design/plan review | 开 |
| `linear` | 把任务同步为 Linear issue（状态 + 设计/计划/归档评论） | auto（配置后自动开） |
| `git` | Conventional Commits、分支命名、dirty-tree 检查 | 开 |
| `tdd` | 每个 execute 任务的红-绿-重构强制 | 随档位 |
| `retrospective` | 归档后的流程审查 | 随档位 |

预设档位给出合理缺省；`/task-setup` 与按任务精调可覆盖其中任意一项。

## 可选集成

- **Linear**——设置 `linear_api_key` 用户配置；`@hatcloud/linear-mcp` 经 `npx`
  拉起。未提供 key 时 Linear 插件自动关闭。
- **Telegram**（无人值守模式通知）——安装配套的
  `telegram@claude-plugins-official` 插件并运行 `/telegram:configure`。

## 致谢

包含 4 个改编自 [obra/superpowers](https://github.com/obra/superpowers)（MIT）的
skill，以 `hatflow-` 前缀收录（`hatflow-systematic-debugging`、
`hatflow-verification-before-completion`、`hatflow-dispatching-parallel-agents`、
`hatflow-receiving-code-review`）。若想用上游可自动触发的原版，直接安装
obra/superpowers——`hatflow-` 前缀让两者并存。

## 更新日志

见 [CHANGELOG.md](./CHANGELOG.md)。用 `/plugin update hat-flow` 升级
（需重启生效），无自动更新。

## 许可证

MIT——见 [LICENSE](./LICENSE)。
