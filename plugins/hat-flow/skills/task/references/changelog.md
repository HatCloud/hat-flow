# Changelog — task suite

task 套件全体 skill 的修订/回溯日志（合并自原各 skill 的 `references/changelog.md`）。**不注入上下文，最新在最上，按 skill 分节。** 仅在真正改了 skill 定义时写一条，非每轮运行流水。

> orchestrator（`task`）为唯一 self-evolving 技能，其后续自进化 changelog 写入本文件的 `## task (orchestrator)` 节顶部。其余 skill 为编排 worker，历史条目保留于此、归档只读。

---

## 2026-07-08 Codex 批⑤——linear MCP 记法、task-setup Codex 指引与 UNATTENDED 能力声明

**为何**：linear 插件与 task-setup 的 `mcp__linear__<op>` 为 Claude 宿主暴露名直呼，改 `linear:<op>` 中性记法 + 顶部记法声明（宿主暴露名归 harness-tools.md「调用 Linear MCP 的 <op>」行）；task-setup 增 Codex `config.toml` Linear 配置指引；UNATTENDED_PROTOCOL 顶部声明宿主能力清单指路（不支持的 harness 交互降级）。

---

## 2026-07-08 Codex 批④——注入行兜底泛化 + 承重站点 inline 防线

**为何**：`!` 注入行仅在 Claude 侧技能激活时展开；协议承重站点（各 phase Runtime Context、DESIGN_PROTOCOL/PLAN_PROMPT 嵌入）在 Read 路由 / Codex 原生加载下静默缺失即整段流程丢失。泛化既有兜底 rule 为「任何加载路径」，并在 7 个站点文件就地加 inline 兜底句（共 9 处——task-design/task-plan 各含 Runtime Context 与协议嵌入两站点；一级防线，不依赖远处 rule）；task-end 无注入行、无需站点防线。

---

## 2026-07-08 Codex 中性化批③——harness 变量与 CLI 直呼收编映射

**为何**：`claude -n`/`claude -p` 命令模板与 `$CLAUDE_CODE_SESSION_ID` 写入模板是 Claude 专属可执行配方，正文直呼阻碍多 harness 共享树。收编进 `harness-tools.md`（新增「斜杠命令触发」「无头驱动」两行、扩「会话标识」「新会话交接」两行的 Claude 列），orchestrator/task-init/headless-driving/evals 正文改为动作 + 指路，判定算法与 graceful 语义原样保留。另：UNATTENDED_PROTOCOL §7 补 Requirements Analyst 的 Claude 落点括注（general-purpose，T4 review M2 携带修补，主题属批②、随批③落盘记账）。

---

## 2026-07-08 Codex 中性化批②——子代理派发与模型档位直呼替换

**为何**：继续移除 task workflow 正文中的 Claude-Code-only 派发语法与本项目内部 Sonnet/Opus 档位直呼，改用 `harness-tools.md` 的子代理派发与模型档位中性动作词，保持 Codex 兼容。

- **task 套件派发语句中性化**：`review.md`、`task-design`、`task-execute`、`execute-workflow.md`、`UNATTENDED_PROTOCOL.md` 中的 `subagent_type` / `run_in_background` / `Agent tool` / `general-purpose` 直呼改为「派发只读 reviewer 子代理 / 后台派发 / 非后台子代理」等中性动作短语，保留 C=0 & I=0、`max_rounds`、JOIN 与 HARD-GATE 语义。
- **模型档位中性化**：设计 / 执行 / review 矩阵与无人值守升级路径改用「常规档 / 加强档」并指向 `harness-tools.md` 的 Claude 档位映射；`agents/design-reviewer.md` 正文同步，frontmatter 原样保留。

## 2026-07-08 Codex 中性化批①——交互/清单/续接/worktree 工具直呼替换

**为何**：批量替换 AskUserQuestion/TaskCreate/TaskUpdate/TaskList/TaskGet/SendMessage/EnterWorktree/ExitWorktree 等 harness 专属工具直呼为 harness-tools.md 定义的中性动作短语，为 Codex 引擎兼容铺垫。

- **task 套件正文中性化**：`${CLAUDE_PLUGIN_ROOT}/skills/task/`、`skills/task-*` 中的交互停点、TODO sync、review 续接、worktree 切入/退出等说明改用「向用户提问（结构化选项优先）」「维护进度清单」「定向续接某代理」「进入/退出隔离工作树」等中性动作短语，保留原 HARD-GATE / 停点 / 派发语义与祈使强度。
- **入口映射提示**：orchestrator 与各 phase `SKILL.md` 开头补工具落点映射提示，统一指向 `references/harness-tools.md`。
- **特殊口径**：`PLAN_PROMPT.md` 示例组件名由 `TaskList` 改为 `TaskBoard`；`references/todo-sync.md` 改为动作短语 + harness-tools.md 落点指针，避免机制文档继续直呼宿主工具。

## 2026-07-08 Codex harness 动作映射表新增（hatflow-codex-port Task 2）

**为何**：多 harness 支持场景下，工具落点需要一个唯一权威来源，供后续中性化批次引用，避免把 Claude Code 专属工具名继续写进行为承重正文。

