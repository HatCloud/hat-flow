---
name: brainstorm
description: "Use when 用户的想法模糊/初级、需要把它扩充为详尽需求，或用户主动要头脑风暴/完善需求；可独立触发，也被 task-init 低分路径与 skill-create Phase 1 调用。Do NOT use when 需求已清晰具体、只需直接执行，或属纯外观性 trivial 改动。触发词: \"头脑风暴\", \"brainstorm\", \"帮我想想\", \"完善需求\", \"想法还不成熟\""
user-invocable: true
self-evolving: true
---

# Brainstorm — 轻量苏格拉底式需求头脑风暴

把模糊/初级的想法用逐问苏格拉底式对话扩充为合理详尽的需求；可独立 `/brainstorm` 触发，也被 task-init 低分路径调用。轻封装——无多阶段/模板/对抗 review 的重型脚手架。

**Announce at start:** "Using brainstorm to 扩充需求。"

## 启动注入（self-evolution）

- 经验库（本技能数据，可变）：!`cat "${CLAUDE_SKILL_DIR}/references/lessons.md" 2>/dev/null || echo "(经验库暂缺)"`
- 自进化过程准则（全局母本，受管·勿改）：!`cat "${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/references/self-evolution-canonical.md" 2>/dev/null || echo "(母本未注入)"`

> 调用载体：被编排方（task-init / skill-create）以 Read 方式加载本文件时，上方注入行不展开——此时先手动 Read 上述两个文件再进入流程（`!`cat`` 只在 Skill / 斜杠激活路径生效）。

## Iron Laws

<rule>
头脑风暴每轮只问一个聚焦问题（优先多选）；需深入则拆成多个单问，不批量发问。
Reason: 一次一问是需求澄清/elicitation 的实证最佳实践——批量发问会压垮用户、稀释思考深度（Superpowers one-question-per-message 与 LLMREI 论文双源印证）。
</rule>

<rule>
联网补全先经许可：循环开始先询问是否允许联网，许可前不调用 web-research。无人值守模式默认允许。
Reason: 联网有成本与外部依赖，是否引入由用户掌控；无人值守无人应答时按默认放行以不阻塞。
</rule>

<rule>
只有 web-research 返回 verification==verified 的 findings 才作需求扩充依据；tentative/opinion/filtered_out 仅作"待验证"备注。Tier/verification 判定权威在 web-research 引擎，本技能不复述、不自定义。
Reason: 防 dual-definition drift；未经核实的外部 claim 当作决策依据会把噪音写进需求。
</rule>

<rule>
被编排方（task-init / skill-create）调用时产物回流到内存态结构化需求，不直接写盘（落盘由调用方各自负责：task-init 1f 原子写 prompt.md、skill-create Phase 1 收入其需求上下文）；仅在收敛时一次性替换内存态。
Reason: 调用方的落盘点都在本技能返回之后；过程中写文件会产生半成品、违背原子回流，也会与调用方的落盘职责冲突。
</rule>

## Process

### Step 1: 进入与定调

- 读取输入：独立触发取用户当前想法；被编排方调用取其传入的内存态需求（task-init 附 1b.2 健康度表；skill-create 传技能想法初稿）。
- 一句话复述当前理解，声明本轮目标 = 把它扩充到"高质量"（消除原低分维度）。
- 进入前存一份当前需求快照（供中途退出回滚）。

### Step 2: 联网许可门

- **[Interactive]** AskUserQuestion：是否允许联网补全外部信息（已知解法 / 选型 / 最佳实践 / 版本差异）？是 / 否。
- **[Unattended]** 默认允许；被编排方调用且有 task-folder 时记入 `{task-folder}/unattended-decisions.md`，独立触发的无人值守场景把该决策记录并入最终输出文本。

### Step 3: 逐问苏格拉底循环（核心）

每轮：
1. 针对当前最大的不确定 / 缺口，提**一个**聚焦问题（优先多选）。
2. 等用户回答（**[Unattended]** 派 Requirements Analyst subagent 作答，见 UNATTENDED_PROTOCOL §7）。
3. 按需联网（已许可时）：按 `references/web-research-contract.md` 构造 `WebResearchRequest`（`depth:"quick"`、单一 `research_question`、`local_context` 带已知结论、`unattended` 透传），只采信 verified findings，`coverage_gaps` 转下一轮提问。联网失败 / 配额耗尽 → 引擎软着陆降级，本轮不阻断、按已有信息继续提问。
4. 把新结论并入内存态需求草稿。
5. 进入 Step 4 收敛判定。

### Step 4: 收敛（双触发）

- **被动**：用户任意轮说"够了 / 继续 / 可以了"→ 收敛。
- **主动**：每轮后重评 7+1 维度健康度（清晰度 / 可验证性 / 完整性 / 项目匹配度 / 外部依赖 / 歧义度 / 范围界定 / 模型能力，借 placeholder / 矛盾 / 歧义 / scope 四项自审）。一旦从低分回到高分（0 个 ❌ 且原低分维度已解决）→ **主动询问**"需求已达高质量，是否就此收敛？"，不干等用户喊停。
- **[Unattended] 确定性退出 cap**：最多 5 轮逐问 + 最多 3 次 web-research；达 cap 仍未收敛 → 按当前置信度产出"最佳扩充假设"、记 `unattended-decisions.md`（含未解决项）、软着陆收敛，不无限发散。

### Step 5: 产物回写

- **独立触发**：输出扩充后的结构化需求文本给用户，不写任何任务文件。
- **被编排方调用**：收敛时原子替换内存态 Structured Requirement + 追加内存态 `## Brainstorm Results`（含联网 verified 事实带源），由调用方落盘（task-init 1f / skill-create Phase 1）。

### Mid-session Exit

用户收敛前喊停 → AskUserQuestion 三选：① 丢弃（恢复进入前快照）② 保存当前摘要为"未收敛草稿" ③ 继续。被 task-init 调用时丢弃 / 保存后回到调用点继续（不重入本技能）；独立触发仅输出已得摘要。

## Mandatory Stop Points

| Step | When | Ask | [Unattended] |
|---|---|---|---|
| 2 | 循环开始 | 是否允许联网补全 | 默认允许 |
| 3 | 每轮提问 | 一个聚焦问题（优先多选） | 派 Requirements Analyst subagent 作答 |
| 4 | 质量回到高分 | 是否就此收敛 | cap 内自动续，达 cap 软着陆 |
| Exit | 用户中途喊停 | 丢弃 / 保存 / 继续 | N/A（不主动喊停） |

## Dependencies

- 消费: web-research 引擎（经 WebResearchRequest/Result 契约，见 `references/web-research-contract.md`）
- 调用方: task-init 1b.2b（低分门控，经 Read 协议 inline 调用）、skill-create Phase 1（无条件需求扩充，经 Read 调用）
- 条件加载: `${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`（被 task-init 无人值守调用、或本技能检测到 unattended 状态时）
- 自进化母本: `spec-skill/references/self-evolution-canonical.md`（启动注入）

## VDD 策略

N/A——对话类技能、无代码产出，不适用 Full/Lite TDD；正确性靠收敛后的需求质量自审（7+1 维度）与下游 Design 阶段验证。

## 自进化

本技能 self-evolving。运行段把经验沉进 `references/lessons.md`（带「建议出口」标记），固化由 `skill-revise` 双盲测试后执行；运行段不改正文。过程准则以启动注入的全局母本为准。
