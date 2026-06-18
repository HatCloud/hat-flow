---
name: task-setup
description: "Use when first configuring the hat-flow task workflow in a project (first-run setup). Guides Linear identity, optional Telegram notifications, enabled plugins, and output language. 触发词: \"task setup\", \"初始化配置\", \"配置任务流\", \"setup hat-flow\""
---

# Task Setup — 首次引导

hat-flow 任务工作流的首次配置向导。引导用户配置 Linear 身份、可选 Telegram 通知、启用哪些插件、输出语言。配置写入**项目本地**（`CLAUDE.md` / `task-defaults.json`），不含任何作者私人值。

**Announce at start:** "Using task-setup to configure the hat-flow workflow."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

> 本向导为**可跳过**：任一步用户选「跳过」即用缺省（对应能力关闭 / 沿用默认），不阻断。所有问题用 AskUserQuestion，逐项确认。

---

## Red Flags

| If you are thinking... | The reality is... |
|---|---|
| "`jq` is missing but I'll push on — most steps don't need it" | `jq` missing means every hook (review/linear/git/timing) silently fails: the flow runs but produces nothing. Stop and have the user install it first. |
| "I'll write my own Linear team/project/key into the config so it just works" | Config must hold no author-private values. Write only what the user selects; this skill ships to other people's projects. |
| "Hardcode the resolved status UUIDs to save a runtime lookup" | State UUIDs are never written here. They resolve at runtime via `get_status_map` by name. Hardcoded UUIDs break across workspaces. |
| "Put the override in the global `task-defaults.json`" | Overrides go to the project-local `task-defaults.json`, never the global preset file. Global edits leak one project's choices into all others. |
| "Set the output language for the user inside this wizard" | Output language follows Claude Code's `/config`; this wizard does not force a language. |

---

## Step 0: 依赖预检

任务流的 hook 引擎与若干 bin 脚本依赖外部命令。**先跑预检**，缺失则提示安装后再继续：

```bash
for c in jq python3; do command -v "$c" >/dev/null 2>&1 && echo "✓ $c" || echo "✗ $c (必需)"; done
command -v node >/dev/null 2>&1 && echo "✓ node (Linear 集成需要)" || echo "○ node 缺失 (仅启用 Linear 时需要)"
```

- **`jq`（必需）**：hook 路由引擎靠它解析 manifest/config；缺失则 review/linear/git/timing 等**所有插件 hook 静默失效**，流程照跑但产物全缺。缺则提示 `brew install jq` / `apt-get install jq`，装好再继续。
- **`python3`（必需，3.8+）**：部分 bin 脚本与流程辅助逻辑运行其上。
- **`node`（可选）**：仅 Linear 集成需要（`@hatcloud/linear-mcp` 经 `npx` 拉起）。未启用 Linear 可忽略。
- **Codex（可选外部插件 `openai-codex`）**：仅当 `plugins.review.reviewer` 或 `execution.engine` 选 `codex` / `auto` 时用于派 Codex 做 design/plan review 或实现执行。**未安装不阻断**——`codex-check` 返回 `FALLBACK:`，流程自动降级 Claude reviewer / executor。

`jq` 或 `python3` 缺失时**不要继续**——先让用户安装。

---

## Step 1: Linear 身份（可选）

Linear 集成用于把任务同步为 issue（状态流转 + 设计/计划/归档评论）。**不配置则 linear 插件优雅关闭**，任务流照常运行。

1. AskUserQuestion：是否启用 Linear 集成？（启用 / 跳过）
2. 若启用：
   - 调 `mcp__linear__list_teams` 列出用户可访问的 team，AskUserQuestion 让用户选择。
   - 调 `mcp__linear__list_projects`（按所选 team）列出 project，让用户选择（可选——无 project 也可）。
   - 把所选 team/project 的 **id + key** 写入项目 `CLAUDE.md` 的 `## Linear 配置` 段落：
     ```markdown
     ## Linear 配置

     - **Team**: <name> (key: <KEY>, id: <uuid>)
     - **Project**: <name> (id: <uuid>)
     ```
   - 状态 UUID **不在此写死**——运行时由 linear 插件经 `mcp__linear__get_status_map` 按 name 动态解析（见 `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/linear.md`）。
3. 若 `mcp__linear__*` 工具不可用（Linear MCP 未配置）→ 提示用户先完成 Step 2（API key + MCP），或本次跳过 Linear。

