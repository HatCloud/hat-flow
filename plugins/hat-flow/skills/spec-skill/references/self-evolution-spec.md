# Self-Evolution Spec（spec-skill 参考）

> 从 spec-skill 正文下沉的自进化组件完整定义。spec-skill SKILL.md 的 `## Self-Evolution Capability` 指向本文件；skill-create/skill-revise 在实际给某技能搭建或订正自进化组件时按需 Read。本文件自包含——所有自进化组件已在此定义，无需依赖任何外部项目实例。

## Components

| 组件 | 形态 | 关键约束 |
|------|------|---------|
| **经验库** `references/lessons.md` | SKILL.md 启动时 `!`cat`` 注入 | 表格化（见下，含「建议出口」列）；**硬上限（默认 ≤15 条）**；运行段沉淀增长、固化段（`skill-revise` 升级后移除）+ 归纳覆写收缩；越短越健康。**这是每个技能自己的数据**（可变） |
| **摩擦临时文件** `~/.claude/.friction/<session-id>.md` | 运行时即时 append，收尾汇总后移 archive | 检测到摩擦点当场写（`hat-friction-record`）、静默自动不通知用户、不写进项目树；收尾按 `<sid>.md` 读取→蒸馏进 lessons。权威约束在 canonical 母本 |
| **冷归档** `references/lessons-archive.md` | **永不注入、永不作为路径给 model 主动读** | 被挤出经验库的条目沉这里——**不删**，仅供人工回溯 / skill-revise 复活 |
| **修订日志** `references/changelog.md` | 不注入，按需 Read，最新在最上 | **仅在 skill 定义（SKILL.md / reference / 经验库结构）被修改时**写一条，记「改了什么 + 为何」。**没改 skill 就不写**——它不是每轮运行 / dogfood 的流水账 |
| **过程准则（受管 · 全局注入）** spec-skill 的 `references/self-evolution-canonical.md` | 各技能 SKILL.md 启动时**直接 `!`cat`` / `Read` 母本的绝对路径**（`${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/references/self-evolution-canonical.md`） | **先验后做 + 裁决漏斗 + 写入闸 + 整合三机制 + changelog 纪律** 的权威文本，**唯一母本**集中在此。**全局共享**（类比 system prompt）：所有自进化技能注入同一份、**不各存副本**；自进化流程严禁改 / 删；要改规则只改母本，全体下次启动即生效。技能若有自己额外的自进化补充，另注入它自己那份，不动母本 |
| **收尾 Dogfooding**（运行段） | 流程最后一个 Phase | 复盘本轮**两类摩擦点**（①技能与实际不符 ②执行返工：凭记忆猜字段/参数/文件名导致的回改），读 `~/.claude/.friction/` 临时文件汇总→按裁决漏斗打「建议出口」标记后**只写进 lessons.md**（不在收尾改正文/reference/CLAUDE.md——固化由 `skill-revise`）+ 按需跑经验库维护。**复盘 ≠ 写 changelog**——运行段没改 skill 定义就不写 changelog |
| **回归用例（Optional）** `references/evals.md` | skill-create Phase 3 验证通过 / skill-revise 候选固化后追加 | 每条 = 当时用的 experiment（task+criteria）+ verdict 摘要；skill-revise 下次订正同一技能时在改后文本上补跑确认仍 pass，防止修订静默破坏已验证行为。markdown 表格，不引入 JSON schema。**硬上限 ≤8 条**，满后淘汰最旧 / 区分度最低者（淘汰记 changelog）——每条回归都派真实 worker，不设上限成本随修订次数线性膨胀 |

可选组件：**激进迭代期**——前 N 轮前置激进迭代 + 全程交互，稳定后收敛到每轮结尾一次。

**为何外置成全局母本**：这套过程准则对所有自进化技能都一样；手写进各 SKILL.md 正文会漂移、且被自进化流程自身改坏。收敛成单一 canonical 母本、各技能启动时注入其绝对路径（不存副本），改一处全体下次启动即生效。

## 经验库格式（表格，非自由堆叠）

```markdown
| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| 一句话经验（可带 emoji 标类别） | 1-10 | 正文/reference/CLAUDE.md/lessons | case/日期 | 日期 |
```

