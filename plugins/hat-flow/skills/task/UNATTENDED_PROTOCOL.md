# Unattended Protocol

本文件为 task 系列 skill 的无人值守模式**权威规则来源**。design.md 中的规则表为设计时快照，以本文件为准。外部驱动方（E2E / cron / 调度器）的机读契约见 `references/headless-driving.md`（state.json schema + 驱动判定算法）。

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
Reason: hat-flow 流水线（`hat-task-package`）读取 `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` 来烘焙公开分发版。该文件里的任何 chat_id/bot_token 都会随之发给每一个下游用户，泄漏作者的私有标识符。
</rule>

**显式关闭短路（先于整条探测链）**：项目本地 `task-defaults.json` 显式写 `"telegram_chat_id": null`（或 `false`）= 该项目**显式禁用** Telegram 通知——短路下方整条探测链，不再回退到 personal local 等其它来源。「显式禁用」与「字段缺失」语义不同：缺失才走探测链。适用：测试床 / 预演 / 不希望产生真实外部通知的项目。

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
无人值守通知直接走 Bot API；不使用 `mcp__plugin_telegram_telegram__reply` 工具来发送它们。
Reason: `reply` 需要一个 `message_id` 作为回复对象（它是为入站消息流设计的——Telegram 用户私信 bot、助手回复）。无人值守通知是出站广播，没有可回复的入站消息。在这里强用 reply 工具，要么静默失败、要么编造一个假的 message_id，两者都不诚实。
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

**激活时机：** ① **Quiet 入口**（`-q`/`--quiet`/`--headless`/「无人值守」经编排器 Step 0 确立 `quiet_mode`）——由 task-init **1f** 直接物化 `unattended.json`（`enabled:true, activate_after:"now"`，并带 `degrade_policy`），Init 之后全程无人值守；② **交互主入口**——编排器 Step 2A.1（Phase 1/2/3 完成后的过渡点，仅当 unattended.json 尚不存在时询问；编排路径下 Init→Design 过渡必先经此，四个选项都写入文件）；③ **standalone 后备**——task-design Step 2e Activation Timing，仅在 task-design 被独立调用（未经编排器、文件尚不存在）时兜底询问。

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
Consumer 侧守卫先检查 `declined == true` 并短路：跳过激活询问、不进入任何激活分支、不推断 `activate_after`。
Reason: declined 哨兵不带 `activate_after`，因此一个落到「缺省视为 now」规则（§1）的守卫会把显式拒绝误读为立即激活。选用显式的 `declined` 字段（而非复用裸 `enabled:false`），使其与延后激活状态区分开——后者同样是 `enabled:false`，但带 `activate_after`。
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
| Design 完成后过渡               | 若 `activate_after == "design"` 且当前 `enabled:false` → 翻 `enabled:true` 并加载本文件（激活无人值守）；已 `enabled:true` → 静默推进，不询问、不输出交接建议 |
| Plan 完成后过渡（新会话交接软停） | 已激活或本过渡点即将激活（`activate_after == "plan"`）→ 跳过交接建议（不输出交接命令块），翻 `enabled:true` 后静默推进到 Execute                 |

> 延后激活（`activate_after` 为 design/plan）在匹配过渡点由编排器翻 `enabled`；翻转后发送"无人值守模式已激活"通知。两条停顿路径（Design/Plan 过渡）均不靠人工应答推进。

#### task-init

