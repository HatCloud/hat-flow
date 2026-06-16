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
