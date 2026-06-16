# Task Setup Skill

## 目的

hat-flow 任务工作流的**首次配置向导**（first-run setup）。引导用户在一个项目里完成任务流的初始配置，把结果写入**项目本地**（`CLAUDE.md` / `task-defaults.json`），不含任何作者私人值。

## 触发条件

- 在新项目里第一次准备用 task 工作流时
- 直接调用 `/task-setup`
- 触发词："task setup"、"初始化配置"、"配置任务流"、"setup hat-flow"

## 核心职责

**目的**：一次性把任务流在某项目里配置就位——依赖预检、Linear 身份、可选 Telegram 通知、插件档位、输出语言。

**触发**：新项目首次准备用 task 工作流，或直接 `/task-setup`。

**关键规则**：
- 依赖预检中 `jq` / `python3` 为必需，缺则不继续（hook 引擎与 bin 脚本靠它）
- 配置只写**项目本地**（`CLAUDE.md` / `task-defaults.json`），绝不写入作者私人值或硬编码状态 UUID
- 全程可跳过；所有问题用 AskUserQuestion 逐项确认

## 关键规则

- **全程可跳过**：任一步选「跳过」即用缺省（对应能力关闭 / 沿用默认），不阻断流程
- 所有问题用 AskUserQuestion，逐项确认
- 配置只写**项目本地**，绝不写入作者私人值（分发安全）

## 产物

- 项目 `CLAUDE.md` 的任务流相关段
- 项目 `task-defaults.json`（档位预设 + 插件开关）

## 在 task 族中的位置

`task` 编排族的**配置入口** worker：在 `task` 编排正式跑流程前，由本 skill 把项目配置就位。与生命周期内各 worker（init/design/plan/execute/test/end）不同，它只在「首次接入」时跑一次。
