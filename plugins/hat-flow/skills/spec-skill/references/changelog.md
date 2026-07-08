# spec-skill 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-07-07 负向自进化：第 3 类摩擦（规范失真）+ 负向候选出口（用户诊断「只加不减」）

- **背景**：用户指出自进化系统只增不减——薄弱/无用/幽灵内容没有修改或删除的路径。同日舰队审计实证：幽灵 `claude-dispatch verify`、过时 permission_mode 枚举、断裂调用链声明，全部只能靠一次性人工审计发现，两段式闭环对它们零感知。
- **canonical 母本**：「dogfooding 收什么」由两类扩为三类，新增**第 3 类·规范失真（负向信号）**——照文本执行即失败 / 声明调用链断裂 / 被合理跳过且无后果的疑似死文本；裁决漏斗后新增「负向候选」段：建议出口标 `正文订正` / `正文删除`，与加法候选同走两段式；**事实性订正（有实测证据的照做必失败类）走合规订正路径直改、证据即裁决、不占实验预算**。
- **配套**：skill-revise 对比协议新增负向模式裁决表（§3b，中性语义反转：两臂等效=不承重=可删）；`hat-skill-lint` 新增声明-现实一致性两查（注入路径存在性 + 正文幽灵引用，pytest 20→25）；舰队审计固化为 named workflow（`.claude/workflows/skill-fleet-audit.js`，含负向候选产出）。

## 2026-07-07 user-invocable 判据例子订正

- ③ subagent-only 例子删去 dogfooding——它由用户直接调用（其正文自述 + 用户确认 /dogfooding 可见），举例与判据矛盾会误导 review 把它当违规。

## 2026-07-07 Length Budget 改三档声明制（用户决策，基于 19 技能全量审计数据）

- **背景**：2026-07-07 技能舰队审计发现 12/19 超 500 词预算，实测词数天然聚成三簇（<500 / 800-1400 / 1500+），单一 500 + 硬编码权威名单（lint 内 `AUTHORITY_SKILLS`）无法表达中间层，导致重流程技能永久挂 WARN 或被迫过度碎片化下沉。
- **规则**：Length Budget 改为三档 + 豁免——500（默认）/ 1000（多阶段流程技能，下沉做完仍需）/ 2000（编排器 / 生命周期一体型 / 权威规范类，吸收原 1500 档）/ exempt（仅 task 编排器）。档位经 frontmatter `word-budget` 声明，升档 / 豁免须在 changelog 记理由，review 时可挑战。用户明确：bookkeeping、task-init、task-execute **不入豁免**，声明 2000 档并列入瘦身队列；不设 500 以下档位（预算是上限不是目标，小技能不因此省 token）。
- **实现**：`bin/hat-skill-lint` 废除 `AUTHORITY_SKILLS` 硬编码，改读 frontmatter（超档 WARN / 非法值 FAIL / exempt 仅报数）；pytest 由 16 → 20 个（新增声明档内 / 声明档超 / exempt 报数 / 非法值四用例，删除硬编码权威名单用例）。本 skill 自身声明 `word-budget: 2000`（权威规范类）。

## 2026-07-05（三）自进化闭环修复：收尾触发兜底（用户发现摩擦点积压无人提醒）

闭环审查发现两个断裂点，都是「触发缺失」而非「机制缺失」（实证：`.friction/` 38 个文件积压、仅 4 个曾归档）：

- **断裂点 1（friction → 收尾蒸馏）**：收尾 Dogfooding 依赖技能流程走完，会话中断 / 用户忘记发起时摩擦点永久积压。修复：新增 `bin/hat-friction-remind` **Stop hook**（harness 强制执行、不靠模型自觉）——本会话摩擦点 ≥3 时提醒用户可跑 `/dogfooding`，一会话只提醒一次（marker 防重 + `stop_hook_active` 防循环），顺带报历史遗留文件数；`settings.json` hooks.Stop 注册；配套 7 个 pytest。canonical 母本补「收尾兜底」一段（hook 机制 + 历史遗留消化路径归 /dogfooding）。
- **断裂点 2（lessons → skill-revise 固化）**：lessons 积压后没人提醒开池（老化机制只解决排队不解决触发）。修复：`hat-skill-lint` 加积压信号——lessons.md 条目 ≥5 时 WARN「建议跑一轮 skill-revise」，`--all` 巡检时自然浮现。修了一个实现 bug：表头判据从子串匹配改为精确匹配首单元格（子串会误滤以「经验」开头的真实条目）。

