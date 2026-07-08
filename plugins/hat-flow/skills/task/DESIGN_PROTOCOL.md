# Design Protocol

本文件提供主 session 的完整设计阶段工作流——流程步骤、模板、复杂度矩阵、原则的**单一来源**。在 Phase 2（Design）开始时由 task-design/SKILL.md 通过 `!cat` 嵌入。主 session 直接遵循此协议——不委托 subagent。

<HARD-GATE>
推进到 Plan phase 要求设计已展示给用户并获得显式批准；在批准之前，流程停在 Plan 之外、不写任何实现代码。
Reason: 跳过批准会让未经 review 的假设直接流入实现——那是发现它们代价最高的地方。一个未获批准却静默推进的设计，会产出用户从未同意的工作，且通常不得不返工重做。
</HARD-GATE>

---

## Pattern: 每个任务都走设计流程

每个任务都走设计流程，没有例外。设计的**篇幅**由复杂度决定，**是否设计**则不取决于复杂度——再简单的任务也展示设计并获批。

"这个太简单，直接写就行"是未审假设导致返工的高发区：简单任务的设计一旦跳过，错误假设往往拖到实现甚至上线才暴露。正确做法是设计可以**短**（几句话即可），但都**展示给用户并获得批准**。

---

## Design for Isolation and Clarity

设计时把系统拆成**单一职责单元**：每个单元有定义良好的接口，能被独立理解、独立测试。

判据——每个单元都应能回答：
- **What**：它对外提供什么？（接口 / 契约）
- **How**：它内部怎么实现？（实现细节，消费者不应关心）
- **Depends on**：它依赖什么？（上游契约）

两个检验问题：
- 能否**不读内部实现**就理解这个单元的用途？（接口是否自解释）
- **改内部实现**是否会破坏消费者？（封装是否到位）

信号：**文件过大 = 职责过多**。一个文件承担多个不相关职责时，应拆分。

---

## Scope 分解先于澄清问题

在投入详细提问之前，**先评估范围**。

如果请求横跨多个独立子系统，**先建议拆分成多个任务**：在尚需分解的项目上提澄清问题，问题会散落在不该一起处理的子系统之间、浪费往返。先分解，再针对每个聚焦的子任务提问。

---

## Design Flow

按顺序执行以下步骤，每步都有明确的完成条件，逐步走完不跳步。

### Step 1: Explore Project Context

- 优先派发 **Explore subagent** 而非自己发起大量工具调用。subagent 可以将探索噪音隔离在主上下文之外。
- 如果自行探索，阅读相关源文件、文档和配置。运行 `git log --oneline -20` 了解近期变更。
- 识别现有代码风格、架构模式、命名约定。
- 读取 `{task-folder}/prompt.md` 获取结构化需求作为探索的起点。

**Exploration budget**: 超过 10 次探索性工具调用（Read / Grep / Glob / Bash）仍未形成清晰假设时，停止探索、转而向用户提一个澄清问题。漫无目的的探索浪费 token。

**API/环境验证**: 如果方案依赖特定 API 或运行时能力（原生模块、平台 API、第三方服务等），在探索阶段通过快速实验（console.log、REPL 测试等）确认其可用性和返回值，不要等到执行阶段才发现 API 不可用。

**原生依赖验证（RN 项目）**: 如果方案需要新增原生依赖（如 Skia、MMKV 等需要编译原生代码的库），在探索阶段验证：① 安装后 `pod install` / codegen 是否通过 ② dev client 能否正常编译启动。M2 教训：Skia 的 codegen 因 `balanced-match` v4 破坏性变更导致 `pod install` 失败，在执行阶段才发现，浪费大量调试时间。

**Completion condition**: 你已有足够的上下文来提出有针对性的问题（且已完成 scope 分解评估，见上方 "Scope 分解先于澄清问题"）。

### Step 1.5: Optional Web Research（联网调研）

本地探索只看项目内内容。有些需求外部信息能省掉从零探索——解 bug（网上可能已有解法）、0→1 新项目（选型 / 脚手架）、建技能、引入陌生第三方依赖（官方文档 / 最佳实践 / 版本差异）。在本地探索已建立初步图景、缺口已清楚之后插入这一步（此时调研问题问得最准）。

