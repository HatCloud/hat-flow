# Changelog — task suite

task 套件全体 skill 的修订/回溯日志（合并自原各 skill 的 `references/changelog.md`）。**不注入上下文，最新在最上，按 skill 分节。** 仅在真正改了 skill 定义时写一条，非每轮运行流水。

> orchestrator（`task`）为唯一 self-evolving 技能，其后续自进化 changelog 写入本文件的 `## task (orchestrator)` 节顶部。其余 skill 为编排 worker，历史条目保留于此、归档只读。

---

## task (orchestrator)

### 2026-06-17 Telegram 通知发送链路修正 + chat_id 配置分层（个人隐私护栏）

**触发**：归档任务 `2026-06-17-todo-sync-dogfooding` 跑完后，self_test 模式下 unattended.json.telegram_chat_id 始终为 null，所有无人值守通知静默降级；追查发现 3 处叠加问题：

1. **UNATTENDED_PROTOCOL §4 发送工具假设错位**：写"由 companion 插件 `mcp__plugin_telegram_telegram__reply` 工具发送"——`reply` tool 是 reply 到具体 message_id（用于入站消息回复），不适合无人值守的 broadcast 通知（无入站消息）。修正为直接调 Telegram Bot API（`curl https://api.telegram.org/bot<token>/sendMessage`），通知链路与 MCP plugin 解耦（plugin 仅承担 access control / 配对）。
2. **chat_id 配置路径不明**：探测优先级 §3 只写"task-defaults.json"，没说"个人 local 配置"和"分发版污染"两层；新增 4 级优先级（session 上下文 → personal local → 全局 → null）+ `<rule>` 守隐私（chat_id / bot token 任何 hardcode 进仓库源文件都污染 hat-flow 分发版）。
3. **task-setup Step 5 引导缺关键一步**：原本只让用户跑 `/telegram:configure` 配对，配对完无法在 CLI 启动会话里发通知（无 session 上下文）。新增"写入 chat_id 到 `~/.claude/task-defaults.local.json`"的具体 bash 命令段，从 `access.json.allowFrom[0]` 读出本人 chat_id，合并入 local config（chmod 600）。

**同步改动**：
- `task-defaults.json` + `.example`：顶层新增 `telegram_chat_id: null` 字段 + `_telegram_chat_id_note` / `_telegram_chat_id_setup` 注释（说明 null 语义、覆盖路径、获取方式）。默认 null 保持 opt-in。
- 降级告警格式：`[notify] ...` → `★ ...`（更显眼）+ 每条告警给具体配置入口而非笼统"chat_id 不可用"，便于用户立即知道在哪改。

**不动**：MCP plugin 本身 / hat-flow plugin 仓库结构 / 现有 .tasks 归档格式。

**验证**：dogfooding 跑了一次完整 Bot API curl 发送（chat_id=6457159333, token 从 `.env`）→ API `ok:true`、message_id=203、收件人 Jeff Chi (@hat_cloud)；access.json dmPolicy 由 pairing → allowlist（本人 lockdown）；未写 `task-defaults.local.json`（user 选择暂不写全局默认值）。

### 2026-06-17 worktree 跨 session 回切 Step 2B.0 (M2)

- Step 2B 新增 **2B.0 Worktree 回切**：选定 open task 含 `worktree` 指针（hat-task-detect 从主仓库 stub 读出）且 CWD 不在 worktree 内时，`EnterWorktree(path=)` 切入后重新 detect 定位真实任务文件夹；指针失效 → 交互询问 / 无人值守暂停通知。
- 配套：`hat-task-detect` 新增 `worktree` 字段（读 `.worktree` stub 指针）；task-init 1d-wt 物理创建（`git worktree add -b task/<folder> ... HEAD` + `EnterWorktree(path=)`）；task-end 3.4.4 teardown。

### 2026-06-17 无头模式入口 Step 0 + 三层配置 + degrade_policy (M1)

