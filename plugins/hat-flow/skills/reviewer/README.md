# Reviewer Skill

## 目的

为 task 流程提供统一的 review 能力。覆盖 5 种 review 类型。作为 subagent 被调用方派发，接收注入的上下文，返回结构化的 issue 列表。不负责修改文档或代码。

## 触发方式

由 task skill 在以下节点派发 subagent 调用：
- `/reviewer DESIGN` — design.md 完成后的独立 review
- `/reviewer PLAN` — plan.md 完成后的独立 review
- `/reviewer CODE` — 代码变更后的 review（Light 或 Full 模式）
- `/reviewer DOCUMENT` — 文档审核（卡片/Wiki/报告/博文），动态注入 Guide
- `/reviewer SKILL` — skill 文件审核（SKILL.md + README.md），注入 spec-skill 规范

subagent 模式下使用路径 B（直接注入协议内容到 prompt），不依赖动态路由。

## 5 种 Review 类型

### Design Review

输入：design.md 全文、prompt.md、轮次编号。

- **Round 1 — 结构完整性**：需求覆盖、节间间隙、验收测试对齐、Goals/Non-Goals 边界
- **Round 2 — 对抗审查**：故障场景、边界情况、未声明假设、回滚路径、过度设计

### Plan Review

输入：plan.md 全文、design.md 全文、轮次编号。

- **Round 1 — 结构完整性**：任务排序、依赖完整性、文件路径准确、范围一致性、forbidden patterns 扫描
- **Round 2 — 对抗审查**：逐 task 失败分析、回滚路径、验证盲区、隐式依赖

### Document Review

输入：待审文档全文、对应 Guide 文件全文、文档类型。

三个检查维度：
- **Fact Check**（分级策略）：硬事实=Critical / 软事实=Important / 观点=Suggestion
- **Format Compliance**（Guide 驱动）：从 Guide 的"审核检查项"段落提取检查条件
- **Content Quality**（通用基础）：独立性、深度、可读性

Guide 映射：Cards→CARDS_GUIDE / Wiki→WIKI_GUIDE / Report→REPORT_GUIDE / Blog→BLOG_POST_GUIDE

### Skill Review

输入：SKILL.md 全文、README.md 全文、spec-skill 规范。

四个检查维度：
- **结构合规**：必要段落完整性
- **流程完整性**：Gate/Iron Laws/Error Handling 覆盖
- **兼容性**：CC 特有语法黑名单检查
- **内容质量**：指令清晰度、占位符扫描

### Code Review

两种模式：

- **Light 模式**（单 agent，每 task 完成后）：代码质量、plan 对齐、明显 bug
- **Full 模式**（并行 4 维度，所有 task 完成后）：
  - Plan Alignment — 实现与计划的一致性
  - Code Quality — DRY、错误处理、类型安全、边界情况
  - Architecture — 设计模式、关注点分离、性能、安全性
  - Testing — 测试覆盖、断言质量、edge case

Full 模式由 task skill 并行派发 4 个 reviewer subagent，每个负责一个维度。

## 复杂度与默认策略

| 复杂度 | Design/Plan Review | Code Review Light | Code Review Full |
|--------|-------------------|-------------------|------------------|
| Low    | 0 轮              | 可选              | 不做             |
| Medium | 1 轮（Round 1）   | 每 task 后        | 可选             |
| High   | 2 轮（Round 1+2） | 每 task 后        | 全部完成后       |

## 输出格式

统一使用三级分类：Critical / Important / Suggestion。每个 issue 附 confidence 评分（0-100）。Confidence ≥ 80 正常分级输出，< 80 放入 Low Confidence 节供用户判断。

## 关键规则

- 只报告不修改——reviewer 的角色是诊断，不是治疗
- 缺失输入直接报错终止——不做降级 review
- 输入超限直接报错——不做部分 review

## 文件结构

```
${CLAUDE_PLUGIN_ROOT}/skills/reviewer/
├── SKILL.md              # 主框架：路由、通用规则、输出格式
├── README.md             # 本文件
├── DESIGN_REVIEW.md      # Design review protocol
├── PLAN_REVIEW.md        # Plan review protocol
├── CODE_REVIEW.md        # Code review protocol
├── DOCUMENT_REVIEW.md    # Document review protocol（动态 Guide 注入）
└── SKILL_REVIEW.md       # Skill review protocol（基于 spec-skill）
```

## 依赖

- **调用方**：task skill（design/plan/code review）、distill/dive/card-refine（document review）
- **引用**：spec-skill（skill 格式规范）、Knowledge_Base Guide 文件（document review）