| 停止点                    | 自动决策                                                                                                                         |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 现有任务选择（1a）        | 继续现有任务（对齐编排器单任务恢复）                                                                                             |
| 需求澄清（1b.1）          | quiet 下不调 AskUserQuestion：按最保守、最小范围解释自行假设并逐条记 `unattended-decisions.md`（任务文件夹未建则暂存内存、1f 落盘）；跳过纯文本确认、以假设的结构化理解直接推进 1b.2；关键歧义按 §8「低置信澄清问题」暂停（早于 1f 物化，按 quiet_mode 判定） |
| 头脑风暴补完（1b.2b）     | 低分默认进入（不询问，记 `unattended-decisions.md`）；非低分跳过                                                                 |
| 档位粗选（1b.3）          | 按推荐自动选择，不弹 AskUserQuestion                                                                                             |
| Dirty 文件                | 忽略，直接继续                                                                                                                   |
| 分支决策                  | 不询问，按 effective config `branch.mode` 自动决定（默认 `keep` = 留在当前分支）                                                 |
| worktree 隔离（1d-wt）    | 按已解析值自动决定（quiet 已在 1b.3 解析为 true/false，缺省 true；显式 true/false 直接生效），不进 `"ask"` 询问分支              |
| 新分支分叉告警（ISSUE） | 仅「创建新分支」路径触发——Unattended 分支决策默认「留在当前分支」故通常不触发；若触发则记录告警、不阻塞（NO_GIT/git 关闭亦跳过） |
| Linear issue 创建失败（1f checkpoint） | 不重试询问，自动跳过 Linear 集成继续                                                                                 |
| `/rename` 提示（post-1f） | 自动跳过提示：不停顿、不执行 `/rename`                                                                                           |

#### task-design

| 停止点                   | 自动决策                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| 联网调研门（Step 1.5）   | 不弹门：保守档默认跳过联网调研，仅当 `prompt.md` 显式要求外部调研时才跑；跑时给 `web-research` 引擎传 `unattended: true`（成本封顶、档位降级，见引擎「无人值守」节）。Headless 同样不弹门、按 prompt 信号决定跑或跳 |
| 澄清问题（Step 2）       | 多轮 subagent 自讨论（见第 7 节）；跳过确认循环的纯文本等待                              |
| 选择方案（Step 3）       | 按推荐选项自动选择（标注 "Recommended" 的，或综合判断的最优组合），Telegram 通知「自动选择方案：[方案名]」，不等待用户响应 |
| 每节确认（Step 4）       | 跳过每节用户确认，自我检查通过即继续下一节                                               |
| 配置面板（Step 2e）      | 合理时自动沿用已选 preset，明显偏离时按推荐值自动修正，不询问                            |
| 敏感度升级（Step 2e.2b） | 不弹面板，沿用 checkpoint（即使评估为高敏感）——与 2e.2 的 headless 短路一致，无头流程不在此引入交互 |
| 批准 design.md（Step 8） | 前置分支（不依赖是否执行 Step 7、不进入确认循环）：有 reviewer 时 C/I 过线（Critical = 0 且 Important = 0）自动批准；无 reviewer 轮次（Low）直接自动批准；均不等待纯文本确认 |
| Step 7 达 `max_rounds`   | 不询问，Telegram 通知后暂停（等待 `/task` 恢复人工决策）；`degrade_policy` conservative/headless 走 §9 A4 accept-with-findings 续跑（同点同 phase 至多一次） |

#### task-plan

| 停止点             | 自动决策                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Plan format        | 按 task-config.json 配置                                                                                                       |
| 3b 收敛后确认循环  | `Verdict == Approved` 直接推进 3c（跳过“是否有补充/继续”）；`Verdict == Issues` 修复后重跑一次，仍 Issues 则 Telegram 通知暂停 |
| 3b 达 `max_rounds` | 不询问，Telegram 通知后暂停（等待 `/task` 恢复人工决策）；`degrade_policy` conservative/headless 走 §9 A4 accept-with-findings 续跑（同点同 phase 至多一次） |

#### task-execute（Phase 4）

| 停止点                     | 自动决策                                                                    |
| -------------------------- | --------------------------------------------------------------------------- |
| Light 验证未配置           | 跳过验证                                                                    |
| BLOCKED（卡壳升级阶梯末端，≥3 次或架构级） | 重试一次（Opus）；按硬判据二选一——命中系统性问题（design 假设偏差 / 跨模块契约变更 / plan 任务边界需重划）→转 Revise，否则（局部实现卡点、非架构级）→Telegram 通知后 auto-cancel |
| NEEDS_CONTEXT 2 次后仍失败 | 视为 BLOCKED                                                                |
| 执行引擎                   | 按 `task_config.execution.mode` + `engine`                                  |
| codex dirty-conflict escalate（4a·D） | 同各模式统一 escalate（session 内可见停下 + 冲突报告，等 `/task` 恢复走 resolution menu），额外发 Telegram 远程通知（best-effort 叠加） |

