---
name: spec-skill
user-invocable: false
word-budget: 2000
description: "ALWAYS read this BEFORE authoring, creating, scaffolding, editing, modifying, or reviewing ANY Claude Code skill or SKILL.md — it is the single authoritative spec for all skill work. Use the moment a task involves a skill's structure, frontmatter, language/bilingual strategy, self-evolution components, or quality checklist. Do NOT use for non-skill files. 触发词: \"写个 skill\", \"建一个 skill\", \"新建技能\", \"做个技能\", \"脚手架技能\", \"改一下 skill\", \"修改技能\", \"让技能合规\", \"review 技能\", \"scaffold/author a skill\""
---

# Skill Specification Guide

Skill 不是操作手册，而是**行为约束系统**——不仅定义"做什么"，还要阻止"model 会怎么绕过"。

本 skill 覆盖 skill 的创建、修改和 review。spec 类（`spec-` 前缀，如本 skill）和流程类（如 task、distill）结构要求基本相同，区别在于内容侧重：spec 类偏规则/标准，流程类偏步骤/分支。

**入口分流（三分流）**：从零建新技能 → `skill-create`（纯编排前门，Phase 2 读本 skill 作权威生成结构；本 skill 在新建场景退为被调用的规范权威）；改本规范本身 → 本 skill；**修改既有技能的正文 / 流程、或固化某技能 lessons 进流程 → `skill-revise`**（带对比实验测试门，是改既有技能正文的唯一入口）。运行段（dogfooding / 收尾）对既有技能只把经验沉进 lessons、不直接改正文。用户主动要建新技能时提醒走 `skill-create`、要改既有技能时提醒走 `skill-revise`。这 5 个技能（本 skill、`spec-task-skill`、`skill-create`、`skill-revise`、`skill-test`）共同遵守的跨技能设计哲学见 `references/meta-skill-philosophy.md`（供改动它们时参考，非运行时必读）。

**Announce at start:** "Using spec-skill to [write/modify/review] the skill."

## Required Structure

每个 skill 必须包含以下元素：

### 1. Frontmatter

```yaml
---
name: skill-name
description: Use when [trigger]. Do NOT use when [exclusion]. 触发词: "中文触发词1", "中文触发词2"
self-evolving: true   # 可选：开启自进化能力时加（见下方 Self-Evolution Capability）
user-invocable: false # 可选：Claude Code 原生字段，见下段判据；缺省即可被用户 / 调用
word-budget: 1000     # 可选：体量档位（500 缺省 / 1000 / 2000 / exempt），判据见 Length Budget
---
```

description 以 "Use when..." 开头，含触发条件和排除条件，**必须包含中文触发词**（帮助 Claude 匹配中文用户意图），不超过 500 字符，**不要概述流程**。

<rule>
description 只陈述何时使用该 skill，不概述其 workflow 或步骤。
Reason: description 一旦概述流程，Claude 会把它当捷径照着走、跳过阅读 skill 正文。真实案例：description 写「code review between tasks」时，即使正文规定两轮（先 spec compliance、再 code quality），Claude 也只做了一轮；改成纯触发条件（"Use when executing implementation plans"）后，Claude 才去读正文并跑完两轮 review。
</rule>

`user-invocable: false` 判据——不适合用户单独直接调用的技能：① **spec 类**（靠触发词激活而非 `/`）；② **被编排器派发的 worker**（如 task 族的 init/design/plan/execute/test/revise）；③ **subagent-only / 内部委托工具**（如 reviewer）。面向用户的入口与生命周期命令（如 `task`、`task-end`）保持默认可见。判据：用户会不会主动敲 `/<name>` 来用它？不会 → `false`。**review 不得把它当违规字段误删**——它是合法可选项，隐藏后仍能被 description / 其它技能调用。

### 2. Overview + Announce

```markdown
# Skill Name

一句话描述这个 skill 做什么、不做什么。（用户配置语言）

**Announce at start:** "Using [skill-name] to [purpose]."
```