---

## Step 2: Linear API Key + MCP（仅启用 Linear 时）

Linear 集成依赖 `@hatcloud/linear-mcp`（通过 `npx` 自动安装，无需手动 clone）。用户只需提供 API key：

1. 提示用户在 Linear 设置（Settings → API → Personal API keys）创建一个 Personal API Key。
2. 配置方式：本插件 `plugin.json` 声明了 `userConfig.linear_api_key`（标记 `sensitive`，存入系统密钥串）——提示用户运行 `/plugin` 配置界面填入，或在插件配置中设置 `linear_api_key`。
3. `.mcp.json` 已把 `LINEAR_API_KEY` 绑定到该 userConfig，配置后重启 session 即生效。

---

## Step 3: 启用哪些插件

任务流的 5 个插件（review / linear / git / tdd / retrospective）按需启用。缺省档位见 `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` 的 4 档预设（full / standard / lite / hotfix）。

1. AskUserQuestion：选择缺省档位（standard 推荐 / full / lite / hotfix）。
2. 如需细调（如关闭 retrospective、tdd 改 lite），把 override 写入**项目本地** `task-defaults.json`（复制自 `task-defaults.json.example`），仅写差异项到 `overrides`。
3. linear 插件的 `enabled: auto` 会依据 Step 1 是否写了 `## Linear 配置` 自动决定开关。

---

## Step 4: 输出语言

任务流面向用户的输出语言**跟随 Claude Code 的 `/config` 语言设置**（本插件不强制特定语言）。

1. 提示用户：如需中文/英文/其他输出，用 `/config` 设置语言偏好，或在项目 `CLAUDE.md` 写明语言偏好。
2. 无需在本向导额外配置。

---

## Step 5: Telegram 通知（可选，仅无人值守需要）

无人值守模式（unattended）下的 phase 过渡 / 决策 / 完成通知经 Telegram 发送。**这是可选能力**——不配置则无人值守仍可运行，通知静默降级（打印告警）。

1. AskUserQuestion：是否需要无人值守 Telegram 通知？（需要 / 跳过）
2. 若需要，提示用户：
   - 安装 companion 插件：`/plugin install telegram@claude-plugins-official`
   - 完成配对与策略配置：`/telegram:configure`（或 `/telegram:access`）
3. 配对完成后，**chat_id 落入 personal local 配置**——这样从 CLI 启动（非 Telegram）的会话也能发通知：

   ```bash
   # 1) 从 access.json 读出 allowFrom 里的 chat_id（一般是配对人本人）
   CHAT_ID=$(python3 -c "import json; d=json.load(open('$HOME/.claude/channels/telegram/access.json')); print(d['allowFrom'][0])")

   # 2) 创建或合并 ~/.claude/task-defaults.local.json
   mkdir -p ~/.claude
   if [ -f ~/.claude/task-defaults.local.json ]; then
     python3 -c "import json; p='$HOME/.claude/task-defaults.local.json'; d=json.load(open(p)); d.setdefault('telegram_chat_id','$CHAT_ID'); json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)"
   else
     echo "{\"telegram_chat_id\": \"$CHAT_ID\"}" > ~/.claude/task-defaults.local.json
   fi
   chmod 600 ~/.claude/task-defaults.local.json
   ```

   **为什么必须写到 local 配置**：探测优先级见 UNATTENDED_PROTOCOL.md §3。CLI 启动的会话**没有** Telegram session 上下文，chat_id 只能来自 personal local 配置；写进任何仓库内文件都会污染 hat-flow 分发版。

4. 验证：跑一次 `cat ~/.claude/task-defaults.local.json`，确认含 `"telegram_chat_id": "<id>"`。
5. 不需要 → 跳过；无人值守仍可用（self_test 类型全自动推进，不依赖通知）。

---

## 完成

汇总本次写入的配置（项目 `CLAUDE.md ## Linear 配置` / 本地 `task-defaults.json` override / 提示用户后续手动项），告知用户可随时 `/task` 开始第一个任务。

## Dependencies

- **Writes**: 项目 `CLAUDE.md`（`## Linear 配置`）、项目本地 `task-defaults.json`（override）
- **MCP（可选）**: `mcp__linear__list_teams` / `mcp__linear__list_projects`
- **References**: `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`、`${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/linear.md`
