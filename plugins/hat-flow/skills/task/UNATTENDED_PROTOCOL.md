# Unattended Protocol

本文件为 task 系列 skill 的无人值守模式**权威规则来源**。design.md 中的规则表为设计时快照，以本文件为准。

各 skill 在 Process 步骤中**条件加载**本文件（仅当检测到 unattended.json 存在时 `Read` 本文件），**不应**在 Runtime Context 中 `!cat` 本文件以避免无效 token 消耗。

---

## 0. How to Read task-config.json（任务配置）

在无人值守模式激活后（读取 unattended.json 成功且 `enabled == true`），读取任务配置：

```bash
cat "{task-folder}/task-config.json" 2>/dev/null
```

task-config.json 由 P2 Step 2e 生成，包含完整的插件配置快照。若不存在（Phase 1 阶段或旧任务）：

1. 读取全局 `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`
2. 若全局也不存在，从 `.example` 复制创建
3. 使用默认 preset（standard）的配置

解析并存储以下关键字段：

| 字段                         | 默认值       | 说明                                                         |
| ---------------------------- | ------------ | ------------------------------------------------------------ |
| `execution.mode`             | `"inline"`   | 执行模式：`auto` / `inline` / `parallel-agents`              |
| `execution.engine`           | `"auto"`     | 仅 auto/parallel-agents 派发模式：`auto` / `sonnet` / `opus` |
| `plugins.review.code_review` | `"medium"`   | Code review 策略                                             |
| `plugins.review.reviewer`    | `"claude"`   | Reviewer 类型                                                |
| `plugins.review.max_rounds`  | `3`          | 最大 review 轮次                                             |
| `plugins.linear.enabled`     | `true/false` | Linear 集成                                                  |
| `plugins.tdd.mode`           | `"none"`     | TDD 模式                                                     |

将解析结果存为变量 `task_config`，后续各决策点直接引用。

---

## 1. How to Read unattended.json

在各 skill Process 开头（获取 task folder 路径后）执行：

```bash
cat "{open[0].path}/unattended.json" 2>/dev/null
```

解析字段：

- `enabled`: true/false
- `declined`: true/false（可选）。`true` 表示用户**已拒绝**无人值守（区别于延后激活的待激活态）。见第 5 节哨兵语义。
- `activate_after`: `"now"` / `"design"` / `"plan"`（缺省视为 `"now"`；决定 `enabled` 何时翻为 true，见第 5 节）
- `task_type`: `"self_test"` 或 `"user_test"`
- `telegram_chat_id`: 字符串或 null
- `triggered_at`: ISO 时间戳
- `degrade_policy`: `"standard"` / `"conservative"` / `"headless"`（可选；缺省 `standard`）。撞卡点分级处理档位——`standard`=暂停等人工（现状）；`conservative`=可逆点 accept-with-findings 续跑 + 留痕（同点至多一次）；`headless`=同 conservative + 全局 degrade_budget（后续）。由 quiet 入口（`-q` → conservative、`--headless` → headless）或 effective config 的 `headless.degrade_policy` 写入。详见 §9。
- `end_decisions`: （仅 self_test）对象，包含 `branch`/`claude_md` 两个字段

若文件不存在或 `enabled != true`：不进入无人值守模式，按正常交互流程执行。两种 `enabled:false` 须区分：

- **已拒绝（`declined == true`）**：用户主动拒绝无人值守。消费侧守卫须**先判 `declined == true` 并短路**——不再询问、不进激活分支、不推断 `activate_after`（哨兵无 `activate_after` 字段，不可套用「缺省视为 now」）。
- **延后激活（`declined` 缺省/false 且 `activate_after` 为 design/plan）**：待激活态，由编排器 Step 3 在匹配过渡点翻 `enabled`。

---

## 2. How to Detect 无人值守 Keyword

在各 skill Process 开头（读取 unattended.json **之前**）检查：

若用户当前消息包含"无人值守"关键词，且 `{task-folder}/unattended.json` 不存在：
→ 执行 **How to Create unattended.json**（见第 5 节）后继续当前 skill 流程

若 unattended.json 已存在：静默继续（不重复询问）

---

## 3. chat_id Detection（Telegram 为 opt-in，无配置则静默降级）

> Telegram 通知是**可选**能力：需用户自行安装 companion 插件 `telegram@claude-plugins-official` 并完成配对（引导见 task-setup）。未安装 / 未配置时所有 Telegram 通知静默降级（打印一行告警、不阻断流程），无人值守流程照常推进。