- 新增 **Step 0（Quiet Mode & Flag Parsing）**：入口统一解析 `$ARGUMENTS`，由显式信号（`-q`/`--quiet`/`--headless`/「无人值守」）确立 `quiet_mode` 与 `flag_overrides`；实测无稳定 headless 自动信号（交互会话亦 `ENTRYPOINT=cli` + 非 TTY），故 `<rule>` 禁止 auto-probe 翻转、显式信号为唯一契约。
- 顶部 Unattended Mode note 改为指向 Step 0（统一入口）；quiet 入口由 task-init 1f 物化 `unattended.json`，Step 2A.1 降为后备。
- `UNATTENDED_PROTOCOL.md`：§1 加 `degrade_policy` 字段、§5 加 Quiet 入口、新增 **§9 Degrade Policy**（standard/conservative/headless 分级 + 强制留痕 + HARD-STOP 硬下限）。
- 配套：`task-defaults.json`(+`.example`) 新增顶层 `branch`/`headless`/`end_decisions` 段；新脚本 `bin/hat-task-config-resolve`（三层确定性合并 + worktree "ask" 哨兵解析）。

### 2026-06-16 自进化过程准则改为注入受管 self-evolution.md

- 删手写自进化节、改 `!cat` 硬注入受管副本 `references/self-evolution.md`（防漂移）；changelog 改为仅改 skill 才写、非每轮流水。task 专属归属补充（编排决策点判据 / 不另建 series 经验库）保留在正文。

### 2026-06-15

- 启用编排级自进化：frontmatter 加 `self-evolving: true`；Runtime Context 增加 `references/lessons.md` 注入行（`!`cat``）；过程准则新增「## 自进化（收尾 Dogfooding）」节（裁决漏斗 / 写入闸 + 归属判据 / 整合触发，规则以 spec-skill Self-Evolution 为单一来源）。
- 新建 `references/lessons.md`（编排决策类经验库，表格化 + 硬上限 ≤15，头部记「上次整合」）、`references/lessons-archive.md`（冷归档，永不注入）、`references/changelog.md`（本文件）。
- 修复 README.md 悬空引用：删除子协议表中 `PROCESS_REVIEW_TEMPLATE.md` 一行（该文件在 task/ 不存在）。

---

## task-init

### 2026-06-17 1f 物化 end_decisions.squash + git plugin 记 base_ref

- 1f headless unattended.json 的 end_decisions 增 `squash`（缺省 true）。
- git plugin P1.phase-start 新增：把任务起始 HEAD 记到 `{task-folder}/.git-base-ref`，供 End 阶段 main 连续提交段 squash 定位起点。

### 2026-06-17 1d-wt Worktree 物理隔离创建 (M2)

- 新增 `1d-wt. Worktree Isolation`：读 `branch.worktree`（true/false/"ask"），交互模式 "ask" 追加询问；启用时 `git worktree add -b task/<folder> <path> HEAD`（主目录 HEAD 不动）+ 内置 `EnterWorktree(path=)` 切入；`<rule>` 禁止主目录 `git checkout -b`。
- 1f：worktree 启用时经绝对路径 `$MAIN_ROOT` 写主仓库 stub 指针 `.tasks/open/<folder>/.worktree`（跨 session 恢复用）。NO_GIT 跳过 1d-wt。

### 2026-06-17 三层配置合并 + 无头物化 + 分支默认 keep (M1)

