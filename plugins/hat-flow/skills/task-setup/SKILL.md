---
name: task-setup
description: "Use when first configuring the hat-flow task workflow in a project (first-run setup). Guides Linear identity, optional Telegram notifications, enabled plugins, and output language. Do NOT use for editing existing config (edit task-defaults.json directly). 触发词: \"task setup\", \"初始化配置\", \"配置任务流\", \"setup hat-flow\""
---

# Task Setup — 首次引导

hat-flow 任务工作流的首次配置向导。引导配置 Linear 身份、可选 Telegram 通知、启用哪些插件、输出语言。配置写入**项目本地**（`CLAUDE.md` / `task-defaults.json`），不含任何作者私人值。

**Announce at start:** "Using task-setup to configure the hat-flow workflow."

> 本向导可跳过：任一步选「跳过」即用缺省（对应能力关闭 / 沿用默认），不阻断流程。所有问题用 AskUserQuestion 逐项确认。

---

## Step 0: 依赖预检

任务流的 hook 引擎与若干 bin 脚本依赖外部命令。预检为首步，缺失项提示安装后再继续：

```bash
command -v python3 >/dev/null 2>&1 && echo "✓ python3" || echo "✗ python3 (必需)"
command -v node >/dev/null 2>&1 && echo "✓ node (Linear 集成需要)" || echo "○ node 缺失 (仅启用 Linear 时需要)"
```

- **`python3`（必需，3.8+）**：hook 路由引擎（`hat-plugin-hook`，纯 Python、零依赖）、门控脚本、bin 脚本均运行其上；缺失则所有插件 hook 静默失效、流程照跑但产物全缺。提示 `brew install python` / `apt-get install python3`。
- **`node`（可选）**：仅 Linear 集成需要（`@hatcloud/linear-mcp` 经 `npx` 拉起）。
- **Codex（可选外部插件 `openai-codex`）**：仅 `plugins.review.reviewer` 或 `execution.engine` 选 `codex` / `auto` 时用于 design/plan review 或执行。未装不阻断——`codex-check` 返回 `FALLBACK:`，自动降级 Claude reviewer / executor。

<rule>
python3 缺失时，setup 不继续——提示用户安装后再重跑。
Reason: 缺失则全部插件 hook 静默失效，流程看似跑通但产物全缺。
</rule>

---

## Step 1: Linear 身份（可选）

Linear 集成把任务同步为 issue（状态流转 + 设计/计划/归档评论）。未配置时 linear 插件优雅关闭，任务流照常运行。

1. AskUserQuestion：是否启用 Linear 集成？（启用 / 跳过）
2. 若启用：
   - 调 `mcp__linear__list_teams` 列 team，AskUserQuestion 让用户选择。
   - 调 `mcp__linear__list_projects`（按所选 team）列 project 让用户选择（可选——无 project 也可）。
   - 把所选 team/project 的 **id + key** 写入项目 `CLAUDE.md` 的 `## Linear 配置` 段落：
     ```markdown
     ## Linear 配置

     - **Team**: <name> (key: <KEY>, id: <uuid>)
     - **Project**: <name> (id: <uuid>)
     ```
   - 状态 UUID 不写死——运行时由 linear 插件经 `mcp__linear__get_status_map` 按 name 动态解析（见 `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/linear.md`）。
   - team/project 值只取用户当场所选，不含作者私人值。
3. `mcp__linear__*` 不可用（Linear MCP 未配置）→ 提示用户先完成 Step 2（API key + MCP），或本次跳过 Linear。

---

## Step 2: Linear API Key + MCP（仅启用 Linear 时）

Linear 集成依赖 `@hatcloud/linear-mcp`（经 `npx` 自动安装，无需手动 clone）。用户只需提供 API key：

1. 提示用户在 Linear 设置（Settings → API → Personal API keys）创建 Personal API Key。
2. 本插件 `plugin.json` 声明了 `userConfig.linear_api_key`（标记 `sensitive`，存入系统密钥串）——提示用户运行 `/plugin` 配置界面填入。
3. `.mcp.json` 已把 `LINEAR_API_KEY` 绑定到该 userConfig，配置后重启 session 即生效。

---

## Step 3: 启用哪些插件

任务流的 5 个插件（review / linear / git / tdd / retrospective）按需启用。缺省档位见 `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` 的 4 档预设（full / standard / lite / hotfix）。

1. AskUserQuestion：选择缺省档位（standard 推荐 / full / lite / hotfix）。
2. 如需细调（如关闭 retrospective、tdd 改 lite），把差异项写入**项目本地** `task-defaults.json`（复制自 `task-defaults.json.example`）的 `overrides`。落点须是项目本地文件而非全局预设档（`${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`）——写全局会把单个项目的选择泄漏到所有项目。
3. linear 插件的 `enabled: auto` 会依据 Step 1 是否写了 `## Linear 配置` 自动决定开关。

---

## Step 4: 输出语言

任务流面向用户的输出语言**跟随 Claude Code 的 `/config` 语言设置**（本插件不强制特定语言）。

1. 提示用户：如需中文/英文/其他输出，用 `/config` 设置语言偏好，或在项目 `CLAUDE.md` 写明语言偏好。
2. 无需在本向导额外配置。

---

## Step 5: Telegram 通知（可选，仅无人值守需要）

无人值守模式（unattended）下的 phase 过渡 / 决策 / 完成通知经 Telegram 发送。可选能力——未配置时无人值守仍可运行，通知静默降级（打印告警）。

通知所需的两个字段（缺任一都静默降级）：

| 字段 | 落点 | 作用 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | telegram 插件的 `.env` | 调 Bot API 的凭证 |
| `telegram_chat_id` | `~/.claude/task-defaults.local.json` | 通知发给谁 |

1. AskUserQuestion：是否需要无人值守 Telegram 通知？（需要 / 跳过）
2. 若需要：按 `references/telegram-notify-setup.md` 拿 token 写入 `.env`、配 chat_id 到 personal local、验证两字段就位。两项都 ✓ 才算配置完成。
3. 不需要 → 跳过；无人值守仍可用（self_test 类型全自动推进，不依赖通知）。

---

## 完成

汇总本次写入的配置（项目 `CLAUDE.md ## Linear 配置` / 本地 `task-defaults.json` override / 提示用户后续手动项），告知用户可随时 `/task` 开始第一个任务。

## Dependencies

- **Writes**: 项目 `CLAUDE.md`（`## Linear 配置`）、项目本地 `task-defaults.json`（override）、Telegram 通知 `.env` 与 `~/.claude/task-defaults.local.json`（Step 5 无人值守通知，具体路径见 `references/telegram-notify-setup.md`）
- **MCP（可选）**: `mcp__linear__list_teams` / `mcp__linear__list_projects`
- **References**: `references/telegram-notify-setup.md`（Step 5 按需 Read）、`${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`、`${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/linear.md`