- **新增 `references/harness-tools.md`**：新建动作词表到 Claude/Codex 双列落点的映射文件；首条规则按 A8 spike 实测记录双路径 token 的 Codex 解析快路径与 EH #9 兜底，后续行覆盖提问、进度清单、代理派发 / 续接、worktree、新会话交接、套件脚本、Linear MCP、会话标识、模型档位、`!` 注入行、无人值守模式等 canonical 动作短语。

## 2026-07-08 Plan→Execute compact 软停改新会话交接 + P4 阻塞交互收口（skill-revise 定向修订）

**为何**：用户反馈 ① compact 软停体验差——compaction 有损且残留上下文继续计费，任务状态本已全量落盘，新会话恢复更干净；② plan 之后应尽量不再问用户（spec-task-skill 约定 9），但 review/tdd 插件在 P4 仍留有 3 处阻塞交互；③ full 档 P4 逐 plan task TODO 展开在 resume 后退化为 4a/4b 两行。

- **task (orchestrator) SKILL.md**：Step 3 步骤 2「Compact 建议」整块替换为「新会话交接建议」——触发条件 / 前置门 / Hotfix 例外 / phase_merge 降级原样保留，输出可复制命令块 `cd {项目根} && claude -n "{task-folder-name}" "/task 继续任务…先读 phases.md 与 task-config.json…"`，回「继续」仍可留在当前会话（软停语义不变）；过渡类型表、HARD-GATE、[Unattended] 段措辞同步。Step 1 多 open tasks 分支新增 `$ARGUMENTS` 子串唯一命中 → 直选不询问（交接命令自带任务名，新会话恢复不多问）。
- **UNATTENDED_PROTOCOL.md §6**：两行停止点措辞 compact→交接，自动决策语义不变。
- **plugins/review.md 收敛循环**：触发判据两模式统一（≥1 Critical 或 ≥2 Important 自动修复进循环，不弹 AskUserQuestion，修复内容 session 内可见）；达 max_rounds 改「可见停下 + 报告」终态（对齐 task-execute escalate A2 先例），处置菜单挪到 `/task` 恢复时经 4b 分诊触发。删除了 Interactive「修复前 AskUserQuestion 确认」（约定 9 P4 零阻塞合规修复）。
- **plugins/tdd.md RED 异常**：[Interactive] AskUserQuestion 阻塞问改所有模式统一「可见停下 + 异常报告」，处置经 `/task` 恢复决定，Telegram 保持 best-effort 叠加。
- **references/todo-sync.md Bootstrap 行**：full 档加 Execute 例外——step 重建按 task-execute 的 plan.md 逐 task 展开规则，不用 phases.md 4a/4b 粒度（修复 resume 后 step 级进度退化；新会话交接落地后 P4 常从 resume 进入，此走样会常态化）。

波及机械换词：task-init/design/plan/test/execute 的 transition rule 与 spec-task-skill 约定 1/2 中「compact」机制名 → 「新会话交接」（各技能自有 changelog 各记一条）。指「上下文被压缩」这一客观事件的 compaction 引用（task-plan 提交 rule、task-execute 4b 分诊、review.md agentId 恢复）不属本机制，保留。

## 2026-07-07 word-budget 档位声明回填（2026-07-07 预算三档制）

依据 2026-07-07 Length Budget 三档声明制回填 task 套件各 skill 的 frontmatter `word-budget`：`task`（编排器）声明 `exempt`；`task-init`/`task-execute`/`task-end`/`task-design`/`task-test`（多阶段流程 + 生命周期一体型）声明 `2000`；`task-plan`/`task-revise`/`task-cancel`（多阶段流程但下沉已做完）声明 `1000`。均属既定 WARN 瘦身队列成员，声明不改变正文内容。

## 2026-07-07 ISSUE：机读状态信号 state.json + 外部驱动契约（headless-state-signal 任务）

经完整 6-phase 任务流落地（design 1 轮 R1/R2 review：10 Accept 1 Reject；plan review codex 真跑 1 轮）：

- **新增 `bin/hat-task-state`（+11 pytest）**：任务级 `state.json` 写入器——三态（running/waiting_input/terminal）+ `resume_hint` 机械消费枚举 + `outcome`；原子写、schema 自校验；`stamp` 子命令作 Stop hook 按 session_id 匹配盖 `stopped_at`（实证：交互与 `-p` 无头模式均实时触发）
- **新增 `references/headless-driving.md`**：外部驱动契约唯一权威（schema、五分支判定算法、stopped_at 必要不充分语义、900s/600s 坑、resume 循环、stream-json、回退路径、stop_point 开放词表）
- **编排器接线**：Step 2B/Step 3 戳 running；新增全 phase 共用停点写入 `<rule>`（等待用户输入的回合结束前先戳 waiting）；task-end/cancel 归档前戳 terminal（先戳后移）
- **8 个 phase skill 停点表下各一行薄指针**；UNATTENDED_PROTOCOL 头部指针；settings.json hooks.Stop 注册 stamp
- 来源：E2E 首跑 friction 1/4（ISSUE）

