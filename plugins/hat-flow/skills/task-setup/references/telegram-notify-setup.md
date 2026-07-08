# Telegram 通知落地细节

task-setup Step 5 的操作细节（仅在用户选择启用无人值守通知时按需读取）。通知走 `curl` 直连 Bot API、与 telegram 插件解耦（机制见 UNATTENDED_PROTOCOL.md §4）——下面两个字段就位即可发通知，不要求装插件；插件仅负责入站双向交互 / access control。缺任一字段，通知都会静默降级。

## 拿 token 并写入 .env

按是否还要**双向遥控**二选一：

- **要双向遥控**（从 Telegram 反向给 Claude 发指令 / 远程批准）：装插件 `/plugin install telegram@claude-plugins-official` + `/telegram:configure`——配对会把 token 写入 `.env`、配对人写入 access.json。
- **只要单向通知**（无人值守推荐，最省）：找 `@BotFather` 建 bot 拿 token，手动写入 `.env`：

  ```bash
  mkdir -p ~/.claude/channels/telegram
  printf 'TELEGRAM_BOT_TOKEN=%s\n' '<你的-bot-token>' > ~/.claude/channels/telegram/.env
  chmod 600 ~/.claude/channels/telegram/.env
  ```

## 配置 chat_id 到 personal local

CLI 启动的会话没有 Telegram session 上下文，chat_id 只能来自 personal local（落点是 personal local 而非仓库内文件——写进仓库会污染 hat-flow 分发版，探测优先级见 UNATTENDED_PROTOCOL.md §3）：

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

## 验证两个字段都就位

```bash
grep -q '^TELEGRAM_BOT_TOKEN=' ~/.claude/channels/telegram/.env 2>/dev/null && echo "✓ token" || echo "✗ 缺 token"
grep -q 'telegram_chat_id' ~/.claude/task-defaults.local.json 2>/dev/null && echo "✓ chat_id" || echo "✗ 缺 chat_id"
```

两项都 ✓ 才算配置完成。可选实发一条测试通知验证连通性：见 UNATTENDED_PROTOCOL.md §4 的 curl 片段。