- 1b.3 第 5 步改为调用 `hat-task-config-resolve`（默认模板 ① < 全局 local ② < 项目本地 ③ < 调用 flag ④ 深合并 + `branch.worktree` "ask" 哨兵按 quiet 解析），替代原「读 preset 模板深合并」substep；保留裁剪覆盖与 auto 解析。
- 1d 分支决策：读 effective config `branch.mode`（默认 **keep** = 留当前分支，支持同目录多 task 协作）；Iron Law 加 quiet/unattended 例外（按 config 不询问）；worktree 物理隔离与交互追问拆到 `1d-wt`（M2）。
- 1f：quiet_mode 时物化 `task-config.json` 顶层 `_source:"headless"` + 直接写 `unattended.json`（`enabled:true, activate_after:now, degrade_policy, end_decisions`），使 Init 后全程无人值守。
- Dependencies 增 `hat-task-config-resolve` 脚本、`unattended.json` 写、三层配置读源。

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Bilingual Strategy / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **SKILL.md 补 Red Flags 表**：预判 init 阶段越界探索 / 跳过需求确认 / 自动建分支 / 跳过 tier 确认等合理化失败模式（全英文，符合双语策略）。
3. **README.md 去掉「worktree」措辞**：SKILL.md 1d 实为 `git checkout -b`，无 worktree。「设置 git 分支或 worktree」改为「设置 git 分支」。
4. **双语：中文章节标题改英文**——`### 1b.3 档位粗选` → `### 1b.3 Tier Pre-Selection`；`### 1b.4 Debt 关联检查（轻量）` → `### 1b.4 Debt Linkage Check (Lightweight)`，与同文件其余英文标题统一（Resume Support 中文对照行保持不变）。

---

## task-design

### 2026-06-19 新增「视觉/语义决策用 preview」rule

设计期遇图标/emoji、命名格式/缩写、键位、文案、布局等视觉/语义选择，要求在 Step 2 澄清用 AskUserQuestion preview 一次收敛、写进 design.md，不留到实现期凭文字反复试。来源：retrospective of 2026-06-18-tmux-agent-restore（此类选择在 P5 花了 ~25 轮 AskUserQuestion）。

---

### 2026-06-18 强化 codex-first 派发护栏（Step 7）

- Red Flags 加一行 + Step 7 reviewer 解析处加 `<rule>`：reviewer 解析为 codex（auto+codex-check READY 或显式 codex）时**必须**走 review.md codex 分支；降级 native 仅限 hard fallback（联网/沙盒/quota/`FALLBACK:`）且**每次必记** `fallback-log.jsonl`，"native 更简单/更快"不是合法理由。
- 动因（dogfooding）：一次真实运行解析为 codex 却为图快派了 native design-reviewer、未记 fallback，静默降低 review 深度；改走 codex 后挖出 2 个 Critical（native 多半漏）。未记的降级会掩盖"配置的 reviewer 从未真正跑过"。

### 2026-06-17 Step 7 max_rounds A4 分级续跑 (M3)

- Step 7 max_rounds 退出的 [Unattended] 分支按 `degrade_policy` 分流：standard/缺省=暂停（现状）；conservative/headless=A4 accept-with-findings（剩余 findings 写 design.md `## Unresolved Review Findings` + unattended-decisions.md，续跑；同点至多一次，第二次退回暂停）。见 UNATTENDED_PROTOCOL §9。

### 2026-06-17 Step 2e headless 短路 (M1)

- Step 2e.2 加 `_source == "headless"` 最先判断：无头物化的 config 永不弹偏离面板，复杂度评估仍跑、结果写 2e.3 design.md 策略段。
- Activation Timing 守卫补注：`enabled:true` 含 quiet 入口 1f 物化的 headless 状态，跳过激活询问。

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **README.md 核心流程第 2 步对齐 SKILL.md Stop Points**：「提出澄清问题（每次一个）」与 SKILL.md「合并提问（最多 4 个）」不一致，改为「合并提问（最多 4 个）」；「关键规则」中的「每次只问一个问题」一并删除。

---

## task-plan

### 2026-06-17 3b max_rounds A4 分级续跑 (M3)