## 2026-07-07 E2E 首跑后固化：无头模式两处协议语义补全（skill-revise 直改例外，实测证据 + 用户确认）

来源：E2E 回归首跑（`plans/e2e-run-1/`）实测发现，经主会话核实实现后固化：

- **§3 chat_id 探测新增「显式关闭短路」**：项目本地 `telegram_chat_id: null/false` = 显式禁用、短路整条探测链（区分「显式禁用」与「字段缺失」）。实测：探测链第 2 步直读 personal local、不经三层 resolver，项目层 null 压不住——测试床无法屏蔽真实 Telegram 通知。
- **§6 task-end 补 `branch=keep` 验证口径**：事后/外部验收须在任务分支/worktree 内执行，主分支目录会假阴性。实测：E2E-2 断言 grep subtract 在主床 miss、切任务分支才 PASS。
- 另两条 E2E 发现（无头状态信号 + 外部驱动契约文档）属新功能设计，转独立任务处理（见 task lessons 建议出口=新任务条）。

- **hook 引擎（bin/hat-plugin-hook）**：删 `after` 依赖校验与重排机制（~27 行）——零插件使用、零测试覆盖、代码自注「当前无插件使用 after」；handler 排序只按 priority。golden 零变化。
- **git 插件**：删 frontmatter 空 `recommend_disable_when`/`recommend_enable_when` 占位键（其余插件均有实值，空列表无消费意义）。
- **保留（偏离诊断，理由记 plans §5）**：hotfix 档位（声明式 preset 数据、公开 4 档契约）；degrade_policy headless 档「后续」标注（诚实标注的未实现项）。诊断中另一处规则错配项经查已在前批清零。3c review JOIN 协议实测并入最终 E2E 阶段。

## 2026-07-06 批次 2b：lessons 固化（实验子集，2 条候选双双中性，正文零改动）

skill-revise Phase 3.5 对比实验（基线/改前/改后三臂 × 3 模型 × 3 轮，Opus+Sonnet+MiniMax-M3 池化，总费 $9.51）——改造后机制 B（基线臂预检）/C（候选老化计数）/E1 首次实战：

- **编排器「新任务信号路由分支」（ISSUE F1）**：三臂 9/9 全 pass——现行「1 open task→Resume」文本在 fresh-context 下不误导任何 worker，**中性×2 → 移入 lessons-archive**（不再重测；真实事故证据保留，可依协议例外手动强制固化）。ISSUE 的误续属长上下文注意力稀释，非文本缺陷。
- **task-init「rubric 判定锚点」（ISSUE F3）**：基线臂 0.33 fail（题有区分度）、改前/改后均 9/9——无锚点 rubric 对明显糟糕的 prompt 同样稳定，**中性×1 → 留 lessons 待重设计**（需换贴判定边界的 borderline prompt 才测得出锚点增量）。
- **中性复盘表**：

| 候选 | 首次中性原因猜测 | 重设计后结果 |
|---|---|---|
| 编排器新任务路由分支 | ×1 轮疑选项泄漏；×2 轮实景路由题仍中性——模型基线已覆盖该判断 | 中性×2，归档 |
| task-init rubric 锚点 | 测例 prompt 离判定边界太远（明显糟糕），两臂天花板 | 待重测（borderline prompt） |

- 有区分度的 B 题沉入 skill-test prompt-bank（含「对锚点增量无区分度」教训注记）。
- 顺手修真实 bug：claude CLI 新版把 ⚠ auth 横幅打进输出、事件数组形态——claude-dispatch 收集器解析失败致全批报错；修复 + 回归测试（bin/test_claude_dispatch.py +1）。

## 2026-07-06 批次 2b：lessons 固化（直改子集，13 条事故实证 + 2 条移出）

来源：7 份 lessons.md 积压 17 条，经用户确认走「真实事故 > 测题区分度」直改例外（批次 0 先例）。剩 2 条（编排器新任务路由、init rubric 锚点）走 skill-revise 实验路径。

- **task-init**：1f 补 scaffold 勿传 --help；1d-wt 增同树并发守卫（≥2 open task 共享树 → ask 分支推荐翻转为 worktree 隔离，ISSUE 三处串扰实证）
- **task-design**：2e.3 落盘 check 命令按产物语言归类校验器（ISSUE SC1071）
- **PLAN_PROMPT**：File Structure 预置改 skill 任务的 changelog 产物项（ISSUE F6）；Self-Review 增确定性断言噪声源检查（ISSUE）
- **task-execute**：执行循环第 7 步补 plan.md checkbox 同步（ISSUE）；4b 增全量套件判据（改名/跨模块/触 golden 源，ISSUE）
- **task-test**：蔓延闸补 feature-sized 追加不进 revise 的分流护栏（ISSUE）；验收分类补「契约可验 vs 需 dogfooding」两档标注（ISSUE F7）
- **task-end**：3.3 增共享文件归属核验（并发 session，ISSUE debt.md 串扰实证）
- **spec-task-skill**：约定 6 补薄引用纪律（只列触发点名+指回权威，ISSUE F-E）
- **激活入口序订正（O2，代码证实的双问 bug）**：2A.1 确立为交互主入口（编排路径必先触发、四选项都写文件）；task-design 2e Activation Timing 降为 standalone 后备，守卫改「文件已存在即跳过」——原守卫漏掉 `enabled:false + activate_after`（延后激活）状态、会被再问一遍。§5 入口序改三层表述，编排器/各 loader 脚注同步
- **归属修正**：golden 重生规则写入 `.claude/CLAUDE.md` 验证命令节（仓库级约定非通用技能规则）；「盲写 TUI 模板锚点」「Go iota 越界」两条属 ISSUE 项目级经验，移出技能 lessons（任务归档留底）

