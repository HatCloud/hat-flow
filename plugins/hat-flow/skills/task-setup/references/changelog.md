# Changelog

最新在最上。

## 2026-06-18

- Step 5（Telegram 通知）重构为「配齐通知所需的全部字段」：
  - 原版只引导 `chat_id`、把 token 当作 `/telegram:configure` 的隐式副产物；现显式列出两字段（`TELEGRAM_BOT_TOKEN`→`.env` / `telegram_chat_id`→local）及落点表。
  - 明确通知与插件**解耦**：不装插件也能发（curl 直连 Bot API），给出 `@BotFather` 手动拿 token 写 `.env` 的纯通知路径。
  - 验证步骤覆盖**两个字段**（原只验 chat_id），缺一即静默降级。
  - 背景：telegram 插件因 bun 进程泄漏被全局关闭，暴露「通知靠插件副作用拿 token」的脆弱假设；UNATTENDED_PROTOCOL.md §4 同步改为 curl 前显式 source `.env`。

## 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 补 SKILL.md 的 Red Flags 表。
  - `README.md` 的「核心职责」由逐条镜像 SKILL 步骤收敛为「目的+触发+关键规则」提炼。