不记精确命中计数（agent 自报不可靠、逐步记账必被省略）；改用**重要度**（创建时打 1-10）+ **上次命中**（recency，整合时粗判刷新）。**建议出口**列由运行段按裁决漏斗打标，供 `skill-revise` 固化段分流（升级进正文/reference/CLAUDE.md 或就地留 lessons）。lessons.md 头部另记一行 `上次整合: YYYY-MM-DD`——整合触发判据据它 + 硬上限判定（防膨胀机制权威文本见 canonical 母本）。

## 编排族的经验归属（orchestrator + workers）

一个技能负责**编排**、把具体活派给一组子技能执行（如 `task` 编排 `task-init / task-design / task-execute / …`），这叫**编排族**。族里一道任务由多个技能重合完成，「这条经验落哪个技能」会出现单技能场景没有的歧义。判据只有一条：

> **经验归属 = 它下次会被检索、被应用的那个决策点，不是它被发现的地方。**
> 自检：「下次这条经验，该在**谁**的**哪个决策点**被读到？」——落在那个技能，而非偶然发现它的那次流程所在的技能。

三条推论覆盖绝大多数情况：

| 经验性质 | 例 | 落点 |
|---|---|---|
| **执行细节** | 「执行子任务时跑测试前要先 source 环境」 | 子技能——即使是在一次完整编排流程里发现的，它唯一的复用点就是那个子技能 |
| **编排决策** | 「design 没过审不该放进 plan」「某类任务该跳过 test 阶段」 | orchestrator——选谁 / 排序 / 分支 / 何时停 |
| **交接契约** | 「plan 传给 execute 的产物必须含验证命令」 | 看谁把关：把关动作在编排层→orchestrator；是子技能被调用时的前置假设→该子技能开头 |

orchestrator 自己也只是一个技能，**有自己的 `lessons.md`，专收编排经验**；**不给编排族另造 series 级公共经验库**（那是又一个垃圾桶入口）。每个技能各收各的，按上表分流。canonical 母本的 write-gate 含一道归属问句（「下次由哪个技能的哪个决策点读到？」），据此判定。

**编排族 worker 的 inbox 形态（`self-evolving: inbox`）**：被编排的 worker 技能自己不做运行时自进化（无 lessons 注入行、无收尾沉淀段、不加载 canonical 母本），但持有一个 `references/lessons.md` 收件箱——写入端是编排层的复盘机制（如 task 族的 retrospective 插件），读者是 skill-revise（固化进正文后移除该条，空是常态）。frontmatter 声明 `self-evolving: inbox` 使形态可被 `hat-skill-lint` 机判：inbox 形态要求 lessons.md 存在、不要求 lessons-archive.md。与 spec 类暂存 inbox 的差别只在写入端（spec 类=自身运行段；worker=编排层复盘机制）。

## When to Offer

仅对**重复使用型流程类技能**（反复处理同类任务，如 work / review / distill）主动提议**完整经验库机制**（常驻 library + 冷归档 + 整合）；**spec(Spike)类技能不设常驻经验库**，但用一个 `lessons.md` 作**暂存 inbox**——两段式运行段把候选经验沉这里（带「建议出口」标记），由 skill-revise 固化进正文后**清空**（空是常态，不做冷归档 / 整合，消费者是 skill-revise 而非自注入）；一次性工具技能默认 N/A。**所有被修改的技能都要有 changelog**（见 File Organization）。

## README.md 的历史定位（已废弃，记录供参考）

技能大多以英文写作、README 承担中文对照译文职责的时代，spec-skill 曾要求 README 是"纯中文的流程综述，覆盖目的/触发条件/核心流程/关键规则"——这个覆盖范围实质上要求 README 镜像 SKILL.md 几乎全部内容。现在正文已统一为陈述式中文，翻译职责已无意义，且这个覆盖范围本身是持续复述、注定漏同步的结构性诱因（SKILL.md 与 README.md 曾在"写入闸"语义等多处因此走样）。现行定位见 SKILL.md Required Structure 第 5 项：只做摘要 + 补充信息，不复述 Iron Laws / Process。