Overview 用用户配置语言。**不在每个 skill 写 LANGUAGE RULE 块**——面向用户的输出语言由项目 `CLAUDE.md` 单一固定，per-skill 重复冗余且易漂移。

### 3. Iron Laws

在关键流程节点使用 `<rule>` 标签标记不可违反的规则，措辞用 Title Case（不用 ALL CAPS），每条必须附 Reason。详见下方 Constraint Mechanism Guide。

### 4. Process

每个步骤需要包含：触发条件、完成条件、失败处理、用户确认点 (AskUserQuestion)。

### 5. README.md

每个 skill 须有配套 `README.md`，职责只有两项：**① 3-5 句摘要**（这是什么、为什么存在）；**② SKILL.md 正文放不下 / 不适合放的补充信息**（设计背景、历史决策、示例、外部链接）。不复述 Iron Laws / Process 步骤细节——README 不是 SKILL.md 的镜像或译文（历史沿革见 `references/self-evolution-spec.md` 末尾）。

### 6. Dependencies

```markdown
## Dependencies
- 预注入: LINEAR_PROTOCOL.md, DESIGN_PROTOCOL.md
- 调用: distill skill (Step 2.6)
- 引用: spec-git（commit 规范）
```

帮助维护者了解改动的影响范围。

### 7. Permission Constraints (Optional)

如果 skill 涉及文件读写，建议声明权限边界，例：`Write-only Inbox/distilled/`、`Read-only Cards/`。

---

## 语言策略

核心：**正文与约束都用陈述式中文；仅技术标识符 / 工具名 / 代码 / 路径 / 章节锚点用英文。** 约束（含 Reason）写成事实状态的中文，不靠 ALL-CAPS / NEVER 的嗓门[^lang]。判断口诀：这句是**给模型的硬约束**，还是**给人读的描述**？两者都写成陈述式中文，仅标识符 / 代码 / 路径用英文。

[^lang]: EN/ZH 指令遵从差真实但中等、前沿模型缩小；declarative 改写降低跨语言依赖。证据基见 `references/wording-evidence.md`。

---

## Constraint Mechanism Guide

### Constraint Tiers

| 层级 | 格式 | 用途 |
|------|------|------|
| `<HARD-GATE>` | XML 标签 + 中文正文 | **绝对不可绕过**的阻断点——跳过会让下游产物 / 检查**静默失效**。必须写明阻断后果 |
| `<rule>` | XML 标签 + 中文正文 | 违反会造成不可逆损害的铁律 |
| **Bold rules** | 加粗规则名 + 中文解释 | 一般性强调 |

`<rule>` 表达"不该违反"；`<HARD-GATE>` 表达"违反则后续步骤无意义"——判据：跳过是否让下游**静默失效**、是否必须在**当前 turn** 完成、是否属"agent 凭记忆即兴、声称做了实际没做"这类元 bug。

<rule>
违反规则的字面即违反规则的精神。
Reason: agent 在压力下会寻找字面漏洞（「规则说的是 X，但严格讲这是 Y」）来规避意图。如果某种对规则的解读让你得以跳过该规则本要强制的工作，那种解读就是错的。
</rule>

### 措辞准则（陈述式优先）

核心：**强语气 ≠ 强约束**。约束默认写成「世界的状态」；祈使 / 强调留给少数真硬约束。各条证据基（一手来源引用）见 `references/wording-evidence.md`。

1. **陈述式默认** — 约束写成事实状态（`X: disabled` / `Required: Y`），而非 `NEVER X` / `ALWAYS Y`。硬约束 / 安全 / agentic 坚持仍可用祈使；保留的硬否定放段落末尾 + 客观。
2. **去强调通胀** — 不堆 IMPORTANT / CRITICAL / MUST，不用 ALL-CAPS 强调，一句清楚的陈述通常就够。
3. **附 Reason** — 非显然规则配一句原因，模型从解释泛化。
4. **具体非模糊** — 形容词换可测量标准：`Response budget: 2-3 句` 优于「保持简洁」。
5. **规则少而不冲突** — 每条约束只写一次，不同层级提供不同信息。
6. **Trailing reminder** — 流程末尾重复关键终态约束（如「展示 checklist」）。
7. **结构承重** — 一致分隔 / 表格 / 有序步骤，刻意且统一。