## 2026-07-06 批次 1：结构精简（诊断报告 B 组，用户两方向落地）

来源：`plans/task-slim-diagnosis.md` 批次 1（B1/B3/B4/B5/B7 + 1d）。结构重组不降能力，四项核心能力承载点未动。

- **B1（8 个 phase skill + UNATTENDED_PROTOCOL）**：无人值守渐进式披露——各 SKILL.md 的 `[Unattended]` 内联分支、停点表 Unattended 列、过渡备注全部收敛进 UNATTENDED_PROTOCOL §6（自动决策唯一来源；task-init 补 5 停点、task-design 补联网门/敏感度升级、task-end 补债务对账/产物门控/worktree 冲突、task-cancel 补 4 行、新增 task-revise 整节）；phase skill 只留 Unattended State 加载器 + 一行 §6 指针。Self-Discussion 的「主 agent 不 inline 作答」规则移入 §7 `<rule>`。
- **B3（激活契约收敛）**：UNATTENDED_PROTOCOL §5 为激活契约唯一权威；8 个 loader 脚注统一为薄引用——其中 6 份原写「统一由编排器 Step 2A.1 处理」与双入口设计（quiet→1f / 主入口→design 2e / 2A.1 后备）矛盾，已订正；删 task-init loader 内联复写的 4 行 §6 决策（其触发条件无视 declined 哨兵，属 bug）。
- **B4（11 份 README）**：按新 README 定位（摘要 + 增量信息，不镜像正文）收窄，402→98 行。
- **B5（删展示性双写）**：删 `task/LIFECYCLE.md`（134 行镜像流程图）与 task-execute 卡壳阶梯 dot 图（正文文字阶梯为权威）；指针清零（task/README、task/SKILL Dependencies、.claude/CLAUDE.md、hat-task-package excludes + 测试断言）。
- **B7**：worker description 排除条件（批次 0 已修）、init/execute transition 统一、停点表薄索引化——三项确认已消解。
- **1d（导出去侵入，窄修）**：task-execute 与 review plugin 两处「分发安全」括注改环境健壮性表述；review plugin「分发版经 ${CLAUDE_PLUGIN_ROOT} 解析」改「勿写绝对路径」；`task-defaults.json` `_telegram_chat_id_note` 去分发叙事（安全语义保留、指 §3）。诊断中 path-placeholder.md / `_note` 「可纯移打包器」分类经实物核查不成立（均为运行时消费物），不移，理由记 `plans/task-slim-diagnosis.md` §5。golden corpus 重生（1 例）。

## 2026-07-05 批次 0：修复级缺陷（诊断报告 A 组，用户确认后直改）

来源：`plans/task-slim-diagnosis.md` A 组四项功能性缺陷。均有真实事故证据（ISSUE/523/546），按对比协议「真实事故 > 测题区分度」例外经用户确认强制固化，未走两臂测试；对应 lessons 条目已移除。

- **A1（orchestrator）**：新增 `<rule>`——经 Read 加载的 phase SKILL.md 中动态注入行不展开，遇字面 `!`cat`` 当场 Read、字面 `!`命令`` 当场 Bash 执行。修复「DESIGN_PROTOCOL / PLAN_PROMPT 协议正文与 Runtime Context 探测在编排路由下静默缺失」（ISSUE F5，task-design lessons 固化上移至此——加载机制是编排决策，归 orchestrator）。
- **A4（orchestrator）**：新增 `<rule>`——一切 subagent / codex / headless worker 派发带超时上限（缺省 10 分钟），超时/瞬时 infra 错误退避 ≤1 次即转 fallback 并留痕（固化 task lessons 两条：ISSUE 529 空转 25min、ISSUE codex 续接挂起）。
- **A3（git plugin P6.post-archive）**：squash 守卫两处修复——①「全部未推送」判法改为 `--not --remotes` 计数比对（原 `--remotes` 在无 remote 仓库把全部本地提交计入、守卫误报，ISSUE）；②新增「区间无他任务提交」守卫（按他任务 `docs(task)`/`[task]` 标记判定，堵「并发任务也归档后 open≤1 守卫误通过」的洞，ISSUE/501）。守卫 `<rule>` 顺手由英文 ALL-CAPS 改为陈述式中文。golden corpus 经新工具重生。
- **A2（task-execute）**：codex dirty-conflict escalate 的 [Interactive] AskUserQuestion 阻塞菜单移除——所有模式统一为「可见停下+报告 + 经 /task resume resolution menu 决定」，兑现 P4 零阻塞交互（spec-task-skill 约定 9）；[Unattended] 的远程通知保留为 best-effort 叠加。
- **A4 补充（bin/codex-sandbox-gate）**：新增「验证依赖模拟器」机器判据（`xcrun simctl` / `maestro` / `xcodebuild …simulator…` → hard-fallback），修「gate 判 eligible 但沙盒无 CoreSimulatorService、能写不能验」（ISSUE，task-execute lessons 固化为代码）；配套 pytest 用例。
- **新工具 `bin/hat-plugin-golden-regen`**（+5 pytest）：按 golden 测试的等价构造重生 golden corpus，替代手抄 JSON；首跑即统一了 6 个手抄文件缺 `args` 键的格式漂移。
- **顺手（10 个 worker frontmatter）**：description 补排除条件（Do NOT use…），修合规审查 F4。