## 2026-07-05（二）用户 review 后的审核修订

- **Length Budget 规则修订**：原「高频加载 skill <200 words 核心」在执行中证实不可行（Required Structure + Iron Laws + Checklist 本身即超 800 词），且被全文预注入的消费者需要正文完整可用。改为「权威规范类（被其他技能全文预注入消费）：正文 ≤1500 words 且 ≤500 行，论证/证据/进阶机制强制下沉 references/」——预算约束的是「不该在正文的内容」而非砍掉操作性规则。`bin/hat-skill-lint` 阈值同步（200→1500），description 检查接受 "Do NOT use" 变体（本 skill 的 ALWAYS-read 开头是 2026-06-16 为触发可达性的刻意设计，不该永久挂 WARN）。
- **File Organization**：evals.md 行补硬上限 ≤8 条 + 淘汰规则（同步 `self-evolution-spec.md` 组件表、skill-revise 协议文件）。
- **Checklist 新增**：「若目标是 5 个元技能之一：已先读 references/meta-skill-philosophy.md？」——philosophy 文档此前没有任何机制保证被读到，与 spec-task-skill 曾经的「靠人记得加载」是同构问题。
- **philosophy 文档补「已知例外登记」节**：skill-revise 无自进化（经用户确认的设计例外）的理由与代价显式记录。
- **修悬挂引用**：Patterns 节「（见 Dynamic Injection）」→ 指向 `references/advanced-features.md`（该节已下沉）。
- **`hat-skill-lint` 新增 `--all` 全仓扫描模式**（按 `skill-maintenance-ignore` 过滤外部技能、输出汇总、任一 FAIL 退出码 1）——补齐「维护者」的主动巡检能力，原 plan 只有被动触发。首次全仓扫描即暴露并修复 lint 自身一个 bug：description 为 YAML block scalar（`>`）多行写法时只解析首行、把 bookkeeping/daily 等 7 个有中文触发词的技能误判 FAIL——`get_description()` 现兼容单行 / block scalar / 折行。配套 pytest 用例扩至 14 个。

## 2026-07-05 元技能改造第一批：体量下沉 + 自相矛盾清零 + README 定位重写

用户发起的「元技能体系改造」诊断发现规范权威自身不合规：正文 493 行/2148 词，远超自定「高频加载 <200 词核心」预算；正文第 314 行（spec 类保留 lessons.md inbox）与旧 Checklist 项（spec 类只有 changelog）自相矛盾；正文与 README.md 存在新旧「写入闸」语义混杂。改动：

- **正文体量下沉**（493→305 行，2148→1330 词，降约 38%，未压到 <200 词——见下方说明）：Self-Evolution Capability 的 Components 表/经验库格式/编排族归属/When to Offer 详述下沉至新建的 `references/self-evolution-spec.md`；措辞准则 7 条的证据基（脚注引文）下沉至新建的 `references/wording-evidence.md`；Cross-Model Compatibility 整节下沉至 `references/advanced-features.md`；Dogfooding 的具体执行步骤（worktree/dry run/检查点清单）下沉至 `references/proven-patterns.md`。正文只留骨架规则、两条 Iron Laws、Checklist——未进一步压到 200 词是因为 SKILL.md 会被 `skill-revise`/`spec-task-skill` 全文 `!cat` 预注入，继续下沉会让这些消费者读不到操作性必需内容（Constraint Tiers/措辞准则清单/Length Budget/File Organization/Checklist 予以保留）。
- **Checklist 矛盾清零**：「经验库归属按类型正确」一项改为与正文一致的「流程类才有完整 lessons.md + 冷归档；spec 类仅 lessons.md 暂存 inbox + changelog；一次性工具类都没有」。
- **README.md 定位重写**（Required Structure 第 5 项）：去掉「纯中文流程综述，覆盖目的/触发条件/核心流程/关键规则」的镜像式定位（英文技能时代译文职责的遗留），改为「① 3-5 句摘要 ② SKILL.md 放不下的补充信息」，不复述 Iron Laws/Process。历史沿革记录在 `references/self-evolution-spec.md` 末尾。`README.md` 本身按新定位整篇重写收窄。
- **File Organization 新增 `evals.md`**（Optional）：技能行为回归用例，经 `skill-create`/`skill-revise` 验证通过后追加，供下次修订回归复测。
- **Checklist 新增两项**：技能带 scripts/ 时是否配 `bin/test_<script>.py`（pytest）；是否跑 `bin/hat-skill-lint` 通过。
- **新增 `references/meta-skill-philosophy.md`**：5 个元技能共同遵守的跨技能设计哲学（8 条原则 + 与外部实践的取舍记录），正文入口分流段加一句非强注入的指针。
- **顺手修正**：`~/.claude/skill-maintenance-ignore` 文件头注释里的过时技能名 `revise-skill` 改为现名 `skill-revise`（2026-06-22 该技能已改名，注释未同步）。