---

## Pre-injection Strategy

| 条件 | 策略 |
|------|------|
| 文件内容直接控制 model 当前步骤行为 / 传递给 subagent 的 prompt | `!`cat`` 预注入 |
| 文件仅在特定条件分支使用，体积大 | 按需 Read |
| 文件是脚本，由 Bash 执行 | 路径引用即可 |

**口诀**：model 需要阅读才能正确行动 → 预注入；model 只需要知道路径 → 引用。

<rule>
关键子协议文件须经 `!`cat`` 预注入，以保证它们一定被读到。
Reason: 模型有时会跳过阅读以路径引用的文件，导致 silent failure。确保文件被读到比省 token 更重要。
</rule>

跨模型兼容性（指令密度 / 停点 / 探索预算）、Flowchart 用法完整判据见 `references/advanced-features.md`。

---

## Design Principles

| Principle | Rule |
|-----------|------|
| **Evidence Over Claims** | 运行命令、读输出、确认结果；不写「应该没问题」式断言。 |
| **Context Isolation** | 每个 subagent 只给最小必要信息，no session history。 |
| **Bite-Sized Tasks** | 每步 2-5 分钟，一步一个动作。 |
| **User-Verified Completion** | Agent 不替代用户测试；展示产物后停下等待。 |
| **YAGNI** | 没有明确需求就不加功能。 |
| **No Redundant Constraints** | 每条约束只写一次。不同层级必须提供不同信息，not repeat the same rule。 |

**压缩 / token 优化**额外对照 `references/optimization-rubric.md`——Anthropic 官方文档一手鉴真的 11 条优化准则 + Source Ledger，压缩或 review 既有 skill 时逐条过。已验证设计模式（Verification-Driven Development、Mandatory Stop Points、Two-Stage Review、Implementer States、Scope Freeze、Confirmation Loop）见 `references/proven-patterns.md`，按需 Read。

## Token Efficiency

Context is a finite, critical resource. 用简单直接的语言，以合适的抽象层级呈现：交叉引用而非重复、一个好例子 > 三个平庸例子、表格 > 段落、避免过于复杂的硬编码逻辑。

### Length Budget（三档 + 豁免，frontmatter 声明制）

预算档位由 frontmatter `word-budget: 500|1000|2000|exempt` 声明，缺省 500；`bin/hat-skill-lint` 按声明档检查（超档 WARN、非法取值 FAIL、exempt 仅报词数）。预算是上限不是目标，不设 500 以下档位。

| 档位 | 判据 |
|------|------|
| **500**（默认，无需声明） | 单一职责工具技能 |
| **1000**（声明） | 多阶段流程技能，仅在被调用时加载，且论证 / 示例已下沉 `references/` 后正文仍需此量 |
| **2000**（声明） | 编排器 / 生命周期一体型 / 权威规范类（被其他技能全文预注入消费——正文必须完整可用，预算约束的是「不该在正文的内容」而非砍掉操作性规则） |
| **exempt**（声明） | 极少数「一个任务只落在这一个技能上」的巨型编排器（当前仅 task）；lint 仅报词数，增长仍可见 |

升档或豁免须在该技能 `references/changelog.md` 记一条理由；skill-revise / review 时档位可被挑战——「超了」本身不构成升档理由，升 1000 的前提是下沉已经做完。getting-started 类工作流条目另守 <150 words/条（进入每次对话）。

超预算时：细节移到 `references/` 子文件、交叉引用替代重复、压缩示例。验证：`wc -w skills/path/SKILL.md`，或跑 `bin/hat-skill-lint <skill-dir>` 做结构化自检（含此项）。

<rule>
跨 skill 引用使用纯文本路径或 skill 名；该文件只在真正需要时才加载。
Reason: `@path/to/file` 会立即强制加载文件，在尚未用到前就烧掉 200k+ context。只有同目录、用于预注入的关键子文件才用 `!`cat``。
</rule>

## Advanced Features

