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

## 快速开始

1. `/task-setup`——首次一次性配置（依赖预检、Linear、插件、语言）。
2. `/task <任务描述>`——启动任务；编排器驱动它走完全部六个阶段。
3. 后续 session 里 `/task`（不带参数）——从中断处恢复进行中的任务。
4. `/task-end`——收尾已完成的任务（终稿报告、retrospective、归档）。

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

## 许可证

MIT——见 [LICENSE](./LICENSE)。