## 2026-06-22 canonical 母本：沉淀经验须带上下文 + 出处指针（用户诉求）

`self-evolution-canonical.md` 写入闸后新增一条：每条经验「来源」列须填 ① 一句简短上下文（产生情境 / 为何重要）+ ② 原始出处指针（commit 短 hash / `.tasks` 归档名 / PR 号，可内联或 markdown 角标，确无可留空）；**固化采纳后上下文 + 出处一并剥离、不进正文**（溯源归 changelog）。动因：沉淀与固化异步，固化方缺情境时判不出该改写措辞固化还是抛弃；带上下文 + 出处才能据情境定夺。配套在 `skill-revise/references/comparison-test-protocol.md` 实现约束补「固化时剥离上下文 + 出处」一条。母本注入所有自进化技能 + skill-revise，沉淀端与固化端同时生效。

## 2026-06-22 lessons 候选「CLI flag 先 --help 核对」对比实验中性、保留 lessons（skill-revise）

候选（重要度 8，拟落 Constraint Mechanism Guide 正文）经 skill-test 两臂对比：改前 / 改后 mid 池均 6/6 pass（worker 不带该 rule 也选「先核对再写」）→ 中性，改后无增量。「建议出口」标注为「正文（测试中性·留待重测）」、留 lessons 不固化。注：本轮 experiment 的 VERDICT 选项措辞偏引导、未充分拉开区分度，下次可重设计更隐蔽的 criteria 再测。

## 2026-06-22 Dogfooding 加实证验证（skill-test）+ revise-skill 改名（ISSUE）

- `## Dogfooding` 补一段「实证验证（尽量，非必须）」：新写/改技能文本时尽量用 `skill-test` 多 provider 多轮池化加权裁决，用证据而非主观判断引导效果。
- 全局改名 `revise-skill`→`skill-revise`、`blind-ab-test-protocol`→`comparison-test-protocol` 同步到本文件正文引用（机械改名，见 skill-revise changelog）。

## 2026-06-21 自进化闭环改造 批次3：首次走通固化端（双盲 A/B 实跑）

revise-skill Phase 3.5/4 首次实跑（对 dogfooding 2 条 lessons 双盲 A/B 测试，18×Sonnet）：
- **固化** 1 条——「文档与脚本同时落地先定脚本形状」进 canonical 母本「先验后做」段；双盲 N=3 **全有效**（改后命中、改前不命中）。
- **退回** 1 条——「即时落盘缺触发点」3 轮全中性（改前描述已够强），保守退回 dogfooding lessons 标「测试未决」，演示测试门挡下 YAGNI 式过度固化。

## 2026-06-21 自进化闭环改造 批次2：spec 类技能引入「暂存 inbox」（补两段式裂缝）