机制 / 进阶参考下沉到 `references/advanced-features.md`（按需 Read）：Cross-Model Compatibility、Dynamic Injection（`!`command`` + `${CLAUDE_SKILL_DIR}` 路径约定）、Dynamic Routing、Sub-Files Strategy、Subagent Collaboration、Process Review Loop、Flowchart Usage。

<rule>
skill 内容不得包含具体项目信息或硬编码的本地/绝对路径（如 `~/Projects/<name>/...`、`/Users/<you>/...`）。使用 `${CLAUDE_SKILL_DIR}` 或相对于它的路径。项目级 skill 可引用其自身项目（经相对路径），但绝不引用另一个项目。
Reason: 硬编码本地路径会让 skill 无法分享且脆弱——项目一旦移动或他人安装，每一处这类引用都会断。可移植的引用能在迁移和分享后存活。（`.claude/skills/` 这类通用框架路径没问题；具体项目根则不行。）
</rule>

---

## Self-Evolution Capability

自进化技能从自身**每次运行**中沉淀经验、持续改进，而非一份静态文档。`self-evolving: true`（frontmatter）是开关信号。完整组件定义（经验库 / 摩擦文件 / 冷归档 / changelog / 编排族经验归属 / 何时开启 / 回归用例 evals.md）见 `references/self-evolution-spec.md`——skill-create 搭建、skill-revise 订正自进化组件时按需 Read。

<rule>
自进化过程准则（pre-flight verification + decision funnel + write-gate + consolidation + changelog discipline）集中存放于 spec-skill 下的单一 canonical 母本（`references/self-evolution-canonical.md`）。每个 self-evolving 技能在启动时直接以 `!`cat``（an alternate runtime 兼容技能则用 `Read`）注入母本的绝对路径；不保留各技能副本。把这些规则手写进某技能的 SKILL.md 正文，以及从自进化流程中修改母本，都不在范围内。
Reason: 跨技能手工复制的同一套过程准则会彼此漂移，并被它们本要约束的那个流程改坏。一份 canonical 母本经绝对路径注入到每个技能，既保证一致性，又让规则改动在下一次运行时全体生效——无需同步任何副本。
</rule>

<rule>
创建或修改重复使用型（流程类）技能时，经 AskUserQuestion 询问用户是否加入完整自进化能力。若是，脚手架出各组件并设 `self-evolving: true`。spec 类技能不设常驻经验库，但保留一个 `lessons.md` 作暂存 inbox：运行段沉候选（带「建议出口」标记）、skill-revise 固化进正文后清空，不做冷归档 / 整合、不自注入。
Reason: 两段式自进化要求运行段「只沉 lessons、不直接改正文」对所有技能统一——spec 类若完全没有 lessons.md，其运行段经验就无处可沉（实测 gap：「改 plugin 须重生 golden」这类经验卡住）。inbox 是 transient 收件箱、非常驻 library，固化即清空，不构成「垃圾桶」；它的读者是 skill-revise 的固化端，故不进 spec 类自身的启动注入。
</rule>

---

## Patterns（正确默认）

直接陈述应当如何，无需禁止式对照：

- **行为约束系统**：skill 是规则 + 门禁，不是 cookbook 式命令序列。
- **动态检测**：路径 / 版本从项目状态读取（Dynamic Injection，见 `references/advanced-features.md`），不硬编码。
- **强制而非建议**：硬约束用 `<rule>` / bold rule，不用「suggest」。
- **精简骨架**：主 SKILL.md 留骨架，细节进子协议文件，守长度预算（见 Token Efficiency）。
- **每步含失败处理**。
- **预判绕过**：写 skill 时想清 model 会怎么合理化跳步，把这些失败点转成正文的陈述式规则（作者侧头脑风暴，本身不必落进 SKILL.md）。
- **约束匹配模型能力**：越强的模型约束越简；过度约束致分布偏移（Prompting Inversion，见 `references/advanced-features.md` ## Subagent Collaboration）。

---

## Dogfooding

