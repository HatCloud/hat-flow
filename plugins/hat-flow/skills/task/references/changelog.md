# Changelog — task (orchestrator)

最新在最上。仅在真改了 skill 时才写，非每轮运行流水。

## 2026-06-17 Telegram 通知发送链路修正 + chat_id 配置分层（个人隐私护栏）

**触发**：归档任务 `2026-06-17-todo-sync-dogfooding` 跑完后，self_test 模式下 unattended.json.telegram_chat_id 始终为 null，所有无人值守通知静默降级；追查发现 3 处叠加问题：

1. **UNATTENDED_PROTOCOL §4 发送工具假设错位**：写"由 companion 插件 `mcp__plugin_telegram_telegram__reply` 工具发送"——`reply` tool 是 reply 到具体 message_id（用于入站消息回复），不适合无人值守的 broadcast 通知（无入站消息）。修正为直接调 Telegram Bot API（`curl https://api.telegram.org/bot<token>/sendMessage`），通知链路与 MCP plugin 解耦（plugin 仅承担 access control / 配对）。
2. **chat_id 配置路径不明**：探测优先级 §3 只写"task-defaults.json"，没说"个人 local 配置"和"分发版污染"两层；新增 4 级优先级（session 上下文 → personal local → 全局 → null）+ `<rule>` 守隐私（chat_id / bot token 任何 hardcode 进仓库源文件都污染 hat-flow 分发版）。
3. **task-setup Step 5 引导缺关键一步**：原本只让用户跑 `/telegram:configure` 配对，配对完无法在 CLI 启动会话里发通知（无 session 上下文）。新增"写入 chat_id 到 `~/.claude/task-defaults.local.json`"的具体 bash 命令段，从 `access.json.allowFrom[0]` 读出本人 chat_id，合并入 local config（chmod 600）。

**同步改动**：
- `task-defaults.json` + `.example`：顶层新增 `telegram_chat_id: null` 字段 + `_telegram_chat_id_note` / `_telegram_chat_id_setup` 注释（说明 null 语义、覆盖路径、获取方式）。默认 null 保持 opt-in。
- 降级告警格式：`[notify] ...` → `★ ...`（更显眼）+ 每条告警给具体配置入口而非笼统"chat_id 不可用"，便于用户立即知道在哪改。

**不动**：MCP plugin 本身 / hat-flow plugin 仓库结构 / 现有 .tasks 归档格式。

**验证**：dogfooding 跑了一次完整 Bot API curl 发送（chat_id=6457159333, token 从 `.env`）→ API `ok:true`、message_id=203、收件人 Jeff Chi (@hat_cloud)；access.json dmPolicy 由 pairing → allowlist（本人 lockdown）；未写 `task-defaults.local.json`（user 选择暂不写全局默认值）。

## 2026-06-17 worktree 跨 session 回切 Step 2B.0 (M2)

- Step 2B 新增 **2B.0 Worktree 回切**：选定 open task 含 `worktree` 指针（hat-task-detect 从主仓库 stub 读出）且 CWD 不在 worktree 内时，`EnterWorktree(path=)` 切入后重新 detect 定位真实任务文件夹；指针失效 → 交互询问 / 无人值守暂停通知。
- 配套：`hat-task-detect` 新增 `worktree` 字段（读 `.worktree` stub 指针）；task-init 1d-wt 物理创建（`git worktree add -b task/<folder> ... HEAD` + `EnterWorktree(path=)`）；task-end 3.4.4 teardown。

## 2026-06-17 无头模式入口 Step 0 + 三层配置 + degrade_policy (M1)

- 新增 **Step 0（Quiet Mode & Flag Parsing）**：入口统一解析 `$ARGUMENTS`，由显式信号（`-q`/`--quiet`/`--headless`/「无人值守」）确立 `quiet_mode` 与 `flag_overrides`；实测无稳定 headless 自动信号（交互会话亦 `ENTRYPOINT=cli` + 非 TTY），故 `<rule>` 禁止 auto-probe 翻转、显式信号为唯一契约。
- 顶部 Unattended Mode note 改为指向 Step 0（统一入口）；quiet 入口由 task-init 1f 物化 `unattended.json`，Step 2A.1 降为后备。
- `UNATTENDED_PROTOCOL.md`：§1 加 `degrade_policy` 字段、§5 加 Quiet 入口、新增 **§9 Degrade Policy**（standard/conservative/headless 分级 + 强制留痕 + HARD-STOP 硬下限）。
- 配套：`task-defaults.json`(+`.example`) 新增顶层 `branch`/`headless`/`end_decisions` 段；新脚本 `bin/hat-task-config-resolve`（三层确定性合并 + worktree "ask" 哨兵解析）。

## 2026-06-16 自进化过程准则改为注入受管 self-evolution.md

- 删手写自进化节、改 `!cat` 硬注入受管副本 `references/self-evolution.md`（防漂移）；changelog 改为仅改 skill 才写、非每轮流水。task 专属归属补充（编排决策点判据 / 不另建 series 经验库）保留在正文。

## 2026-06-15

- 启用编排级自进化：frontmatter 加 `self-evolving: true`；Runtime Context 增加 `references/lessons.md` 注入行（`!`cat``）；过程准则新增「## 自进化（收尾 Dogfooding）」节（裁决漏斗 / 写入闸 + 归属判据 / 整合触发，规则以 spec-skill Self-Evolution 为单一来源）。
- 新建 `references/lessons.md`（编排决策类经验库，表格化 + 硬上限 ≤15，头部记「上次整合」）、`references/lessons-archive.md`（冷归档，永不注入）、`references/changelog.md`（本文件）。
- 修复 README.md 悬空引用：删除子协议表中 `PROCESS_REVIEW_TEMPLATE.md` 一行（该文件在 task/ 不存在）。