dogfooding 实拍暴露的 gap：spec 类技能原本「不设 lessons.md、经验直接改正文」，但两段式要求「运行段只沉 lessons、不直接改正文」——spec 类运行段经验无处可沉（如「改 plugin 须重生 golden」卡住）。修复：
- **When to Offer 段 + `<rule>` + 按类型分表**：spec 类不设常驻经验库，但保留 `lessons.md` 作 **transient inbox**（运行段沉候选 + 「建议出口」标记 → revise-skill 固化进正文后**清空**；不归档 / 不整合 / 不自注入，读者是 revise-skill）。
- **canonical 母本**：补「lessons.md 两种形态」注（流程类=常驻 library，spec 类=transient inbox）。
- 配套为 `spec-task-skill` 建首个 inbox `references/lessons.md`（落 golden 重生经验）。
> 注：revise-skill 不是 spec 类（无 `spec-` 前缀），它可按需有自己的常驻 lessons；本批次只针对 `spec-*` 规范类。

## 2026-06-21 自进化闭环改造 批次1：两段式范式（提议/固化分离）+ 摩擦临时文件硬约束

把自进化从「运行段直接改流程」改为「提议-固化分离」的保守闭环（依据 SkillsBench skill-debt 警示 + Reflexion 反思入 buffer 范式）：
- **canonical 母本 `self-evolution-canonical.md` 整段重写**：新增两段式范式表 + `<rule>`（运行段只许写 friction 临时文件 + lessons，固化延后到 revise-skill 双盲测试后）；新增「摩擦点忠实记录」硬约束（遇摩擦当场写 `~/.claude/.friction/<sid>__<ts>__<seq>.md`、静默自动不通知用户、不写项目树）；裁决漏斗改为「只分类打『建议出口』标、不当场固化」；写入闸反转为「运行段默认进 lessons」；整合段移除「升级固化」（转交 revise-skill）。
- **SKILL.md Self-Evolution Capability**：Components 加「摩擦临时文件」组件行、经验库组件改述两段式；收尾 Dogfooding 组件改为「只写 lessons 不改正文」；经验库格式加「建议出口」列；防膨胀机制段同步两段式表述。
- 配套 dogfooding / revise-skill 改造见各自 changelog（批次1 后续步骤）。

revise-skill 批1（spec 层）自审发现并订正：
- **README.md 整篇重写**（原 Critical 偏差）——原 README 仍是 ISSUE 改造前旧范式（「Overview+Language Rule」「Red Flags 必需结构」「## 双语策略：约束用英文」「ALL CAPS 失败率最高」），与现行 SKILL.md 全面冲突。重写为新范式：必需结构 7 项（无 Language Rule / 无 Red Flags 必需项）、语言策略（陈述式中文+输出语言由 CLAUDE.md）、约束机制三层 HARD-GATE/rule/Bold、删证伪的 ALL CAPS 断言。
- **正文下沉守 rubric 500 行上限**（684→488 行）：`## Proven Patterns` → `references/proven-patterns.md`、`## Flowchart Usage` + `## Advanced Features` → `references/advanced-features.md`（>100 行加 TOC）；正文留指针。no-hardcoded-paths `<rule>`（审计相关）保留正文；更新「见 Subagent Collaboration」交叉引用指向 reference。
- **悬挂引用清理**：Dogfooding 检查点「需要加 `<rule>` 或 Red Flag」→「或陈述式规则」（Red Flag 构件已删）。

## 2026-06-21 范式落地后精修：移除 LANGUAGE RULE 要求 + Iron Laws 例子中文 + 自进化精简 + 语言策略收口

承接 2026-06-20 范式转变 + LANGUAGE RULE 移除，精修本 spec：
- **移除 per-skill LANGUAGE RULE 要求**：Required Structure §2 改「Overview + Announce」（删 LANGUAGE RULE 模板）；删「§输出语言」整节（连带孤立的 `[^lang-consistency]` 脚注）；输出语言改由项目 CLAUDE.md 单一固定。
- **删 §3 Red Flags 段**（已降级为不注入的作者工具、正文留它已无上下文）+ §4-8 重编号为 §3-7。
- **Iron Laws 例子转中文**（`<rule>` 示例以身作则）；语言策略核心句去掉「取代旧双轨——双轨从未验证」这类改动来由（属 changelog）。
- **Exploration Budget / Stop Points 残留英文转中文**。
- **Self-Evolution Capability 精简**：防膨胀机制（写入闸/整合/changelog 纪律）改为指向 canonical 母本、不再正文重复；删编排族 2 条与母本重复的 `<rule>`；缩短「为何外置」justification。保留 canonical 强制 `<rule>`。
- **移除 Failing-Test-First for Skills**（实测从未触发）→ 作为可选实践折叠进 Dogfooding 一句。
- **Checklist 同步 + 中文化**：合并冗余项、补「约束陈述式」检查、英文项转中文、去 LANGUAGE RULE 项。