Skill 写完 / 改完后，必须用它跑一次真实任务来验证。目的不是"测试通过"，而是以用户视角找出摩擦点和遗漏。发现的问题应立即修复，而非记录到 debt。具体执行方式（pressure scenario、worktree 隔离 / dry run、检查点问题清单）见 `references/proven-patterns.md`。

**实证验证（尽量，非必须）**：新写或改一段技能文本时，尽量用 `skill-test` 做实证验证——把它经多 provider 多轮池化加权裁决（pass/fail/signal），用证据判断「这段技能真能引导 worker 做对」，而非只凭主观读一遍。

### Self-Compliance Check

Skill 修改完成后，用自身 Checklist 逐项审核。这既是验收步骤（确保改动不破坏已有规范），也是 dogfooding 的一种形式（检验 Checklist 本身是否完备）。

不合规项必须修复后才算完成。如果发现 Checklist 本身有遗漏，同时补充。

---

## Dependencies

- 引用: PLAN_PROMPT.md（VDD 模板）
- 无预注入依赖
- 无 skill 调用依赖

## File Organization

通用 skill 文件结构（约定文件名，路径相对技能目录）：

```
skills/skill-name/
  SKILL.md                  # 主流程/规范（中文正文 + 语域中性硬约束）
  README.md                 # 摘要 + 补充信息（纯中文，不是 SKILL.md 的镜像/译文）
  references/               # Optional: 子协议 / 标准 / 经验库 / 日志
    changelog.md            # 修订日志（被修改的 skill 通用，不注入，最新在最上，仅改才写）
    <protocol>.md           # 子协议（按预注入策略 !`cat` 或按需 Read）
    lessons.md              # 经验库（仅流程类/self-evolving）：!`cat` 注入，表格化，硬上限
    lessons-archive.md      # 冷归档（仅流程类）：永不注入/引用
    evals.md                # Optional：技能行为回归用例（task+criteria+verdict），经 skill-create/skill-revise 验证通过后追加，供下次修订回归复测；硬上限 ≤8 条，满后淘汰最旧/区分度最低者（淘汰记 changelog）
  scripts/                  # Optional: 脚本；改动逻辑须配 `bin/test_<script>.py`（pytest）
```
（自进化技能**不再保存** `references/self-evolution.md` 副本——过程准则统一注入全局母本，见上。）