- 3b max_rounds 退出的 [Unattended] 分支按 `degrade_policy` 分流：standard/缺省=暂停（现状）；conservative/headless=A4 accept-with-findings（剩余 Issues 写 plan.md `## Unresolved Review Findings` + unattended-decisions.md，续跑；同点至多一次，第二次退回暂停）。见 UNATTENDED_PROTOCOL §9。

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Bilingual Strategy / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **README.md 核心流程重写对齐 SKILL.md SC2 二元契约**：原描述「Reviewer subagent review（Low 0 轮，Medium 1+条件第2轮，High 2轮）」与「确认执行模式 + TDD 策略」均与 SKILL.md 不符——前者属过时的分层轮次矩阵（SC2 实为单个 plan-reviewer、single-pass、Verdict 二元、不算轮次矩阵），后者属 Phase 2 职责（plan 阶段无此停点）。两者均删除/重写。
3. **双语：中文章节标题改英文**——`### 3b. Plan 忠实度评估` → `### 3b. Plan Fidelity Review`；`### 3c + 3d: P3.phase-end（...）` → `### 3c + 3d: P3.phase-end (Timestamp + Commit + Linear Sync)`（Resume Support 中文对照行保持不变）。

---

## task-execute

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 对齐 hook 化后的实际流程：删除已脱节的「Code Review Light（Medium/High 必做）」「Commit Guidelines 内联」表述，改述为 P4.per-task-post / P4.post-execute hook 驱动。
  - SKILL.md 4a mode fallback `<rule>` 正文改英文（Reason 保留中文），符合双语策略。

---

## task-test

### 2026-06-19 5d 增「累积范围守卫」rule

测试期新需求常增量涌现、每条都小但累积让 Test 变第二个 Execute。新增 rule：累计接纳 ≥3 项新功能（非 bug 修复）或新功能改动量超过本 task Execute 时，STOP 提示拆新 task / Revise / 继续。来源：retrospective of 2026-06-18-tmux-agent-restore（P5 占 42% output > P4 35%）。

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 准确性修正：删除 worktree 残留与 `5e` 引用，对齐 SKILL 的 5a/5b/5c/5d。
  - 去冗余：「Test 为硬停、不自动推进 Phase 6」原约 4-5 处重述，保留一处权威 `<rule>`（Test 完成 → 过渡）+ 末尾 trailing reminder，其余改为单行交叉引用。
  - Dependencies 补注 `P5.post-acceptance` 的 linear hook 交接契约。

---

## task-end

### 2026-06-19 retrospective 提为显式门控（Step 3.6 + HARD-GATE）

post-archive hook 把 git + retrospective 一起输出，长输出下 retrospective 段易被截断/漏跑。新增 Step 3.6 + HARD-GATE：retrospective 启用时其流程审查必须在 Step 4 前独立完成，不等同于「跑了 hook」；Step 4 清单加对应项。来源：retrospective of 2026-06-18-tmux-agent-restore（归档时 retrospective 被漏跑）。

### 2026-06-17 End 提交压缩 squash（end_decisions.squash）

- 新增 `end_decisions.squash`（task-defaults.json + .example，缺省 true；三层/flag 可关）。
- **场景①分支→main 合并 squash**：core 3.4.4 worktree teardown 的 `auto_merge` 与 git plugin P6.post-archive「Merge locally」均按 squash 开关用 `git merge --squash`（+ `branch -D`）/ 原 `--no-ff`。
- **场景② main 连续提交段 squash**：git plugin P6.post-archive 新增 1.5 步——已在 main 时把 `base_ref..HEAD` 用 `git reset --soft` 压成单 commit，**守卫全过才执行**（base 是祖先 / N≥2 / 无 merge / 全未推送 / 仅本 open task），任一不过保守跳过 + final.md 记因；`<rule>` 禁止存疑时改写历史。base_ref 由 git plugin P1.phase-start 记录到 `{task-folder}/.git-base-ref`。
- 命令序列已在 scratch repo 验证（merge --squash → base+1；reset --soft → 3 提交合 1、文件全留）。

### 2026-06-17 Step 1.5 债务对账 A3 留痕 (M3)