---

## 2026-06-22 TODO Sync 三档可配置 + 确定性触发契约（ISSUE）

经 continue-task 实施（用户显式选择继续跑 task；改既有 skill 正文前 inline 遵循 spec-skill，双盲验证折叠进 P4 code review，非走 skill-revise）。

- **config（task-defaults.json / .example）**：`todo_sync` 由 boolean 改枚举 `off | overview | full`；顶层 + 4 preset（full/standard/lite=`full`，hotfix=`off`）+ 枚举注释。
- **bin/hat-task-config-resolve**：规范化 legacy boolean（`true→full` / `false→off`）、非法/缺失→`full`；新增 `--todo-sync` 第④层 flag（非法值告警回落 config 值）。单测 `bin/test_task_config_resolve.py` +8 例。
- **bin/hat-task-package**：打包内嵌中英配置表 `todo_sync` bool→enum，避免分发版 README 发布旧契约。
- **references/todo-sync.md（改写）**：删旧「生命周期规则」#1（Phase1 开始建）/#5（Bootstrap 旧版）+ 末尾 `<rule>`；补三档语义 + **确定性触发点表（7 行，唯一权威）** + 4 命名模板（update_overview / update_step / transition_phase / cleanup）。overview 锚从「Phase1 开始」改到「**1f 末**」（name/config 已定），修用户报告的「建 todo 不稳定」时机倒挂根因。
- **task (orchestrator) SKILL.md**：compact 门 `todo_sync == false`→`== "off"`（语义等价）；`## TODO Sync` section 薄化为引用 + orchestrator 触发点（phase 切换 / Bootstrap 重建·刷新）。
- **9 worker SKILL.md（init/design/plan/execute/test/end/cancel/reopen/revise）**：`## TODO Sync` section 统一收敛为薄引用 + 各自触发点；删各自重复的双层契约段落。grep 一致性：10 section 均引用 `references/todo-sync.md`。

---

## 2026-06-21 接入 brainstorm 低分补完门控（ISSUE，经 revise-skill 双盲）

- **task-init（新增 1b.2b 头脑风暴补完）**：在 1b.2 与 1b.3 之间加恒执行门控评估步。触发判据沿用 1b.2 现有门槛（`2+ ❌` 或 `❌/⚠️≥3`）或用户主动；低分 [Interactive] AskUserQuestion 进入/跳过、[Unattended] 默认进入。进入则 `Read brainstorm/SKILL.md` inline、收敛回流到**内存态**结构化需求（prompt.md 仍由 1f 落盘）、重跑 1b.2 评分再进 1b.3。两态步、不引第三态。同步更新 Resume 步骤名映射、1b.3 第6步步骤生成、Mandatory Stop Points 表。为何：此前对模糊/初级需求无主动扩充机制，模糊需求带病进 Design。
- **task (orchestrator)**：phases.md Format Reference 默认模板 Phase 1 加 `1b.2b 头脑风暴补完` 行（与 task-init 生成逻辑步骤名一致）。
- 验证：经 revise-skill Phase 3.5 双盲 A/B（因 sonnet 不可用，改用 DeepSeek 无头进程作答/盲判）N=4 轮全有效（改后提议头脑风暴、改前仅建议重描述）。

---

## 2026-06-21 压测 Round 3 修复（同日）

- **task-design README**：「产物」段补齐 `task-config.json`（Step 2e 就地更新）与 `unattended.json`（activate_after 时），与 SKILL Dependencies 写入清单对齐（原漏列）。

## 2026-06-21 压测 Round 2 修复（同日）

- **task-design**：Step 1.5 调 web-research 补对称的 `contract_version: "1.0"` + 折叠前 major 断言（Round 1 只修了 dive 侧、漏了 task-design 这个对称调用方）。
- **task-end**：Step 2.6 Interactive 打回补状态回退机制（phases.md Phase 5→IN_PROGRESS、Phase 6→PENDING、FAIL 项标待复验），否则重跑 /task 会回环卡在 task-end。

## 2026-06-21 压测修复（同日，承上条）