<rule>
`chat_id` 和 bot token 都是**用户个人信息**——任何 hardcode 进 `${CLAUDE_PLUGIN_ROOT}/skills/task/` 仓库的源文件都会污染 hat-flow 分发版。配置必须落在仓库外（personal local config 或 plugin 自己的 `.env`）。
Reason: the hat-flow pipeline (`hat-task-package`) reads `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` to bake the public distribution. Any chat_id/bot_token in that file ships to every downstream user and leaks the author's private identifiers.
</rule>

优先级顺序（取第一个成功的）：

1. **Telegram session 上下文**：若当前对话有来自 `<channel source="telegram" ...>` 的消息，从最近一条消息中读取 `chat_id`。适用：从 Telegram 直接启动的会话。
2. **个人 local 配置（推荐）**：`~/.claude/task-defaults.local.json` 的 `telegram_chat_id` 字段。**不入仓库**——hat-flow 用户的 personal override 路径，适合非 Telegram 启动的常规 CLI 会话。task-setup Step 2 引导写入。
3. **全局 / 项目配置**：顶层 `task-defaults.json` 的 `telegram_chat_id` 字段（位于 `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` 或 hat-flow 用户的项目本地 `task-defaults.json`）。**慎用**——分发版场景下要么污染共享文件，要么需每用户单独覆盖。
4. **无可用 chat_id**：将 `telegram_chat_id` 设为 null，跳过所有 Telegram 通知（不报错）。

---

## 4. Telegram Notification

**格式**：所有消息开头带任务标识符

```
[{task-folder-name}] {message}
```

**发送机制**：直接调 Telegram Bot API（`curl`），不依赖 MCP reply tool。broadcast 通知无入站 message 可 reply，MCP `reply` 工具的设计契约不匹配。

```bash
[ -z "${TELEGRAM_BOT_TOKEN:-}" ] && [ -f "$HOME/.claude/channels/telegram/.env" ] \
  && . "$HOME/.claude/channels/telegram/.env"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=[{task-name}] ${message}" \
  -o /dev/null -w "%{http_code}" > /tmp/tg-status 2>&1 || echo "tg-curl-fail"
```

**Token 来源**：
- `$TELEGRAM_BOT_TOKEN` 从 telegram 插件的 `.env` 显式 source（见上方 curl 前置行的具体路径）。**不要假设它已在环境里**：telegram MCP server 把 token source 进的是它自己那个 bun 子进程的环境，不会传播到编排器跑 curl 的 shell；且 `telegram@claude-plugins-official` 插件可能被禁用（无头不需要其入站长轮询）。通知链路与 MCP plugin 完全解耦——plugin 仅承担 access control 配对。
- 独立场景：任何能调 `api.telegram.org` 的 bot token 都可，只要它在 `.env` 里或已 export 到环境。