- **Interactive**：向用户提问（结构化选项优先）——「本地探索已完成，是否联网调研补充外部信息（已知解法 / 选型 / 最佳实践 / 版本差异）？」选项：是 / 否。bug 修复、0→1 新项目、建技能、引入陌生依赖等场景默认建议「是」；纯项目内改动默认「否」。
- **若是 → 调 `web-research` 引擎**，构造 `WebResearchRequest`：`contract_version: "1.0"`、`depth: quick`（探索阶段重时效）、`research_question` = 由缺口凝练的单一问题、`local_context` = 已探查的代码结论（避免引擎重复已知工作）。
- **折叠 `WebResearchResult`**（先断言返回的 `contract_version` major 与本协议期望一致，不符则降级只读已知字段并告警）：
  - `findings[verification==verified]` → design 探索上下文「外部技术事实」段，带源可追溯，供 Step 3 提案引用。
  - `findings` 中 `verification` 为 `tentative` 或 `opinion` 者，以及 `filtered_out[]` 数组的 claim → 仅列入探索备注「需实现期验证」，**不作为设计决策依据**（设计决策只建立在 verified 事实上）。
  - `coverage_gaps` → 转成 Step 2 的澄清问题候选。
- **不写报告文件**：task-design 只把结果折进 `design.md` 的探索段，引擎本身不落地任何文件。

**无人值守**：按 UNATTENDED_PROTOCOL 自动决策——保守档默认**跳过**联网调研，除非 `prompt.md` 显式要求外部调研；启用时给引擎传 `unattended: true`（成本封顶、档位降级）。Headless 短路：不弹门，按 prompt 信号决定跑或跳。

**Completion condition**: 已决定是否联网；若联网，结果已折进探索上下文。

### Step 2: Ask Clarifying Questions

向用户提问以理解任务。规则：

- **合并提问（最多 4 个）。** 相关的问题合并到一个 向用户提问（结构化选项优先） 中（最多 4 个）；不相关的话题分开消息提问。
- **Prefer multiple-choice**（选项 A / B / C）而非开放式问题。
- 聚焦于：目的、约束、成功标准。
- **YAGNI** — 无明确需求就不提议、不设计功能。
- 如果请求跨越多个独立子系统，在继续之前先提议拆分（见 "Scope 分解先于澄清问题"）。

**确认循环（Step 2 末必须执行）：**
澄清问题问完后，用**纯文本**（非 向用户提问（结构化选项优先））确认用户是否有补充，例如："还有需要补充的吗？"
- 用户说"没有了"/"LGTM"/"继续"/"无"等明确结束语 → 推进到 Step 3
- 用户有补充 → 收到补充内容后，重新评估是否需要更多澄清问题。若需要则继续提问，问完后再次用纯文本确认。循环直到用户明确表示没有补充。

**Completion condition**: 你已充分理解目标、约束和成功标准，可以提出解决方案，且用户已确认没有更多补充。

提问后，使用 向用户提问（结构化选项优先） 或结束你的回合等待用户回复，不自答、不替用户假设答案。

<rule>
提出问题之后，下一个动作是 向用户提问（结构化选项优先） 或结束 turn 以等待用户回复；自问自答或假定用户的答案均不在允许范围内。
Reason: 自问自答绕过了用户输入，会导致设计与用户意图不符。
</rule>

### Step 3: Propose Solutions

根据任务类型调整提案数量：

- **Bug fix with clear root cause**: 一个方案加简要说明。如果根因不确定或修复涉及重构，改为展示 2-3 个选项。
- **Feature or Refactor**: 展示 2-3 个选项，附优缺点和适用场景。以推荐选项为首，说明推荐理由。

判断标准不是"bug fix = 轻量"——如果修复需要重构模块或改变架构，按 feature 处理。

向用户展示你的方案，然后使用 向用户提问（结构化选项优先） 请用户选择或确认；用户回复前不推进。

### Step 4: Present Design Section by Section

按复杂度分组展示设计。每节/组展示后询问："这部分看起来对吗？"

- **Low 复杂度**：将相关章节合并为 2-3 组展示（如 Architecture + Components 一组，Error Handling + Testing 一组）
- **Medium/High 复杂度**：逐节展示

需覆盖的章节（根据复杂度裁剪——简单任务每节只需几句话）：

- **Architecture**: 整体结构和关键决策
- **Components**: 模块职责和接口
- **Data Flow**: 数据在模块间的流动方式
- **Error Handling**: 异常路径和回退策略
- **Testing**: 测试策略和覆盖优先级
- **Acceptance Tests**: 与用户讨论验收标准。此列表将写入 design.md（格式见 Step 5）。

详细程度：简单任务每节几句话，复杂任务每节 200-300 字。

