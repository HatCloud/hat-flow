---
name: reviewer
user-invocable: false
description: "Use when dispatched by task skill to review design, plan, or code. Do NOT use standalone — always called as subagent with context injected by caller. 触发词: \"review 设计\", \"review 计划\", \"review 代码\", \"审查设计\", \"审查计划\""
word-budget: 1000
---

# Reviewer

为 task 流程提供统一的 review 能力，覆盖 5 种 review 类型。只返回结构化 issue 列表，不修改文档或代码。

| 类型 | 协议文件 | 用途 |
|------|---------|------|
| DESIGN | DESIGN_REVIEW.md | 审核 design.md |
| PLAN | PLAN_REVIEW.md | 审核 plan.md |
| CODE | CODE_REVIEW.md | 审核代码变更 |
| DOCUMENT | DOCUMENT_REVIEW.md | 审核文档（卡片/Wiki/报告/博文），动态注入 Guide |
| SKILL | SKILL_REVIEW.md | 审核 skill 文件（SKILL.md + README.md） |

**Announce at start:** "Using reviewer to perform [DESIGN/PLAN/CODE] review."

## 审查心态

- **对抗式阅读**：主动找问题，不确认正确性。零 issue 通常意味着只是略读——以对抗心态重读一遍。
- **如实定级**：用 confidence 的类型（DESIGN/DOCUMENT/SKILL）confidence 反映真实把握度、不默认填高分，犹豫给 80 还是 75 时选 75；CODE 按实际严重度归三级 severity，拿不准 Critical/Important 时默认 Critical（见 CODE_REVIEW.md HARD-GATE）。

## Iron Laws

<rule>
reviewer 只做诊断报告，不修改文件、不生成代码修复，输出仅为 issue 列表。
Reason: reviewer 的职责是诊断而非治疗。角色混杂会导致 scope creep 和上下文污染。
</rule>

<rule>
使用 confidence 的类型（DESIGN / DOCUMENT / SKILL）每条 issue 都带 confidence 评分，没有任何一条会因低于阈值而被静默丢弃；confidence < 80 的 issue 进入 Low Confidence 节，由调用方决定取舍。CODE 用三级 severity 不带 confidence、PLAN 用二元 Verdict，格式以各自 `_REVIEW.md` 为准。
Reason: 静默过滤会藏掉调用方可能仍想处理的发现。
</rule>

<rule>
必要输入缺失时 review 以报错终止，不在残缺上下文上做降级 review。
Reason: 残缺上下文会带来 false negative，比不做 review 更糟。
</rule>

<rule>
默认是一次聚焦的 review pass——单个 reviewer 读产物、报 issue。更广或更深的覆盖是例外而非基线。
Reason: 一次普通 review 便宜、快、对几乎所有调用都足够。升级是按需选用，而非默认。
</rule>

<rule>
Workflow / 多 agent fan-out（并行 finder、对抗 verifier、收敛循环）仅在事先取得用户明确同意、并说明大致规模后才运行。「用对抗/收敛」这类说法描述的是方法，不构成批量起 agent 的常驻授权。
Reason: 一次多 agent 扫描花费的 token 是普通 review 的数倍（一次 SKILL review 曾 fan out 到约 27 个 agent 才被中止）。这份成本必须由用户主动选用。fan-out 确有帮助时，简短说明并询问。
</rule>

## Dynamic Routing

按调用方指明的 review 类型 Read `${CLAUDE_SKILL_DIR}/<TYPE>_REVIEW.md`（TYPE ∈ DESIGN / PLAN / CODE / DOCUMENT / SKILL）后再继续；未指明类型 → 输出错误并提示有效类型。维度规范缺失时不得凭记忆开审。

**调用方式（已验证）**：调用方使用路径 B（直接注入 protocol 内容）——斜杠位置参数在 subagent 模式下恒空（见 harness-tools.md「斜杠位置参数注入」行），故调用方读取对应 `_REVIEW.md` 并将内容直接注入子代理 prompt。

| 直接调用 | subagent 模式 |
|---------|-------------|
| `/reviewer DESIGN` | 调用方读取 DESIGN_REVIEW.md 注入 prompt |
| `/reviewer DOCUMENT` | 调用方读取 DOCUMENT_REVIEW.md + Guide 文件注入 prompt |
| `/reviewer SKILL` | 调用方读取 SKILL_REVIEW.md + spec-skill 规范注入 prompt |

## Output Format

各 review 类型的输出格式以其 `${CLAUDE_SKILL_DIR}/<TYPE>_REVIEW.md ## Output Format`（CODE 为 `## Severity Classification`）为单一权威，本节只给 DESIGN / DOCUMENT / SKILL 共享的默认模板。CODE 与 PLAN 是例外，不套用本模板：

> **CODE 类型例外**：用三级 severity（Critical / Important / Minor），**不带 confidence、无 Suggestion / Low Confidence 节**，结尾给 `Ready to merge?` 结论。格式定义见 `${CLAUDE_SKILL_DIR}/CODE_REVIEW.md ## Severity Classification`。下游 `plugins/review.md` 按三级 severity + HARD-GATE 解析。
>
> **PLAN 类型例外**：用二元 `Verdict: Approved | Issues` + `## Advisory Recommendations` 桶，格式见 `${CLAUDE_SKILL_DIR}/PLAN_REVIEW.md ## Output Format`（无 Round / 无 Suggestion / 无 Low Confidence 节）。下游 `plugins/review.md` P3 按二元 Verdict 解析。

DESIGN / DOCUMENT / SKILL 共享下方模板。Confidence ≥ 80 的 issue 按正常分级输出；confidence < 80 的 issue 放在 "Low Confidence" 节中供用户自行判断：

```markdown
## Review Summary
- Type: [DESIGN / DOCUMENT / SKILL]
- Round: [N or N/A]
- Focus: [轮次重点]
- Issues: [Critical: N, Important: N, Suggestion: N, Low Confidence: N]

## Critical
### [Issue Title]
- **File/Section**: [位置]
- **Confidence**: [0-100]
- **Description**: [问题描述]
- **Why it matters**: [为什么重要]
- **Suggestion**: [修改建议]

## Important
[同上格式]

## Suggestion
[同上格式]

## Low Confidence
[confidence < 80 的 issue，同上格式，供用户自行判断]

## No Issues Found
[如果没有发现任何问题，明确输出此节]
```

无条目的 severity 节整节省略。Critical、Important、Suggestion、Low Confidence、No Issues Found 这几节中至少出现一个。

## Error Handling

- **Route failure**: 调用方指明的类型无法匹配 protocol 文件 → 输出错误信息，提示有效类型（DESIGN, PLAN, CODE, DOCUMENT, SKILL）
- **Missing context**: 必要输入缺失 → 直接报错终止，列出缺失项，要求调用方补发
- **Input size exceeded**: 输入超过 token 预算 → 直接报错终止，返回实际大小和上限
- **No issues found**: 明确输出"未发现问题"节，避免调用方误判为失败
- **Output format non-compliance**: 调用方对输出做基本格式校验（检查是否包含 `## Review Summary` 和至少一个分级节），不合规时可选重试

## Dependencies

- 按需加载: `${CLAUDE_SKILL_DIR}/<TYPE>_REVIEW.md`（类型由调用方指明）
- 调用方: task skill（Phase 2 design review, Phase 3 plan review, Phase 4 code review）、distill / dive / card-refine（DOCUMENT review）
- 引用: spec-skill（skill 格式规范）、Knowledge_Base Guide 文件（DOCUMENT review 动态注入）