- **task-design**：Resume 映射补「Step 1 + 1.5」折叠注记（防中断恢复跳过联网调研步）；DESIGN_PROTOCOL 折叠规则把 `verification==opinion` 显式纳入「仅备注、不作决策依据」、并区分 findings 字段值与 filtered_out 数组的层级。
- **task-end**：Step 2.6 打回条件 `[MUST] FAIL` → `[MUST] 或 [SHOULD] FAIL`（正文 + Mandatory Stop Point 表 + `<rule>` 三处），消除与 Phase 5 门控（task-test:172）的 drift。
- **task-test**：acceptance-checklist 模板图例登记 `DEFERRED` 为无人值守自动预填的第三种 `→` 取值（原为隐式约定）。

## 2026-06-21 联网调研接入 + 无人值守人工测试后移

- **task-design（DESIGN_PROTOCOL Step 1.5，新增）**：本地探索后、澄清前插入可选「联网调研」门。Interactive 询问是否联网（bug/0→1/建技能/陌生依赖默认建议是），是则调 `web-research` 引擎（`depth: quick`，`local_context`=已探查结论）；`findings[verified]` 折进 design 探索段、`tentative`/`filtered_out` 仅作「需实现期验证」备注、`coverage_gaps` 转澄清候选。无人值守保守档默认跳过（除非 prompt 显式要求），跑时传 `unattended:true`（成本封顶）。task-design SKILL.md 加 Step 1.5 无人值守分支 + Mandatory Stop Point 行。
- **task-test（Phase 5c，D1）**：无人值守 `self_test` 不再跳过/丢弃人工测试项——手动区域照常生成，人工项 `→` 预填 `DEFERRED（待 task-end 后人工验收）` 持久留痕；无人工项则手动区为空、同现状。
- **task-end（Step 2.6，新增 D2）**：归档前检测 acceptance-checklist.md 的 DEFERRED 人工项。Interactive 停下等用户验收（MUST FAIL 打回不归档）、回写 final.md Verification；无人值守不阻断归档，DEFERRED 清单写入 final.md「待人工验收」+ Telegram 通知。无 DEFERRED 项整步跳过、同现状。final.md 模板 Verification 段加 deferred 注释；Mandatory Stop Point 加 Step 2.6 行。
- **UNATTENDED_PROTOCOL**：§6 task-test self_test 行改为 deferred 留痕、新增 task-end「人工验收交还」行；§9 补「人工验收交还非 HARD-STOP」条（仅可机判 MUST/SHOULD FAIL 才硬停）。

## 2026-06-21 task 编排族 spec-skill 合规订正（hat-doctor Phase 1.7）

族模式 revise-skill 对 11 个 task 技能逐一审 + 族级综合，剔除族设计假阳性后落地合规修复：
- **description 去流程化**（7 worker：task-init/design/plan/execute/test/revise/reopen）：删掉 description 里的 workflow 步骤枚举，只留触发条件 + 触发词（spec：description 概述流程会被当捷径跳过正文）。
- **`<rule>` 英文散文 → 陈述式中文**：task-execute（2 条：未识别 mode 回落、P4.post-execute 两段执行）、task-setup（python3 缺失）。
- **变更记录式 / time-sensitive 注释清理**：删 task-execute「行为修正说明」、task-test/task-init/DESIGN_PROTOCOL「仅保留触发入口」；泛化 task-end/task-test/task-design 三处 Reason 里硬编码的任务 ID。
- **DESIGN_PROTOCOL 删残留 per-skill LANGUAGE RULE**（语言由全局 CLAUDE.md 固定）。
- **task-reopen 步骤重编号** Step 6.5 → 7/8/9 连续整数。
- **orchestrator lessons.md 补「建议出口」列**（对齐 spec 自进化表格式）。
- **Dependencies 补声明**：task（todo-sync/review-workflow/DESIGN_PROTOCOL/PLAN_PROMPT/LIFECYCLE）、task-revise（task/SKILL.md Revise 路由表）、task-cancel（UNATTENDED_PROTOCOL/todo-sync）。
- **README 同步**：task-design（步骤号对齐 + visual companion）、task-end（Step 3.6 独立 HARD-GATE）、task-init（补无人值守/档位/worktree/产物清单）、task-test（强否定式改陈述式）。
- **裁决为族设计、不改**：worker 缺 changelog.md（刻意合并进 orchestrator）、worker 缺 lessons.md（刻意集中式自进化）、硬编码 `~/.claude` 路径（个人版单一来源，分发由 hat-task-package rewrite_paths 承担）。
- 本轮无 lessons 固化候选（orchestrator lessons 表为空），故不触发双盲 A/B 测试。

## 2026-06-21 task-design 补回 visual companion 接线（hat-doctor Phase 1.7）