#### task-test（Phase 5）

| 停止点                | 自动决策                                                                                                                                                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 验收清单（self_test） | 仅评估**可机判**验收项：可机判 MUST/SHOULD FAIL → 修复循环（重试一次 Opus），无解 → 暂停 + Telegram 通知人工（**非 auto-cancel**，见第 8 节）；不可机判人工项（MUST/SHOULD/MAY）→ 写入 acceptance-checklist.md 手动区、`→` 预填 `DEFERRED（待 task-end 后人工验收）`，**持久留痕**（不丢弃），交由 task-end Step 2.6 交还人工验收（design.md 无人工测试项则手动区为空）；全部可机判 MUST/SHOULD PASS（deferred 人工项不阻断）→ Telegram 通知（含 deferred 项数、自动推进到 Phase 6）→ 更新 phases.md DONE，推进 task-end |
| 验收清单（user_test） | 生成完整清单文件 → Telegram 通知（验收清单已生成到 acceptance-checklist.md，请填写后回复）→ 停止，等待用户                                                                                                                                        |
| 架构级问题判别（5d）  | §9 HARD-STOP：暂停 + Telegram（含问题描述 + 三选项），等 `/task` 恢复——不自动选向、不自动 Defer（避免静默吞掉架构偏差）                                                                                                                            |
| 累计新功能 STOP（≥3 或体量超 Execute） | §9 HARD-STOP：暂停 + Telegram（含累计计数 + 体量），等 `/task` 恢复——不自动续过蠕变门                                                                                                                                              |

#### task-end（Phase 6）

| 停止点                   | 自动决策                                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 验证命令未配置（Step 0） | 跳过配置询问，继续执行                                                                                                                                  |
| 多 open task 选择        | 选当前 session 最近更新（`Updated` 最新）的 open task；无法判定（无 phases.md 或时间戳并列）则 Telegram 通知后暂停，等 `/task` 恢复人工选择             |
| 验证失败                 | 重试一次（Opus 修复），仍失败 → auto-cancel + Telegram                                                                                                  |
| 债务对账（Step 1.5，§9 A3） | A 新债自动追加为 `- [ ]`；B 自动把**高置信**候选（本任务直接改动的文件/issue 命中的 open 项）标 `- [x] ... — resolved: <issue-id>`，低置信项保持 open；均写 `docs/debt.md`，不询问（conservative/headless 额外留痕见 §9 A3） |
| 人工验收交还（Step 2.6） | 有 DEFERRED 人工项 → **不阻断归档**（非 HARD-STOP）：DEFERRED 清单写入 final.md「待人工验收」子段 + Telegram 通知用户验收；无 DEFERRED 项则跳过、同现状 |
| CLAUDE.md 更新           | 自动更新，读 `end_decisions.claude_md`                                                                                                                  |
| 意外代码变更（Step 3.3） | 自动加入当前 commit                                                                                                                                     |
| 产物门控 FAIL（Step 3.3.7） | 补齐后核心仍缺失 → §9 HARD-STOP：**不归档**、停下 + Telegram 通知（含缺失清单）                                                                      |
| worktree merge 冲突（Step 3.4.4） | 不强 merge（保留 worktree + 分支、登记 `docs/unmerged-branches.md`），Telegram 通知冲突需人工                                                  |
| 分支处理 keep（ISSUE） | 追加 `docs/unmerged-branches.md` 登记（不提示）                                                                                                         |
| 分支处理（4 选项菜单）   | 读 `end_decisions.branch` 映射：`auto_merge`→Merge locally / `keep`→Keep as-is；**`PR` / `Discard` 永不自动触发（跳过）**；字段缺失或非法值 → 默认 keep |