> 自进化技能的 SKILL.md 启动注入区应有**两行注入**：① `${CLAUDE_SKILL_DIR}/references/lessons.md`（本技能数据，可变）② 过程准则**全局母本**的绝对路径 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/references/self-evolution-canonical.md`（受管，勿改）。①用 `${CLAUDE_SKILL_DIR}` 引用本技能自有；②用绝对路径直引母本、**不各存副本**，改母本即全体生效。an alternate runtime 兼容技能两行都改用 `Read` + 绝对路径（禁 `!`cat`` / `${CLAUDE_SKILL_DIR}`）。

### 按类型分（流程类 vs spec(Spike)类）

| 类型 | changelog | lessons.md + 冷归档 |
|------|-----------|---------------------|
| **流程类**（work / task / review / distill 等反复处理同类任务） | ✅ | ✅ 完整自进化机制（见 Self-Evolution Capability） |
| **spec(Spike)类**（`spec-*`、规范/标准类） | ✅ | 🔄 **暂存 inbox**：`lessons.md` 仅作运行段候选收件箱（带「建议出口」标记），skill-revise 固化进正文后**清空**；不做常驻 library / 冷归档 / 整合（空是常态），不自注入（读者是 skill-revise） |
| **一次性工具类** | 改了就记 | ❌ |

<rule>
每个被修改的 skill 都须维护一份 `references/changelog.md`（最新在最上），记录每次改动及其原因。
Reason: 没有每技能的 modification log 就没有 rollback trail——一旦某次编辑破坏了行为，你无从得知改了什么、也无法还原意图。这适用于所有类型的 skill，不只是 self-evolving 的。
</rule>

### Naming: ASCII Only

文件名与文件夹名一律用 **ASCII 英文 kebab-case**，禁止中文 / 空格 / 点（概念名在正文里可用用户配置语言，落到磁盘的名字必须英文）。通用约定译名：经验库→`lessons.md`、冷归档→`lessons-archive.md`、修订日志→`changelog.md`、子协议→`<name>-protocol.md`。项目特有文件名（如某甲方标准、报告模板、产出文件夹）由该项目自己的规范定义，不进本全局 spec。

<rule>
文件名与文件夹名必须为 ASCII（英文 kebab-case）。名字里绝不使用用户配置的语言字符、空格或点。
Reason: 非 ASCII 路径会破坏工具链、跨平台同步以及 Claude Code 的 memory path 编码（它把 `/` 和 `.` 映射为 `-`）。中文文件名还会让 grep/脚本变脆。概念名在正文里可保留中文；落到磁盘的名字必须是英文。
</rule>

## Checklist — Before Creating or Modifying a Skill

- [ ] 关键节点有 Iron Laws（`<rule>` 标签，正文中文）？
- [ ] 约束陈述式（写成事实状态；祈使 / 强调只留少数真硬约束，无 NEVER / ALL-CAPS 堆砌）？
- [ ] 每步有失败处理？
- [ ] 用户决策点有 AskUserQuestion？
- [ ] 无硬编码路径 / 版本、无具体项目信息 / 本地绝对路径 / 跨项目引用（用 `${CLAUDE_SKILL_DIR}` / 相对路径；项目级 skill 只引用自身项目）？
- [ ] 文件名 / 文件夹名全 ASCII 英文（无中文 / 空格 / 点）？
- [ ] description 含中文触发词、只写触发条件不概述流程？
- [ ] 语言：描述 + 约束正文全中文，仅标识符 / 代码 / 路径英文，无 per-skill LANGUAGE RULE 块（输出语言由项目 CLAUDE.md 固定）？
- [ ] 关键子协议文件经 `!`cat`` 预注入？
- [ ] Dependencies 已声明？
- [ ] README.md 已创建 / 更新，且只做摘要 + 补充信息、不镜像 / 翻译 SKILL.md？
- [ ] `references/changelog.md` 存在且本次改动已记一条（最新在最上）？
- [ ] 文件结构符合 File Organization？经验库归属按类型正确（流程类才有完整 lessons.md + 冷归档；**spec 类仅 lessons.md 暂存 inbox + changelog**；一次性工具类都没有）？
- [ ] Dogfooding 已计划？
- [ ] 用户决策点已定义为 Mandatory Stop Points（若有）？
- [ ] VDD 策略已注明（Full TDD / Lite TDD / N/A）？
- [ ] 重复使用型流程类：已用 AskUserQuestion 询问是否加入自进化能力？
- [ ] 若 `self-evolving: true`：自有组件齐备（经验库表格化 + 硬上限 / 冷归档 / 修订日志 / 收尾 Dogfooding，见 `references/self-evolution-spec.md`）；过程准则由启动注入区直接注入全局母本绝对路径（`spec-skill/references/self-evolution-canonical.md`），非各存副本、非手写进正文？
- [ ] frontmatter 的 `self-evolving` 标记与实际组件状态一致（不空挂）？
- [ ] 若属编排族：经验按「检索点归属」分流（执行细节→worker，编排决策→orchestrator），无 series 级公共经验库，无同一软经验跨技能镜像？
- [ ] 若技能带 `scripts/` 或依赖 `bin/` 下的脚本，改动逻辑是否配 `bin/test_<script>.py`（pytest）覆盖？
- [ ] 跑 `bin/hat-skill-lint <skill-dir>` 通过（体量预算 / frontmatter 必需字段 / self-evolving 组件一致性）？
- [ ] 若目标是 5 个元技能之一（spec-skill / spec-task-skill / skill-create / skill-revise / skill-test）：已先读 `references/meta-skill-philosophy.md`？
- [ ] Self-compliance check 通过（用本 checklist 审自身）？

---

参考来源：措辞准则证据基见 `references/wording-evidence.md`；自进化组件完整定义见 `references/self-evolution-spec.md`；进阶机制见 `references/advanced-features.md`；已验证设计模式见 `references/proven-patterns.md`。
