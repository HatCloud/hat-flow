# Design Review Protocol

由 SKILL.md 动态路由加载。针对 design.md 文档进行结构化 review。

## Required Input

调用方必须注入以下内容，缺少任何一项则终止并报错：

| Input | Description |
|-------|-------------|
| design.md full text | 完整的设计文档内容 |
| prompt.md | 原始需求和结构化需求 |
| Round number | 1 or 2 |
| Review focus | 本轮 review 的重点描述 |

<rule>
review 开始前先检查所有必要输入，缺失任一输入即以报错终止，并列出缺失项。
Reason: 在残缺上下文上做 review 会产生 false negative，比不做 review 更糟。
</rule>

## Round 1 — Structural Completeness

round = 1 时执行本 checklist，与 Round 2 分开进行。

逐条检查以下维度，对每个发现的问题按 SKILL.md Output Format 输出：

### Checklist

1. **Requirement Coverage** — design.md 中的每个 Goal 是否有对应的 Architecture/Component 描述？逐条对照 prompt.md 的 Structured Requirement 与 design.md 的 Goals。
2. **Section Coherence** — 各节之间是否有逻辑间隙？Architecture 描述的组件是否都在后续节中展开？Data flow 是否与 Architecture 一致？
3. **Acceptance Tests Alignment** — design.md 的 Acceptance Tests 是否覆盖所有 Goals？是否有 Goal 没有对应的验收项？
4. **Prompt Alignment** — prompt.md 中原始需求的每个要素（Goal、Scope、Expected Result）是否都在设计中体现？是否有偏离？
5. **Goals vs Non-Goals Boundary** — Goals 和 Non-Goals 是否有交叉？是否有需求既不在 Goals 也不在 Non-Goals 中（遗漏）？
6. **Error Handling Coverage** — Error Handling 节是否覆盖了 Architecture 中描述的所有异常路径？是否有组件交互的错误场景未被提及？

## Round 2 — Adversarial Review

round = 2 时执行本 checklist，与 Round 1 分开进行。

以对抗性思维审视设计，主动寻找问题而非确认正确性：

### Checklist

1. **Failure Scenarios** — 列出至少 3 个可能导致实现失败的场景。对于每个场景，评估设计是否有应对措施。
2. **Edge Cases** — 检查边界情况的处理：空输入、超大输入、并发访问、权限不足、网络中断。
3. **Undeclared Assumptions** — 设计隐含了哪些未明确声明的假设？环境依赖、文件存在性、API 可用性、特定运行时版本。
4. **Rollback Path** — 如果实现中途失败，如何恢复到之前的状态？是否有不可逆的操作未标注？
5. **Over-engineering Check** — 设计中是否有可以用更简单方案达到相同效果的部分？是否引入了不必要的抽象层？
6. **Security Risks** — 是否存在敏感数据暴露、未授权操作、注入风险等安全问题？

## Confidence Guidance

Confidence 评分参考。每个区间附锚定示例帮助校准——偏高的 confidence 会掩盖不确定性：

| Confidence | 适用场景 | 锚定示例 |
|------------|---------|---------|
| 95+ | 可证伪的矛盾：文档 A 节和 B 节直接冲突 | "Goals 写不支持 X，Architecture 描述了 X 的实现" |
| 85-94 | 确认的结构性缺失：某个 Goal 没有对应的 Architecture 描述 | "Goal #3 '支持 Full 模式'在 Architecture 中未展开" |
| 75-84 | 潜在问题：需要推理才能发现的间隙或隐含假设 | "Error Handling 未覆盖调用方传入无效轮次的场景" |
| 60-74 | 风格或表述建议：不影响功能的改进 | "Non-Goals 的表述与 Goals 格式不一致" |
| <60 | 纯推测：无法从文档中确认，仅凭经验猜测 | "未来可能需要支持 Round 3" |

Confidence < 80 的 issue 放入 Low Confidence 节。犹豫该给 80 还是 75 时选 75——低估确定性优于高估。

---

## 变体注记质量审查（轻量，嵌入 Round 1）

仅当 design.md 含变体注记（variant note）时执行此一条检查，不增加额外 review 轮次：

1. **变体注记不过度限制** — 若存在变体注记，是否提供了 ≥2 种合理的实现路径？是否存在仅列出一种实现路径而实质限制实现自由度的措辞？过度限制按 confidence 锚定表定级报告。