> **`branch=keep` 下的验证口径**：代码变更活在任务分支 / worktree 内，主分支工作目录不含它——事后 / 外部验收（含 E2E 断言、人工抽查）须在**任务分支或 worktree 内**执行验证命令与产物检查，在主分支目录跑会得到「看起来没做完」的假阴性。流程内 P5 验证本就在 worktree 内跑，不受影响。
| 提交压缩 squash          | 读 `end_decisions.squash`（缺省 true）：`auto_merge` 合并用 `merge --squash`；main 连续提交段在守卫全通过时 `reset --soft` 压缩，任一守卫不过则保守跳过（见 git plugin P6.post-archive 1.5 + `<rule>`） |

#### task-cancel

| 停止点       | 自动决策           |
| ------------ | ------------------ |
| 取消原因     | 从调用上下文推断（BLOCKED / 验证失败 / 用户请求），不询问用户 |
| 处置方式     | Cancel（不 Defer） |
| 代码变更处理 | Keep（保留分支，供参考） |
| Process Review 改进建议（3.3b） | 自动写入 `{task-folder}/debt.md`，不讨论 |
| Feature 分支处理（3.5） | 保留分支（不删除，与 Keep 代码一致） |
| 取消完成通知 | 发送 Telegram `[task-name] 任务已取消：[原因]`（经 §4，Telegram 为 opt-in；未配置 / 插件未装则静默降级、不阻断取消流程） |

#### task-revise（Revise Cycle）

无人值守下单循环自动推进：根因分析后按需自动决定 design/plan 调整并 Telegram 通知；遇根本性问题自动转新任务，不靠人工应答。

| 停止点       | 自动决策           |
| ------------ | ------------------ |
| 步骤插入（RN-rootcause） | 按根因判据自动决定插入哪些步骤，Telegram 通知「根因：[结论]，本次将触及：[步骤]」 |
| 修订方案选择（RN-design） | 按推荐选项自动选择，Telegram 通知「自动选择修订方案：[方案名]」 |
| 任务列表确认（RN-plan） | 跳过确认等待，按生成的任务列表直接推进 |
| 根本性问题（Root-Problem Handling，RN-rootcause 判定或执行中新暴露） | 自动选「转为新任务」：commit WIP（`chore: WIP [DEFERRED Rn] <原因>`）、Revise section 标 DEFERRED 并记 WIP Commit SHA、创建后续任务的 `next-task-prompt.md`、Telegram 通知后停止当前 revise（不靠人工应答） |
| Chain Detection（R3+） | 自动选「拆分为新任务」，Telegram 通知后停止 |
| 执行卡壳 | 接 hatflow-systematic-debugging 定位根因；确为根本性问题 → 按上行 Root-Problem 处理（DEFERRED + WIP commit + 转新任务 + Telegram） |

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
| Linear API 失败   | 跳过，继续（不通知；含 task-init 1f checkpoint 创建失败——不重试、自动跳过） |
| 子 issue          | Cancel together      |

#### review plugin (`plugins.review.enabled`)

| 停止点           | 自动决策                          |
| ---------------- | --------------------------------- |
| Review 策略      | 按 `task_config.plugins.review.*` |
| Code review 确认 | 自动执行                          |
| Revise 触发      | 自动选择深度                      |
| 回归 review 不通过 | 自动触发新 R(N+1)（沿用原深度）；达 `max_rounds` 硬停 + Telegram，**不走 A4 续跑**（回归不通过 = Revise 未修好，不可 accept-with-findings） |

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

<rule>
无人值守模式下，澄清问题的答案来自外部来源（subagent）；即使答案看起来显而易见，主 agent 直接 inline 作答也不在范围内。
Reason: Self-Discussion Protocol 要求一个独立的视角。
</rule>

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