## 2026-06-20 描述范式转向陈述式 + 精简 + 语言策略（pure-Chinese-if-declarative）

设计哲学转变（ISSUE / `plans/3-skill-paradigm-shift.md`），基于两轮对抗式文献核查：

- **删被证伪的断言**：「ALL CAPS 41% / Title Case 3.1%」误引（真源 Dong et al. arXiv:2512.14754 测的是输出全大写、非规则排版）→ 删；「Reason 比强调标记更有效」的比较半句无源 → 软化 + 补 Anthropic 引文。
- **措辞准则重写**：8 条陈述式原则（陈述式默认 / 去强调通胀 / 附 Reason / 具体非模糊 / 规则少而不冲突 / Trailing reminder / 结构承重），各带来源脚注。
- **Red Flags 降级**：删顶部注入表 + 改「作者自用、不注入」+ 清下游引用（Constraint Tiers 行 / Checklist 项 / Anti-Patterns 行）。依据：其对 model 行为无证据（原文 §3 自承）。
- **Anti-Patterns → 陈述式 Patterns**（去禁止式对照列）。
- **Bilingual Strategy → 语言策略**：旧「约束英文 / 描述中文」双轨（未经验证）→「正文中文 + 硬约束语域中性陈述 + 标识符英文 + 输出 pin 显式」。
- **脚注体系**：所有引文移文末 `## 参考来源`，正文用 `[^label]`（GFM 标准、可复用）。
- **示例规则陈述化**（Cards / @-link 示例以身作则）。
- 保留全部硬可靠性构件（HARD-GATE / rule / 预注入 / trailing reminder / gate）；残留 Never/Do-NOT 经核为正当硬约束，按「祈使留给真硬约束」保留。

---

## 2026-06-16 强化触发可达性（description 祈使化 + 全局 CLAUDE.md 硬前置）

实测「新建 skill」未自动加载 spec-skill——description 自动触发是软的、不保证。两层加固：① description 改为祈使式「ALWAYS read BEFORE authoring/creating/scaffolding/editing/reviewing ANY skill」+ 补同义触发词（建一个 skill / 做个技能 / 脚手架 / 让技能合规 / scaffold·author）；② 在全局 `~/.claude/CLAUDE.md` 新增「Skill 规范」段，规定建/改/review 任何 skill 前**必须先调用 spec-skill**（确定性前置，CLAUDE.md 每次必入上下文，不依赖软触发）。

---

## 2026-06-16 自进化过程准则改为「全局母本直接注入」+ 母本新增 pre-flight/收两类摩擦点

- **架构改造**：废弃「每技能各存 `references/self-evolution.md` 副本、批量同步」模型，改为**所有自进化技能启动时直接注入唯一母本绝对路径** `references/self-evolution-canonical.md`（类比 system prompt，改一处全体下次启动生效，无副本可漂移）。删除全仓 22 份副本，22 个技能注入行 `${CLAUDE_SKILL_DIR}/references/self-evolution.md` → `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/references/self-evolution-canonical.md`（an alternate runtime 兼容的 bookkeeping 用 `Read` 绝对路径）。同步：Self-Evolution 组件表/rule/文件结构/Checklist、reviewer 维度5（改查「注入母本」+ 残留副本判 Important）、_template、revise-skill。
- **母本内容升级**（针对实跑反馈：~80% 出错是「凭记忆猜字段/参数/文件名→报错回改」而非脚本错，过去 dogfooding 不收这类、反复犯）：① 新增 **dogfooding 收两类摩擦点**（技能不符 + 执行返工）；② 新增 **先验后做 pre-flight 纪律**（不确定形状先 `--help`/`ls`/读样本再动手；静默空结果先核字段）；③ 漏斗②扩为吸收「可文档化形状」沉进 reference 免下次再猜，并给出返工两类归途（可文档化→reference / 纯纪律疏忽→pre-flight，反复栽→补 SKILL 正文检查点）。