hat-doctor 体检发现 `task-design/visual-companion/`（ISSUE 从 Superpowers brainstorming「视觉脚本搬入」）落地 25 天全仓零引用——改编时只搬了资产、丢了接线。经核为漂移而非死代码，补回：
- **脚本升级到 Superpowers 6.0.3**（我们旧版停在 6.0.0 era）：替换 server.cjs(11→26KB)/helper.js/frame-template.html/start-server.sh/stop-server.sh，逐字保留以便未来安全更新。关键得到 **session-key 安全加固**（`?key=…` gating HTTP+WebSocket，旧版无此防护、同网任意浏览器可读屏/注入）+ `--open` + WebSocket 重连 + idle 30min→4h。仍纯 node 零 npm（新增 `crypto`）。
- **接线进 SKILL.md**：`## Visual / Semantic Decisions` 增「浏览器 Visual Companion」子节——just-in-time 提供、逐问决定浏览器/终端通道、仅 Interactive 无头跳过、指向 `visual-companion/visual-companion.md`；Dependencies 补 on-demand 声明；README 补提及 + 修步骤编号对齐 SKILL（6 → 6.5 → 7 → 8）。
- **顺带**：泛化该节 rule Reason 里硬编码的任务 ID（time-sensitive，optimization-rubric #7）；`.gitignore` 加 `.superpowers/`（companion 临时目录）。
- node --check + shellcheck 全过。

## 2026-06-21 去掉「codex 同仓库不并发」规定 + codex review/execute 并行

实测验证后移除「codex 同 repo 不并发」串行约束（之前从 codex execute 写冲突假设过度套用到 review）：
- **codex review 并行**（review.md）：P2 design R1/R2 由串行改并行——codex review 只读、同 repo 实测不串扰（broker busy 自动 spawn 独立子进程、state/broker 按 workspace-root 隔离），与 native R1/R2 并行对齐；收敛续接改**定向** `SendMessage(to: agentId)`、不依赖 `--resume-last`「最新 thread」。P3 单 reviewer 收敛轮本质顺序、澄清非同仓库限制。
- **codex execute per-worktree 并行**（task-execute）：C 段「强制串行」改「per-worktree 并行」——codex 写同树会 dirty-state 串扰，故可隔离 layer 经 git worktree 隔离并行（**实测**两个并发 codex 各落各 worktree、互不污染、不串主 repo）；D 段 dirty-state baseline/`CODEX_GIT_ROOT`/归因全部 per-worktree 锚定。worktree 生命周期+合并落 `execute-workflow.md` codex 变体。
- golden P2.post-design-draft / P3.post-plan 重生；192 pass、打包 [OK]。

## 2026-06-21 P4 Execute 接入可选 Workflow 后端（探测回落）

hat-flow × Workflow 审计的第二个结合点（推荐度中）。现状 parallel-agents 已是「`await_all` barrier + `handle_hooks_and_checkpoints` 主 session 收口」，故 Workflow 接入只换并行引擎、**不改 hook/commit 语义**：
- **task-execute SKILL.md** auto/parallel-agents 分层调度加「执行后端：可选 Workflow」节——默认主 session 并行派发（≤3）；仅 `execution.dispatch_backend:workflow` + 探测到 Workflow 工具时改用 Workflow `parallel()` barrier（并发可 >3），results 交回主 session 收口。三守卫：不写 phases.md / 不触发 hook / 缺失回落。
- 适用边界：engine≠codex、Files 不重叠故不需 worktree、TDD/RED 同现状。
- 新增 `task-execute/references/execute-workflow.md` 脚本骨架 + 主 session 收口 + A/B 对账。

## 2026-06-21 P4 full-review 接入可选 Workflow 后端（探测回落）

为 review 层最佳试点（hat-flow × Workflow 审计结论）接入 Workflow：
- **review.md `## P4.post-execute/full-review`** 加「执行后端：可选 Workflow」子节——默认主 session 派发；仅 `review.workflow_backend:true` + 探测到 Workflow 工具时，改用 Workflow 并行扇出 reviewer + 逐 finding 对抗验证，barrier 收齐 findings 交回主 session。三守卫：不写 phases.md / 不触发 hook / 缺失静默回落（分发安全）。
- 新增 `references/review-workflow.md`：Workflow 脚本骨架（`pipeline(review→verify)` + schema）+ 主 session 收口 + A/B 对账方法。
- golden `P4.post-execute.json` 同步重生；192 tests pass。

## 2026-06-21 自进化闭环改造 批次1：入口守卫（retrospective + task-end）

落地两段式自进化的「唯一固化入口」（诉求6）：
- **retrospective 插件**（`plugins/retrospective.md`）：Execute-now 的 Workflow/Skill 类改进降级为「沉淀为对应技能 `lessons.md` 候选 + 提醒走 revise-skill」，不再直改 skill 文件；新增 `<rule>` 禁本插件直改技能正文；Project 配置类（CLAUDE.md 等非技能文件）照旧。配套 `bin/fixtures/plugin_hook_golden/P6.post-archive.json` 同步重生。
- **task-end Step 3.6**：门控提示同步——Workflow/Skill 改进只沉淀 lessons、固化改用 `revise-skill`（改既有技能正文的唯一入口，带双盲测试门）。

## task (orchestrator)

### 2026-06-22 lessons 候选「open task 与新 prompt 冲突询问」对比实验中性、保留 lessons（skill-revise）