<rule>
Use the Bot API directly, not the `mcp__plugin_telegram_telegram__reply` tool, for unattended notifications.
Reason: `reply` requires a `message_id` to reply to (it's designed for the inbound-message flow where a Telegram user DMs the bot and the assistant replies). Unattended notifications are outbound broadcasts — there is no inbound message to reply to. Forcing the reply tool here either fails silently or invents a fake message_id, neither of which is honest.
</rule>

**降级（任一缺失/失败都跳、不阻断）**：

| 缺失/失败项 | 跳过的通知 | 告警行 |
|---|---|---|
| `TELEGRAM_CHAT_ID` 为 null | 全部 | `★ Telegram 通知降级：chat_id 未配置 — 编辑 ~/.claude/task-defaults.local.json 加 telegram_chat_id=<id>，或运行 /telegram:configure 配对。` |
| `TELEGRAM_BOT_TOKEN` 为空 | 全部 | `★ Telegram 通知降级：bot token 缺失 — 安装 telegram@claude-plugins-official 并 /telegram:configure <token>。` |
| curl 退出非 0 / HTTP 非 2xx | 当次 | `★ Telegram 通知失败：HTTP=<code> 或 curl error — 本应通知「{message}」。` |

降级告警统一前缀 `★`（比 `[notify]` 更显眼，session 内不易被淹没、事后回看 grep 一搜即得），且每条告警都给出**具体配置入口**而非笼统"chat_id 不可用"——便于用户立即知道在哪改。

**标准通知时机**：

| 时机            | 消息示例                                                               |
| --------------- | ---------------------------------------------------------------------- |
| 无人值守激活    | `[task-name] 无人值守模式已激活，类型：self_test`                      |
| Phase 过渡      | `[task-name] Phase N 完成 → 开始 Phase N+1`                            |
| 关键自动决策    | `[task-name] 自动决策：[问题] → [选择]`                                |
| 澄清假设        | `[task-name] 设计假设：\n- Q: ...\n- A: ...（置信: High）`             |
| BLOCKED cancel  | `[task-name] 任务因阻塞已取消：[原因]`                                 |
| 验证失败 cancel | `[task-name] 验证失败，任务已取消：[错误]`                             |
| git 失败暂停    | `[task-name] git 操作失败，任务已暂停：[错误]，请处理后重新运行 /task` |
| 低置信暂停      | `[task-name] 需要你的输入：[问题列表]，请回复后重新运行 /task`         |
| user_test 停止  | `[task-name] 执行完毕，请手动测试后调用 /task-end`                     |
| 任务完成        | `[task-name] 任务完成 ✓ 已归档`                                        |

---

## 5. How to Create unattended.json

**激活时机：** ① **Quiet 入口**（`-q`/`--quiet`/`--headless`/「无人值守」经编排器 Step 0 确立 `quiet_mode`）——由 task-init **1f** 直接物化 `unattended.json`（`enabled:true, activate_after:"now"`，并带 `degrade_policy`），Init 之后全程无人值守；② **交互入口**——P2 Step 2e 配置面板（主要交互入口）或 Phase 1/2/3 完成后（后备入口，仅当 unattended.json 尚不存在时）询问激活时机。

### activate_after 字段语义（共享契约 SC3）

`unattended.json` 的 `activate_after: "now" | "design" | "plan"`（缺省视为 `"now"`）决定无人值守**何时真正生效**（即 `enabled` 何时翻为 `true`）。producer 侧（task-design Activation Timing、编排器 Step 2A.1）询问激活时机并写入；consumer 侧（编排器 Step 3 步骤 3-a）在匹配过渡点翻 `enabled`。

| `activate_after` | 写入时 `enabled` | 在何处激活（翻 `enabled:true`）               |
| ---------------- | ---------------- | --------------------------------------------- |
| `"now"`          | `true`           | 写入即生效，无需后续激活                      |
| `"design"`       | `false`          | 编排器 Step 3 在 **Design 完成后** 过渡时激活 |
| `"plan"`         | `false`          | 编排器 Step 3 在 **Plan 完成后** 过渡时激活   |

延后激活（`design`/`plan`）期间 `enabled:false`，各 skill 按正常交互流程执行；过渡到匹配阶段时编排器翻 `enabled:true` 并加载本文件。延后激活默认任务类型为 `self_test`，其 `end_decisions`（branch / claude_md）取协议默认值（分支自动合并、CLAUDE.md 按需更新）——激活点不再补问，避免打断已转入的无人值守。

### declined 哨兵语义（用户拒绝无人值守）

当激活询问的 option 为「否」（用户拒绝无人值守）时，写入**拒绝哨兵**：

```json
{ "enabled": false, "declined": true }
```

该哨兵**不含** `activate_after` 字段。其作用是把「用户已拒绝」这一决定持久化，使后续过渡点不再重复询问。消费侧守卫（编排器 Step 2A.1 / Step 3、task-design Step 2e）须遵守：

<rule>
Consumer guards MUST check `declined == true` first and short-circuit: skip the activation question, do not enter any activation branch, and do not infer `activate_after`.
Reason: the declined sentinel carries no `activate_after`, so a guard that falls through to the "缺省视为 now" rule (§1) would misread an explicit rejection as immediate activation. Choosing an explicit `declined` field (rather than reusing bare `enabled:false`) keeps it distinct from the deferred-activation state, which also has `enabled:false` but carries `activate_after`.
</rule>

**激活步骤：**

1. 执行 **chat_id Detection**（第 3 节）获取 `telegram_chat_id`
2. 确定 `activate_after`（由 producer 询问得到：现在启用→`now`；Design 后→`design`；Plan 后→`plan`）
3. 仅当 `activate_after == "now"` 时，`AskUserQuestion`：任务类型？（延后激活时任务类型可在激活点或沿用默认 self_test）
   - **自测任务（Recommended）** — 无需用户测试，自动推进到 task-end
   - **需要用户测试** — 执行完毕后 Telegram 通知，停在 task-test
4. 若选择 **自测任务**：追加 End 阶段决策收集（AskUserQuestion）：
   - **分支处理**：`"auto_merge"` / `"keep"`
   - **CLAUDE.md 更新**：`"auto_update"` / `"skip"`
   - **squash**：`true` / `false`（缺省 `true`，取 effective config `end_decisions.squash`；通常沿用默认不单独询问）
5. 写入文件（`enabled` 不再硬编码为 `true`——按 `activate_after` 决定：`now` → `true`，`design`/`plan` → `false`）：
   ```json
   {
     "enabled": true,
     "activate_after": "now",
     "task_type": "self_test",
     "telegram_chat_id": "{detected_chat_id_or_null}",
     "triggered_at": "{ISO_timestamp}",
     "end_decisions": {
       "branch": "auto_merge",
       "claude_md": "auto_update"
     }
   }
   ```
   延后激活示例（选 "Design 阶段结束后启用"）：`{"enabled": false, "activate_after": "design", ...}`
6. 发送 Telegram 确认（仅 `activate_after == "now"` 即时发送；延后激活在编排器 Step 3 实际翻 `enabled` 时通知）

---

## 6. Auto-Decision Rules

各停止点在无人值守模式下的自动决策。

### 核心决策（始终生效）

#### orchestrator 过渡（task/SKILL.md Step 3）

| 停止点                          | 自动决策                                                                                                                                                  |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Design 完成后过渡               | 若 `activate_after == "design"` 且当前 `enabled:false` → 翻 `enabled:true` 并加载本文件（激活无人值守）；已 `enabled:true` → 静默推进，不询问、不 compact |
| Plan 完成后过渡（compact 软停） | 已激活或本过渡点即将激活（`activate_after == "plan"`）→ 跳过 compact 建议（不输出 `/compact` 块），翻 `enabled:true` 后静默推进到 Execute                 |

> 延后激活（`activate_after` 为 design/plan）在匹配过渡点由编排器翻 `enabled`；翻转后发送"无人值守模式已激活"通知。两条停顿路径（Design/Plan 过渡）均不靠人工应答推进。

#### task-init

| 停止点                    | 自动决策                                                                                                                         |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Dirty 文件                | 忽略，直接继续                                                                                                                   |
| 分支决策                  | 留在当前分支                                                                                                                     |
| 新分支分叉告警（ISSUE） | 仅「创建新分支」路径触发——Unattended 分支决策默认「留在当前分支」故通常不触发；若触发则记录告警、不阻塞（NO_GIT/git 关闭亦跳过） |

#### task-design

| 停止点                   | 自动决策                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| 澄清问题（Step 2）       | 多轮 subagent 自讨论（见第 7 节）                                                        |
| 选择方案（Step 3）       | 按推荐选项                                                                               |
| 每节确认（Step 4）       | 自我检查通过即继续                                                                       |
| 配置面板（Step 2e）      | 按启发式推荐档位                                                                         |
| 批准 design.md（Step 8） | 有 reviewer 时 C/I 过线自动批准；无 reviewer 轮次（Low）直接自动批准；均不等待纯文本确认 |
| Step 7 达 `max_rounds`   | 不询问，Telegram 通知后暂停（等待 `/task` 恢复人工决策）                                 |

#### task-plan

| 停止点             | 自动决策                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Plan format        | 按 task-config.json 配置                                                                                                       |
| 3b 收敛后确认循环  | `Verdict == Approved` 直接推进 3c（跳过“是否有补充/继续”）；`Verdict == Issues` 修复后重跑一次，仍 Issues 则 Telegram 通知暂停 |
| 3b 达 `max_rounds` | 不询问，Telegram 通知后暂停（等待 `/task` 恢复人工决策）                                                                       |

#### task-execute（Phase 4）

| 停止点                     | 自动决策                                                                    |
| -------------------------- | --------------------------------------------------------------------------- |
| Light 验证未配置           | 跳过验证                                                                    |
| BLOCKED                    | 重试一次（Opus）；系统性问题→转 Revise，非系统性问题→auto-cancel + Telegram |
| NEEDS_CONTEXT 2 次后仍失败 | 视为 BLOCKED                                                                |
| 执行引擎                   | 按 `task_config.execution.mode` + `engine`                                  |

#### task-test（Phase 5）

| 停止点                | 自动决策                                                                                                                                                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 验收清单（self_test） | 仅评估**可机判**验收项：可机判 MUST/SHOULD FAIL → 修复循环（重试一次 Opus），无解 → 暂停 + Telegram 通知人工（**非 auto-cancel**，见第 8 节）；不可机判 SHOULD/MAY → deferred 不阻断；全 PASS（含 deferred）→ 更新 phases.md DONE，推进 task-end |
| 验收清单（user_test） | Telegram 通知，停止                                                                                                                                                                                                                              |

#### task-end（Phase 6）

| 停止点                   | 自动决策                                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 多 open task 选择        | 选 `Updated` 最新任务；无法判定则 Telegram 通知后暂停                                                                                                   |
| 验证失败                 | 重试一次（Opus 修复），仍失败 → auto-cancel + Telegram                                                                                                  |
| CLAUDE.md 更新           | 读 `end_decisions.claude_md`                                                                                                                            |
| 分支处理 keep（ISSUE） | 追加 `docs/unmerged-branches.md` 登记（不提示）                                                                                                         |
| 分支处理（4 选项菜单）   | 读 `end_decisions.branch` 映射：`auto_merge`→Merge locally / `keep`→Keep as-is；**`PR` / `Discard` 永不自动触发（跳过）**；字段缺失或非法值 → 默认 keep |
| 提交压缩 squash          | 读 `end_decisions.squash`（缺省 true）：`auto_merge` 合并用 `merge --squash`；main 连续提交段在守卫全通过时 `reset --soft` 压缩，任一守卫不过则保守跳过（见 git plugin P6.post-archive 1.5 + `<rule>`） |

#### task-cancel

| 停止点       | 自动决策           |
| ------------ | ------------------ |
| 取消原因     | 从调用上下文推断   |
| 处置方式     | Cancel（不 Defer） |
| 代码变更处理 | Keep（保留分支）   |

### 插件条件化决策

以下决策仅在对应插件启用时执行：

#### git plugin (`plugins.git.enabled`)

| 停止点         | 自动决策                         |
| -------------- | -------------------------------- |
| Git 规范不存在 | Use default Conventional Commits |
| git 操作失败   | **暂停**，Telegram 通知          |

#### linear plugin (`plugins.linear.enabled`)

| 停止点            | 自动决策             |
| ----------------- | -------------------- |
| 创建 Linear issue | 自动创建             |
| Linear API 失败   | 跳过，继续（不通知） |
| 子 issue          | Cancel together      |

#### review plugin (`plugins.review.enabled`)

| 停止点           | 自动决策                          |
| ---------------- | --------------------------------- |
| Review 策略      | 按 `task_config.plugins.review.*` |
| Code review 确认 | 自动执行                          |
| Revise 触发      | 自动选择深度                      |

#### tdd plugin (`plugins.tdd.enabled`)

| 停止点           | 自动决策                                 |
| ---------------- | ---------------------------------------- |
| TDD RED 意外通过 | 自动调整，记录到 unattended-decisions.md |

#### retrospective plugin (`plugins.retrospective.enabled`)

| 停止点                | 自动决策       |
| --------------------- | -------------- |
| Process Review Part B | 自动写 debt.md |
| 技术债务              | 自动写 debt.md |

> `end_decisions` 字段在创建 unattended.json 时由用户预先决定（见第 5 节）。

---

## 7. Self-Discussion Protocol（替代 task-design Step 2 的 AskUserQuestion）

**触发条件**：task-design Step 2，unattended 模式，主 agent 有需要澄清的问题。

### Requirements Analyst Subagent

使用 **Agent tool**（general-purpose，**非后台**）派发 Requirements Analyst subagent：

```
你是一个需求分析师。
任务：基于以下上下文，回答每个澄清问题。

输入：
- prompt.md 内容：{content}
- 相关代码上下文：{relevant_snippets}
- 澄清问题列表：{questions}

对每个问题输出：
Q: [问题]
A: [答案]
置信: High / Medium / Low
依据: [推理过程]
```

若有 Medium 或 Low 置信答案，再派发 Devil's Advocate subagent 反驳低置信答案，综合两轮结论。

### 结果处理

1. 写入 `{task-folder}/unattended-decisions.md`
2. 发送 Telegram 通知关键假设

### 低置信暂停

两轮后仍有 Low 置信**关键问题**（影响设计方向、无法从代码上下文推导）：

- → 暂停，Telegram 通知用户
- → 任务停在当前阶段，等待新 session 恢复
- 非关键问题（格式偏好、命名风格）取答案继续

---

## 8. Error Handling

| 错误类型                                                 | 处理                                                                                                                                                   | Telegram |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| subagent BLOCKED                                         | 重试一次（切换 Opus），仍失败 → auto-cancel                                                                                                            | 通知原因 |
| 验证命令失败（Step 0 / 5a 的 build/test 命令本身崩溃）   | 重试一次（Opus 修复），仍失败 → auto-cancel                                                                                                            | 通知详情 |
| 验收项 FAIL（self_test 可机判 MUST/SHOULD 清单项不达标） | 进修复循环重试一次（Opus），仍无解 → **暂停** + 通知人工（**非 auto-cancel**——与"验证命令失败"区分：清单项是质量问题、保留任务等人工，命令崩溃才取消） | 通知内容 |
| git 操作失败                                             | **暂停**（仅 git plugin 启用时），不 cancel                                                                                                            | 通知错误 |
| Linear API 失败                                          | 跳过，继续（仅 linear plugin 启用时）                                                                                                                  | 不通知   |
| 低置信澄清问题                                           | 暂停等待用户回复                                                                                                                                       | 通知内容 |
| 未预期异常                                               | auto-cancel                                                                                                                                            | 通知异常 |

**auto-cancel 流程：** 直接执行 task-cancel 核心逻辑（归档为 canceled），发送 Telegram 通知后停止。

**暂停恢复：** 任务停在当前阶段（phases.md 状态不变）。用户下次运行 `/task` 时恢复。

---

## 9. Degrade Policy（撞卡点分级处理）

`unattended.json` 的 `degrade_policy` 决定无人值守撞到「可逆/可降级卡点」时的处理强度。**非无人值守模式恒按 `standard`**（与改造前逐字等价，向后兼容）。

| 卡点 | `standard`（缺省=现状） | `conservative` | `headless`（后续） |
|------|------------------------|----------------|--------------------|
| A4 design/plan review 达 `max_rounds` 不收敛 | 暂停 + Telegram 通知（§6/§8） | **accept-with-findings 续跑**：剩余 findings 原文写 `## Unresolved Review Findings`（design.md / plan.md）+ `unattended-decisions.md`，续跑；**同点同 phase 至多一次**，第二次退回 `standard`（暂停）。兜底：P4 review + P5 验收双网 | 同 conservative + 全局 degrade_budget |
| A3 task-end 债务对账 | 现降级 + 高置信关/低置信留 | 维持现降级 + 关闭动作 / 低置信疑似项汇总进 `unattended-decisions.md`，final.md P6 引用 | 同 conservative + degrade_budget |
| A2 user_test | 停（按 task_type） | 停 | 转 self_test + deferred（后续） |

### 强制留痕（conservative / headless）

每次 AUTO-DEGRADE 必须留痕：

- `unattended-decisions.md` 追加 `## Headless Degraded Decisions` 段，逐条记「卡点 / 原文 findings / 自动决策 / 同点是否已用过一次」。
- final.md（task-end P6）汇总引用这些降级决策，使人工回看可见。

### HARD-STOP 硬下限（任何 degrade_policy 都不自动续，必停）

<rule>
The following are HARD-STOP points that NO degrade_policy may auto-continue past: branch PR/Discard decisions, git operation failure, verification command crash, machine-judgeable MUST/SHOULD acceptance FAIL, artifact gate FAIL, and multiple parallel open tasks. These always pause (Telegram notify) and wait for a human.
Reason: these are irreversible or high-risk — auto-continuing past them can destroy work (discard), ship broken code (verification crash / MUST FAIL), or corrupt task state (artifact gate). Graduated degradation only applies to reversible/degradable points (review non-convergence, debt reconciliation); the hard floor is non-negotiable.
</rule>

- A4 的「续跑」仅适用于 **design/plan review 不收敛**（可逆——findings 留痕、P4/P5 双网兜底）；**绝不**适用于上方 HARD-STOP 清单。
- `degrade_policy` 缺省（字段不存在）或为 `standard` 时，A4/A3 走原暂停路径——现有任务零行为变更。
