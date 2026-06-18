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

通知走 `curl` 直连 Bot API、**与 telegram 插件解耦**（机制见 UNATTENDED_PROTOCOL.md §4）：只要下面**两个字段**就位即可发通知，**不要求装插件**——插件仅负责入站双向交互 / access control。引导用户时必须把两个字段都配齐并验证，缺任一通知都会静默降级。

**通知所需的全部字段：**

| 字段 | 落点 | 作用 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | telegram 插件的 `.env`（具体路径见下方 step 2 命令） | 调 Bot API 的凭证 |
| `telegram_chat_id` | `~/.claude/task-defaults.local.json` | 通知发给谁 |

1. AskUserQuestion：是否需要无人值守 Telegram 通知？（需要 / 跳过）
2. 若需要，按是否还要**双向遥控**二选一拿到 token，写入 `.env`：
   - **要双向遥控**（从 Telegram 反向给 Claude 发指令 / 远程批准）：装插件 `/plugin install telegram@claude-plugins-official` + `/telegram:configure`——配对会把 token 写入 `.env`、配对人写入 access.json。
   - **只要单向通知**（无人值守推荐，最省）：找 `@BotFather` 建 bot 拿 token，手动写入 `.env`：

     ```bash
     mkdir -p ~/.claude/channels/telegram
     printf 'TELEGRAM_BOT_TOKEN=%s\n' '<你的-bot-token>' > ~/.claude/channels/telegram/.env
     chmod 600 ~/.claude/channels/telegram/.env
     ```

3. 配置 chat_id 到 personal local（CLI 启动的会话**没有** Telegram session 上下文，chat_id 只能来自这里；写进任何仓库内文件会污染 hat-flow 分发版，探测优先级见 UNATTENDED_PROTOCOL.md §3）：

   ```bash
   # chat_id 来源：装了插件 → 从 access.json 读；没装 → 给 bot 发一条消息后访问
   #   https://api.telegram.org/bot<token>/getUpdates 取 result[].message.chat.id，或用 @userinfobot 查自己的 id
   CHAT_ID=$(python3 -c "import json; d=json.load(open('$HOME/.claude/channels/telegram/access.json')); print(d['allowFrom'][0])" 2>/dev/null || true)
   [ -z "$CHAT_ID" ] && read -rp "输入 chat_id: " CHAT_ID
   mkdir -p ~/.claude
   if [ -f ~/.claude/task-defaults.local.json ]; then
     python3 -c "import json; p='$HOME/.claude/task-defaults.local.json'; d=json.load(open(p)); d['telegram_chat_id']='$CHAT_ID'; json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)"
   else
     echo "{\"telegram_chat_id\": \"$CHAT_ID\"}" > ~/.claude/task-defaults.local.json
   fi
   chmod 600 ~/.claude/task-defaults.local.json
   ```

4. **验证两个字段都就位**（缺一不可）：

   ```bash
   grep -q '^TELEGRAM_BOT_TOKEN=' ~/.claude/channels/telegram/.env 2>/dev/null && echo "✓ token" || echo "✗ 缺 token"
   grep -q 'telegram_chat_id' ~/.claude/task-defaults.local.json 2>/dev/null && echo "✓ chat_id" || echo "✗ 缺 chat_id"
   ```

   两项都 ✓ 才算配置完成。可选实发一条测试通知验证连通性：见 UNATTENDED_PROTOCOL.md §4 的 curl 片段。
5. 不需要 → 跳过；无人值守仍可用（self_test 类型全自动推进，不依赖通知）。

---

## 完成

汇总本次写入的配置（项目 `CLAUDE.md ## Linear 配置` / 本地 `task-defaults.json` override / 提示用户后续手动项），告知用户可随时 `/task` 开始第一个任务。

## Dependencies

- **Writes**: 项目 `CLAUDE.md`（`## Linear 配置`）、项目本地 `task-defaults.json`（override）
- **MCP（可选）**: `mcp__linear__list_teams` / `mcp__linear__list_projects`
- **References**: `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`、`${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/linear.md`