**Acceptance Tests 讨论要点：**
- 哪些功能需要用户手动验证？
- 哪些可以通过命令/脚本自动验证？
- 每项的重要性等级（MUST / SHOULD / MAY）
- 是否有应说明的实现变体或需排除的反模式
- 每项必须可执行且可观察
- **确认 light / full 验证命令（前置到此处决定）**：与用户敲定 Execute 阶段每个 task 后跑的 light 命令、全部完成后跑的 full 命令。这些命令在此一次性确认，由 task-design Step 2e 写入 `task-config.json` 的 check 字段，供 Execute 直接读——**Execute 不再询问验证命令**（约定 9 Interaction Front-Loading）。无可自动验证项则记「无 light 验证」，Execute 静默跳过。

各节与用户讨论完毕后，进入 design.md 编写。

### Step 5: Write design.md

保存到 `.tasks/open/YYYY-MM-DD-topic/design.md`。

模板（根据复杂度裁剪——这不是一个刚性模板）：

```markdown
## Overview
一段话描述此设计要解决的问题。

## Goals / Non-Goals
- Goals: 我们要做什么
- Non-Goals: 我们不做什么

## Architecture
关键决策及其理由。

## Success Criteria
可验证的完成标准。

## Acceptance Tests
与用户确认的验收测试清单。每项形态为：
`[MUST|SHOULD|MAY] 可执行/可观察的验收项`
按需在该项下补充纯文字注记：
- 变体：允许的实现变体（自由文字）
- 反模式：应排除的实现方式（自由文字）

示例：
- [MUST] 运行 `pytest bin/ -x -q` 全部通过
- [MUST] 启动 dev client，点击保存按钮后列表出现新条目
  - 变体：保存可走本地缓存或直连后端
  - 反模式：保存后整页重载

## Out of Scope
本任务明确排除的内容。
```

**Acceptance Tests 格式规则：**
- 每项以 `[MUST]` / `[SHOULD]` / `[MAY]` 标签起头，后接一句可执行或可观察的验收项。
- 变体 / 反模式为可选的纯文字注记，不是结构化字段。
- **不含评分、不含机器评级 id、不含权重**——Acceptance Tests 是给人读的验收清单（仅 `[MUST|SHOULD|MAY]` 标签），不是机器评分表。

### Step 6: Self-Review

> 由 review plugin 的 `P2.post-design-draft` hook 执行。

当 review plugin 启用时，在 design.md 写完后运行 `hat-plugin-hook {task-folder} P2.post-design-draft`，按输出指令执行自我审查和独立 review。

当 review plugin 关闭时，执行最小化自我检查（placeholder scan + internal consistency），跳过独立 review。

### Step 6.5: Review Strategy Confirmation

> **由 review plugin 的 `P2.post-design-approved` hook 执行。**

用户确认设计后，运行 `hat-plugin-hook {task-folder} P2.post-design-approved`，按输出指令将 Review Strategy 写入 design.md 并执行复杂度评估。

### Step 7: Independent Review

> **已合并到 Step 6 的 `P2.post-design-draft` hook 中。** 不再作为独立步骤。

### Step 8: User Review

所有 review 轮次完成、review 策略写入 design.md 后，明确告知用户："Design 已完成 N 轮 review，请审核 design.md，确认后进入 planning 阶段。" 然后等待明确批准（见 HARD-GATE）。

<rule>
「显式批准」指明确的肯定回复（如 "好"、"可以"、"approved"、"LGTM"、"继续"）。沉默、仅表示收到（"收到"）、或局部反馈都不算批准。
Reason: 含糊的信号会导致过早的 phase 过渡。
</rule>

---

## Complexity Assessment

在设计获批后、进入 Plan 阶段之前执行。统一信号矩阵（含涉及模块数 / 外部 API 行）：

| Signal | Low | Medium | High |
|---|---|---|---|
| 涉及文件数 | 1-3 | 4-8 | 9+ |
| 涉及模块数 | 1 | 2-3 | 4+ |
| 外部 API/服务 | 0 | 1 | 2+ |
| 新增模块/架构 | None | Local | Cross-module |
| design.md 字数 | <500 | 500-1500 | 1500+ |

**Impact of assessment:**

- Plan subagent model: Low/Medium → Sonnet; High → Opus
- Design reviewer rounds: Low → 0; Medium → 1; High → 2
- Plan review rounds（subagent 返回后）: Low → 0; Medium → 1; High → 2（见 task SKILL.md Phase 3a）

向用户展示评估和建议。用户可以一句话覆盖。

---

## Core Principles

- **合并提问（最多 4 个）** — 相关问题合并到一个 向用户提问（结构化选项优先），不相关话题分开消息
- **YAGNI** — 无情裁剪不必要的功能
- **Explore multiple approaches** — 决定前探索多种方案
- **Validate incrementally** — 逐节验证
- **Be ready to backtrack** — 随时准备回退并重新澄清需求