---

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

spec 类不面向用户直接调用，靠触发词/被引用激活；隐藏后仍可自动触发。

---

## 2026-06-16 重定义 changelog 纪律 + 外置受管自进化区块 + user-invocable 隐藏指引

实战（arkcase work skill「即使没改 skill 也每轮往 changelog 灌 dogfood 流水」）暴露两个根因，连带修：

1. **changelog 纪律**：组件表原把 changelog 写成「详尽流水存档」，诱导每轮写；work 母版落实成「每轮把摩擦点/dogfood 经过记 changelog」。改为：changelog **仅在 skill 定义真被修改时**写一条（改了什么+为何），没改不写，不是运行流水账；dogfood 详尽经过蒸馏进正文/经验库或丢弃。新增对应 `<rule>`。
2. **外置受管自进化区块（防漂移 + 便于批量升级）**：裁决漏斗/写入闸/整合三机制/changelog 纪律这套对所有自进化技能都一样，此前各技能手写进正文 → 漂移（实测 14 个里 3 个漏/混 changelog 措辞）。改为：建 canonical 母本 `references/self-evolution-canonical.md`，各技能携带副本 `references/self-evolution.md` 经 `!`cat`` **硬注入**、标记受管勿改；升级从母本覆写。组件表加「过程准则（受管注入）」行 + File Organization 加该文件 + 新增 `<rule>`。
3. **user-invocable 隐藏指引**：frontmatter 段补「哪些该设 false」——spec 类 / 被派发 worker / subagent-only 内部工具隐藏；面向用户入口保持可见。

> 触发来源：用户报 arkcase changelog 每轮被写，要求「一定改了 skill 才写 changelog」+ 提出把自进化元信息外置成注入的受管小文件防漂移 + 把内部技能 user-invocable 隐藏。配套批量修订 ~/.claude 14 + arkcase/car/merlin 各 work/revise + _template。

---

## 2026-06-15 frontmatter 补记合法可选字段 `user-invocable`

全量 revise 扫除时 dogfooding 发现：标尺只列了 `name`/`description`/`self-evolving`，未记 `user-invocable`，导致审查 subagent 把 spec-readwise/bookkeeping/codex-* 的 `user-invocable: true` 误报为非法字段建议删除。核实它是 Claude Code 原生 frontmatter 字段（官方 telegram/vercel/codex 插件均在用 `true/false`，控制是否进 `/<name>` 斜杠列表）。改动：Required Structure §1 frontmatter 段补一条「可选字段 `user-invocable`」说明，明确 review 不得当违规误删。归属：标尺缺口 → 改 SKILL 正文。

---

## 2026-06-15 新增「编排族经验归属规范」（orchestrator + workers）

机制此前只覆盖「单技能 = 一道流程 = 一个经验库」，未考虑 task 这类**编排族**（一道任务由多个技能重合完成，经验归属有歧义）。新增：

1. **Self-Evolution 章加「编排族的经验归属」一节**：立判据「归属 = 下次被检索/应用的决策点，非发现点」+ 三推论（执行细节→worker / 编排决策→orchestrator / 交接契约→看谁把关）+「orchestrator 也只是一个技能、有自己 lessons.md、不造 series 级公共经验库」。
2. **加两条 `<rule>`**：① family 归属按检索点不按发现点、不设共享 lessons.md；② **写入闸补「归属问句」**——写族经验前先答「哪个技能的哪个决策点读它」，答不出唯一归属 → 要么固化进正文、要么没定位到复用点，**绝不把同一软经验镜像进多个 lessons.md**（必 drift）。
3. **Checklist 加一项**：编排族经验按检索点分流、无公共经验库、无跨技能镜像。
4. README 同步「编排族归属」段。

