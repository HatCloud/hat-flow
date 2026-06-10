# Plan Review Protocol

由 SKILL.md 动态路由加载。针对 plan.md 文档进行结构化 review。

## Required Input

调用方必须注入以下内容，缺少任何一项则终止并报错：

| Input | Description |
|-------|-------------|
| plan.md full text | 完整的实施计划内容 |
| design.md full text | 完整的设计文档（用于范围对照） |
| Review focus | review 的重点描述（可选） |

<rule>
Check all required inputs before starting review. If any input is missing, output error listing missing items and terminate immediately.
Reason: plan review without design.md cannot verify scope alignment — the most critical check.
</rule>

## Single-Pass Review

单次 pass 跑完整张 checklist——不分轮、不分维度派发。逐条检查以下维度，对每个发现的问题按 confidence 锚定表定级，再按下方 Output 与 advisory 准入规则归桶。

### Checklist

1. **Task Ordering** — 是否存在依赖倒置？task N 是否引用了 task N+1 才会创建的文件或产物？依赖链是否为 DAG（无环）？
2. **Explicit Dependencies** — 每个 task 的 **Files** 列表中，如果某文件由前序 task 创建，是否明确标注了依赖关系？
3. **File Path Accuracy** — 所有文件路径是否与 design.md Architecture/文件结构 中的定义一致？是否有拼写错误或路径不存在？
4. **Scope Consistency** — plan 是否遗漏了 design.md 中的某个需求？是否有超出 design.md 范围的 task（scope creep）？逐条对照 design.md Goals。
5. **Verification Coverage** — 每个 task 是否有验证步骤？验证步骤是否能真正检测该 task 的产物（而非泛泛的"检查是否正确"）？
6. **Step Granularity** — 每步是否为单一动作？是否有步骤需要超过 5 分钟或包含多个独立操作？
7. **Forbidden Patterns Scan** — 扫描禁用模式，命中则为阻断级问题。模式清单以单一来源为准：见 `${CLAUDE_PLUGIN_ROOT}/skills/task/PLAN_PROMPT.md ## No Placeholders — Forbidden Patterns`（不在此重抄列表）。
8. **Per-Task Failure Analysis** — 对每个 task，分析如果它失败会产生什么影响。前序 task 的产物是否仍然有效？是否需要回滚？
9. **Rollback Path** — 如果 task N 失败，是否可以安全地从 task N-1 的状态继续？是否有不可逆操作（如数据库 migration、文件删除）未标注？
10. **Verification Blind Spots** — design.md 中有哪些需求没有被任何 task 的验证步骤覆盖？列出未覆盖的需求。
11. **Edge Case Coverage** — plan 是否考虑了边界情况？空数据、无权限、网络不可用、并发修改。
12. **Implicit Dependencies** — 是否有两个 task 修改同一文件但未声明依赖？这可能导致合并冲突或覆盖问题。

## Output Format

plan-reviewer 输出二元结论，**不做数值评分、不计算阈值、不分维度派 subagent**：

```markdown
## Review Summary
- Type: PLAN
- Verdict: Approved | Issues

## Issues
（仅 Verdict = Issues 时出现；列 Critical / Important 条目，每条带 Confidence，按 Confidence Guidance 锚定表定级）
### [Issue Title]
- **Severity**: Critical | Important
- **File/Section**: [位置]
- **Confidence**: [0-100]
- **Description**: [问题描述]
- **Why it matters**: [为什么重要]
- **Suggestion**: [修改建议]

## Advisory Recommendations
（不阻断；仅容纳不影响正确性的优化——可并行提示、措辞调整等。每条简述即可，无需 confidence）
```

- `Verdict: Approved` — Issues 桶为空（无 Critical / Important 阻断项）。Advisory 桶可有可无，不影响 Approved。
- `Verdict: Issues` — Issues 桶至少一条。

### Advisory 准入规则

advisory 桶只放**不影响正确性**的优化。以下四类**必须进 Issues 阻断桶，绝不进 advisory**：

| 命中情形 | 归桶 |
|---|---|
| Forbidden Patterns 命中（TBD/TODO/Similar to Task N/占位符等，见 `${CLAUDE_PLUGIN_ROOT}/skills/task/PLAN_PROMPT.md` 清单） | Issues（阻断） |
| 文件路径错误（路径不存在 / 与 design.md 不一致 / 拼写错误） | Issues（阻断） |
| 依赖倒置（task 引用后序 task 才产出的产物） | Issues（阻断） |
| design 需求无对应 task（覆盖缺口） | Issues（阻断） |

<rule>
The four blocking categories (Forbidden Patterns, wrong file paths, inverted dependencies, design requirements with no task) MUST go into the Issues bucket. Never downgrade any of them into Advisory Recommendations.
Reason: these are correctness defects that break execution — routing them to a non-blocking advisory bucket lets a broken plan pass review silently. Advisory is for optimizations that do not affect correctness only.
</rule>

## Confidence Guidance

Confidence 评分参考。每个区间附锚定示例——偏高的 confidence 会掩盖不确定性：

| Confidence | 适用场景 | 锚定示例 |
|------------|---------|---------|
| 95+ | 可证伪的事实错误：forbidden pattern、文件路径拼写错误、依赖倒置 | "Task 3 引用 Task 4 创建的文件"、"步骤中包含 TBD" |
| 85-94 | 确认的排序或覆盖问题：design 需求在 plan 中无对应 task | "design Goal #2 没有任何 task 覆盖" |
| 75-84 | 潜在问题：粒度偏大、验证步骤偏弱、隐式依赖 | "Task 2 和 Task 4 都修改同一文件但未声明依赖" |
| 60-74 | 改进建议：不影响正确性的优化 | "Task 3 可以和 Task 2 并行执行以提高效率" |
| <60 | 纯推测：基于经验的猜测 | "这个 task 可能需要超过 5 分钟" |

本协议为二元输出，**无独立 Low Confidence 节**：影响正确性的问题一律进 `## Issues`（confidence 如实标注，由调用方据 confidence 决定是否行动），不因 confidence 低而静默丢弃；不影响正确性的低 confidence 改进进 `## Advisory Recommendations`。当你犹豫该给 80 还是 75 时，选 75——宁可低估确定性也不要高估。