- Step 1.5 [Unattended] 债务对账按 `degrade_policy`：conservative/headless 额外把自动关闭动作 + 低置信疑似项汇总写 unattended-decisions.md `## Headless Degraded Decisions` + final.md P6 引用；standard/缺省维持原行为。见 UNATTENDED_PROTOCOL §9 A3。

### 2026-06-17 Worktree Teardown 3.4.4 (M2)

- 新增 `3.4.4 Worktree Teardown`（核心，仅 worktree 任务）：检测 linked worktree（`--git-dir != --git-common-dir`）；归档后先 `cp -R` 任务文件夹回主仓库 + 删 stub（防 untracked `.tasks/` 随 worktree 删除而丢记录），`ExitWorktree(keep)` 回主目录，按 `end_decisions.branch` auto_merge（`git merge --no-ff` + `git worktree remove` + `git branch -d`）/ keep（登记 unmerged-branches.md）；PR/Discard 永不自动。回主目录后 3.5 git-plugin 分支处理自然 no-op，不重复。
- `<rule>`：merge 前必先物理拷贝 + ExitWorktree(keep)；未 merge 不强删 worktree（HARD-STOP 类）。

### 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 修正悬空引用：删除 PROCESS_REVIEW_TEMPLATE / Part A 引用（文件不存在），改述为 P6.post-archive 的 hook 驱动 retrospective。
  - 去冗余：「phases.md Phase 6 DONE + P6 phase_end 必须在归档 commit 之前」原三处重述，保留 Step 3.3.4 的权威 `<rule>`，其余两处改单行交叉引用。

---

## task-revise

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 重写 `README.md` 使其与 SKILL.md 的新模型一致：删除旧的「mini design→plan→execute 子流程 / Mini 三段式」表述，改为「自适应单循环、无 Full/Partial/Lite 档位、design/plan 按需」。

---

## task-cancel

### 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 族内契约对齐：`Unattended State` 步骤改为从 phases.md 所在路径解析 task-folder（与 task-revise 一致），不再用 `{open[0].path}/unattended.json`，避免多任务取错状态。
  - Dependencies 一致性：README 去掉不存在的 `PROCESS_REVIEW_TEMPLATE.md` 引用（Process Review 由 retrospective 插件 hook 承载）与未实际使用的 `spec-git` 引用（commit 规范由 git 插件提供），与 SKILL Dependencies 取齐。

---

## task-reopen

### 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 删除 `README-zh.md`（双 README 违反单一性/ASCII 约定），保留单一 `README.md`。
  - `README.md` 与 SKILL.md 对齐：Linear 状态更新改述为经 `statusMap` + `get_status_map` 解析、无硬编码 UUID；依赖段去掉硬编码 `mcp__linear__update_issue`，改引用 `plugins/linear.md` 规范。
  - 补 SKILL.md 的 Red Flags 表。

---

## task-setup

### 2026-06-18

- Step 5（Telegram 通知）重构为「配齐通知所需的全部字段」：
  - 原版只引导 `chat_id`、把 token 当作 `/telegram:configure` 的隐式副产物；现显式列出两字段（`TELEGRAM_BOT_TOKEN`→`.env` / `telegram_chat_id`→local）及落点表。
  - 明确通知与插件**解耦**：不装插件也能发（curl 直连 Bot API），给出 `@BotFather` 手动拿 token 写 `.env` 的纯通知路径。
  - 验证步骤覆盖**两个字段**（原只验 chat_id），缺一即静默降级。
  - 背景：telegram 插件因 bun 进程泄漏被全局关闭，暴露「通知靠插件副作用拿 token」的脆弱假设；UNATTENDED_PROTOCOL.md §4 同步改为 curl 前显式 source `.env`。

### 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 补 SKILL.md 的 Red Flags 表。
  - `README.md` 的「核心职责」由逐条镜像 SKILL 步骤收敛为「目的+触发+关键规则」提炼。