候选（重要度 7，拟落 Step 1 路由正文加分支）经 skill-test 两臂对比：改前 / 改后 mid 池均 5/6 pass → 中性，改后无增量。「建议出口」标注为「正文（测试中性·留待重测）」、留 lessons 不固化。本轮 experiment 措辞偏引导、未拉开区分度，下次重设计更隐蔽 criteria 再测。

### 2026-06-20 描述范式级联：11 个 task skill 删 Red Flags 表 + 软禁止式陈述化（ISSUE）

设计哲学转变（ISSUE / `plans/3-skill-paradigm-shift.md`）从 spec 层（spec-skill / spec-task-skill / spec-git）spillover 到执行层。11 个 task skill 全部经并行 cascade 改造：

- **删各自的 `## Red Flags` 表**（11 张）——逐行核对：已被本文件 `<rule>` / 正文 / checklist 覆盖的直接删；独有指导先硬化成陈述式规则再删，**零指导丢失**。硬化项例：task-design YAGNI、task-plan「review 不因 plan 看着好而跳过」+「手动提交只 add 具体文件」、task-execute「review 修复 commit 须后置于用户确认」、task-revise「revise 不嵌套」、task-reopen「git mv 原子暂存」、task-setup「override 落项目本地非全局预设」、task-end「final.md 写全」「doc-only 仍跑 pre-commit 检查」。
- **软禁止式 → 陈述式**（surgical）：如 task-design `不得全盘接受`→`逐条独立裁决`、task-test `Do NOT commit`→`commit 前置条件是用户确认`、task-init `do NOT create directory yet`→`目录创建推迟到 1f`、task-execute「一卡就上报/换模型」→「上报与换模型后置于根因定位」。
- **保留全部正当硬 `<rule>` / `<HARD-GATE>`**（带 Reason、守不可逆 / 静默失效）；`task/SKILL.md` 的 Step-2B「Rationalization 表」识别为 HARD-GATE 自检的一部分、非 Red Flags，**未删**。
- 字数 18325→16855（**−1470 ≈ −8%**）。未触碰 frontmatter / hook 调用 / `!cat` 预注入 / phase 逻辑（git 验证：`!cat` 0 触碰、frontmatter 0 触碰）。
- **待人工一瞥**（非阻断）：① task-execute 的「TDD RED 异常→停下报告」留在 tdd 插件 hook、未在正文复述（避免重复插件逻辑，仅 tdd 插件关闭时才无正文兜底）；② task-design「explore-first 的 unknown-unknowns 理由」在预注入的 `DESIGN_PROTOCOL.md`（本 pass 不可编辑）。

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

### 2026-06-22 固化「外部 CLI 脚本须 P4 开发期真实冒烟」（skill-revise，经对比实验通过）

P4「执行循环」Light verification 段后新增 `<rule>`：包裹外部 CLI 的脚本（调 claude/claude-hl 等）在 P4 开发期跑一次真实冒烟、不延到 Phase 5——stub 单测只验调用方传参、建模不了外部 CLI 真实语义（变长参数贪婪吞位 / IFS 空白折叠 / PATH 解析），契约层全绿端到端全挂。来源 ISSUE lessons（重要度 9）。经 skill-test 两臂对比实验：改前 pool 6/6 全误判「stub 够用即推进」(fail)、改后 6/6 全选「先跑真实冒烟」(pass) → 判有效，固化进正文并从 task-execute lessons 移除。池 = deepseek-v4-pro + MiniMax-M3（各 3 轮；glm-5.2 strong 档本轮整组不可用，已排除以免同等压垮两臂）。

### 2026-06-22 接第四执行后端 engine=headless-provider（ISSUE）

在 engine 派发漏斗（codex 分支同序位置）加 `execution.engine == "headless-provider"` 分支：经 `claude-dispatch`（headless-scheduler 底座）把实现 task 下放给第三方 provider worker。engine 维度第四值（与 auto/sonnet/opus/codex 并列），非 dispatch_backend 扇出维度。边界：仅 mid+ 档、产出仍过 P4 code review（恒 claude）、守卫参照 codex 后端（不写 phases.md / 不触发 hook / 缺失静默回落）。现有 auto 模型分流与 codex 分支未改。

### 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

### 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 对齐 hook 化后的实际流程：删除已脱节的「Code Review Light（Medium/High 必做）」「Commit Guidelines 内联」表述，改述为 P4.per-task-post / P4.post-execute hook 驱动。
  - SKILL.md 4a mode fallback `<rule>` 正文改英文（Reason 保留中文），符合双语策略。

---

## task-test

### 2026-06-22 transition 补「返回编排器 Step 3」指令（skill-revise 合规订正）

`## Test 完成 → 过渡` 原仅含宣告 + 提示 `/task-end`（约定1 Test 例外），缺 sibling（task-plan/task-execute）一致的「停止输出，返回编排器 Step 3 执行过渡逻辑」结构指令——补上，使过渡逻辑（artifact check / compact / unattended check）归编排器（spec-task-skill 约定1 通用要求）。`/task-end` 硬停提示按约定1 Test 例外保留。

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