**执行环境前置（自动格式化 / 文件 watcher 竞争）：** 无人值守执行依赖「agent 是当前工作树的唯一写者」。worktree 隔离（headless 缺省 true）已隔离主树上编辑器的 format-on-save / watcher；但若有**直接监视任务工作树**的进程（保存即格式化、`tsc --watch`、dev server 热重载、非 git-hook 的 file watcher），它会与 agent 的 Edit 写入竞争、产生隐形改动与 diff 漂移（Aider/OpenHands 同类坑）。启动无人值守前确保此类进程不监视任务工作树——git plugin 在 commit 时跑的格式化 hook 是预期内的、不在此列。

---

## 9. Degrade Policy（撞卡点分级处理）

`unattended.json` 的 `degrade_policy` 决定无人值守撞到「可逆/可降级卡点」时的处理强度。**非无人值守模式恒按 `standard`**（与改造前逐字等价，向后兼容）。

| 卡点 | `standard`（缺省=现状） | `conservative` | `headless`（后续） |
|------|------------------------|----------------|--------------------|
| A4 design/plan review 达 `max_rounds` 不收敛 | 暂停 + Telegram 通知（§6/§8） | **accept-with-findings 续跑**：剩余 findings 原文写 `## Unresolved Review Findings`（design.md / plan.md）+ `unattended-decisions.md`，续跑；**同点同 phase 至多一次**——判重读 `unattended-decisions.md` 的 `## Headless Degraded Decisions` 段，该「卡点+phase」键已有一条 AUTO-DEGRADE 记录即视为已用过、第二次退回 `standard`（暂停）。design/plan/revise 三处统一用此判重。兜底：P4 review + P5 验收双网 | 同 conservative + 全局 degrade_budget |
| A3 task-end 债务对账 | 现降级 + 高置信关/低置信留（仅 final.md 记「疑似解决待人工确认」，无额外留痕） | 维持现降级 + 关闭动作 / 低置信疑似项汇总进 `unattended-decisions.md`，final.md P6 引用 | 同 conservative + degrade_budget |
| A2 user_test | 停（按 task_type） | 停 | 转 self_test + deferred（后续） |

### 强制留痕（conservative / headless）

每次 AUTO-DEGRADE 必须留痕：

- `unattended-decisions.md` 追加 `## Headless Degraded Decisions` 段，逐条记「卡点+phase 键（判重用）/ 原文 findings / 自动决策 / 时间」。该段即「同点至多一次」的判重载体（A4 第二次撞同键即退回 standard）。
- final.md（task-end P6）汇总引用这些降级决策，使人工回看可见。

### HARD-STOP 硬下限（任何 degrade_policy 都不自动续，必停）

<rule>
以下是任何 degrade_policy 都不会自动越过的 HARD-STOP 点——每一处都暂停（Telegram 通知）并等待人工：分支 PR/Discard 决策、git 操作失败、验证命令崩溃、可机判的 MUST/SHOULD 验收 FAIL、artifact gate FAIL、多个并行 open task、Test phase 架构性问题分流（5d）、累计新功能蔓延 gate、以及编排器状态文件（phases.md）损坏。
Reason: 这些都是不可逆或高风险的——自动越过它们可能销毁工作（discard）、交付坏代码（验证崩溃 / MUST FAIL）、损坏任务状态（artifact gate / phases.md 损坏），或静默吞掉一个需要人工重新界定范围的范围/架构偏离（5d 分流、creep gate）。分级降级只适用于可逆/可降级的点（review 不收敛、债务清算）；这道硬底线不容妥协。
</rule>

- **人工验收交还（task-end Step 2.6）非 HARD-STOP**：DEFERRED 人工测试项不可机判，不在「可机判 MUST/SHOULD FAIL」硬下限之列；无人值守下 deferred + final.md「待人工验收」留痕 + Telegram 通知用户，归档照常推进、不阻断（HARD-STOP 仅拦截可机判的 MUST/SHOULD FAIL）。
- A4 的「续跑」仅适用于 **design/plan review 不收敛**（可逆——findings 留痕、P4/P5 双网兜底）；**绝不**适用于上方 HARD-STOP 清单。
- `degrade_policy` 缺省（字段不存在）或为 `standard` 时，A4/A3 走原暂停路径——现有任务零行为变更。
