# Skill 规范指南

> AI agent 就像初级工程师——有能力，但缺乏纪律。Skill 提供纪律。

Skill 不是操作手册，而是行为约束系统——不仅定义"做什么"，还要阻止"model 会怎么绕过"。

## 适用场景

- 创建新 skill
- 修改现有 skill
- Review skill 质量

触发词：`/spec-skill`、"写个 skill"、"改一下 skill"、"新建技能"、"修改技能"、"review 技能"

## 必需结构

每个 skill 必须包含以下元素：

1. **Frontmatter** — name + description（含中文触发词）
2. **Overview + Announce + Language Rule** — 概述用用户配置语言，Announce 和 LANGUAGE RULE 用英文
3. **Red Flags 表格**（建议） — 预测 model 会怎么偷懒，全英文
4. **Iron Laws** — 用 `<rule>` 标签标记铁律，英文内容 + Reason
5. **Process** — 每步包含触发条件、完成条件、失败处理
6. **README.md** — 纯中文流程综述（就是你现在读的这个）
7. **Dependencies** — 声明预注入文件、调用的 skill、引用的规范
8. **Permission Constraints**（可选） — 文件读写权限边界

## 双语策略

核心原则：约束 model 行为的内容用英文，描述流程和解释上下文的内容用用户配置语言。

**英文保留**：
- `<rule>` 铁律块、Red Flags 表格、LANGUAGE RULE 块
- 章节标题、加粗规则名/标签
- 禁令短语（Do NOT / Never / Must）
- 停止指令

**中文**：
- 流程步骤说明、Overview 概述、解释性文字
- 给用户看的提示词、规则名后的解释

判断口诀：**"这句话是在命令 model 做/不做什么，还是在描述流程/解释原因？"** 前者英文，后者中文。

## 约束机制

三层约束，按严重程度递增：

1. **加粗规则** — 一般性强调，加粗英文规则名 + 中文解释
2. **Red Flags 表格** — 预判 model 合理化跳步的场景
3. **`<rule>` 铁律** — 违反会造成不可逆损害，XML 标签包裹

措辞要求：
- 使用 Title Case，不用 ALL CAPS（研究证明 ALL CAPS 失败率最高）
- 每条规则附 Reason（帮助 model 从原因推理泛化）
- 优先正面表述（"等用户确认后再提交" > "不要在未确认时提交"）

## 预注入策略

关键子协议文件必须通过 `!`cat`` 预注入，确保 model 一定读到。只有非关键的大型参考文档才按需加载。

判断口诀：**model 需要阅读才能正确行动 → 预注入；model 只需要知道路径 → 引用。**

## 模型能力分级

派发 subagent 时根据模型能力调整注入内容的详细度：
- 强模型（Opus）→ 精简约束 + 任务描述
- 中等模型（Sonnet）→ 详细步骤 + XML 结构化
- 弱模型（Haiku）→ 逐步指令 + trailing reminders + 更多示例

所有层级避免 ALL CAPS。差异在于详细度，不在语气强度。

## Proven Patterns

经过 dogfooding 验证的设计模式，可按需采用：

- **VDD**（Verification-Driven Development）— Full TDD（有测试框架）或 Lite TDD（无框架），共享 RED-GREEN-REFACTOR 5 步标准
- **Mandatory Stop Points** — 集中式表格列出所有用户决策点 + `<rule>` 保护
- **Two-Stage Review** — Spec Compliance 先于 Code Quality，避免在错误实现上审查代码质量
- **Implementer States** — 4 状态协作规范（DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED）
- **Scope Freeze** — 设计批准后范围变更需用户确认

## Dogfooding

Skill 写完/改完后必须跑一次真实任务验证。没有真实任务时：
- git 项目 → worktree 隔离模拟
- 非 git → dry run

修改完成后还须进行 **self-compliance check**——用自身 Checklist 逐项审核，不合规项须修复。
