# spec-skill 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

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