> 触发来源：用户提出「task 这种系列技能（编排 + 子技能）的经验该落哪」的真空地带。配套 revise-skill（族模式审查）+ hat-doctor（Phase 1.7 分类前置）同批改动。

---

## 2026-06-15 经验库整合改为「触发式」（每轮评估、酌情跳过）

用户反馈：每轮强做归纳覆写不现实。把防膨胀从「写入闸 + 升级 + 每轮归纳覆写」三机制改为**两机制**：①写入闸（每次写入）；②**整合 = 升级 + 淘汰 + 归纳覆写（触发式）**。lessons.md 头部记「上次整合: YYYY-MM-DD」，每轮收尾按判据评估：**必做**（达硬上限 ≤15 / 上线提交 / 特定节点 / 距上次整合 ≥1 天）vs **可跳过**（轻量 / 已精简 / 刚整合过）。判据只看两样：硬上限 + 上次整合时间。已同步 spec-skill 正文 + README + 模板 + arkcase + 各 lessons.md 头部。

---

## 2026-06-15 新增可移植性铁律（无项目信息 / 本地路径）

用户反馈：skill 内容不得含具体项目信息、本地绝对路径（不可分享 + 项目一移就断）。

- **新增 `<rule>`**（Advanced Features 路径约定后）：skill 内容禁止硬编码本地/绝对路径与跨项目引用；用 `${CLAUDE_SKILL_DIR}`/相对路径；项目级 skill 只能引用自身项目（相对），不引用别的项目。通用框架路径（`.claude/skills/`）可接受。
- **修违例**：删除自进化章末尾对 `~/Projects/Outsourcing/_template/skill-template/` 的跨项目引用，改为「本规格自包含」。
- **Checklist 增项**：无具体项目信息 / 本地绝对路径 / 跨项目引用？
- 同步修正 revise-skill 里硬编码的 spec-skill 路径（改用 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/`）。

---

## 2026-06-15 自进化机制升级 + 文件结构规范化

两轮设计讨论的落地。改动：

1. **Self-Evolution Capability 章重构**：
   - 经验库改为**表格格式**（经验 / 重要度 1-10 / 来源 / 上次命中），放弃逐条精确命中计数器（agent 自报不可靠、逐步记账必被省略）。
   - 新增**防膨胀三机制**：写入闸（防垃圾桶，写经验前须论证为何不能上移到流程）、升级（反复命中→固化进流程后移除）、归纳覆写 + 冷归档。
   - 新增**冷归档组件** `references/lessons-archive.md`：永不注入/引用，被挤出的经验沉这里不删，可人工回溯 / revise-skill 复活。
   - 经验库设**硬上限**（默认 ≤15 条）。
   - When-to-Offer 明确：仅流程类提议完整经验库；**spec(Spike)类不设独立经验库**（经验直接改正文），只保留 changelog。
2. **File Organization 重写**：给出通用 skill 文件结构 + **流程类 vs spec(Spike)类**组件分层表；新增 `<rule>`「所有被修改的 skill 都要有 changelog」。
3. **去外包污染**：从全局约定译名移除 `甲方标准/材料/证据/交付/报告模板`（Outsourcing 专有概念，归该项目自己的规范）；全局只留通用译名（lessons.md / lessons-archive.md / changelog.md / 子协议）。
4. **Checklist 增项**：changelog 存在、文件结构合规、经验库归属按类型正确、防膨胀三机制就位。
5. **README.md 同步**：新增「文件结构与类型分层」「自进化与经验库防膨胀」两节。
6. **本 changelog 文件创建**（dogfood 新规则：spec 类 skill 也要 changelog）。

调研依据：Hermes/an alternate runtime（实测确认其技能存储与官方 Agent Skills 同构，但**未解决防膨胀**）、Voyager（验证入库门槛）、Generative Agents（importance×recency 评分）、ExpeL（投票淘汰）、AWM（归纳覆写）、CoALA（procedural/episodic 分类 → 固化 vs 软记）。

配套：新建全局 `revise-skill`（用本 spec 作标尺系统性订正现有 skill）。
