---
name: hatflow-receiving-code-review
description: "[hat-flow bundled dep — invoked explicitly by the task workflow, not auto-triggered] Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation. 触发词: \"消化 review 反馈\", \"评估审查意见\", \"处理代码审查\", \"别急着改\", \"review 反馈不清楚"
disable-model-invocation: true
---

# Code Review Reception

代码审查需要技术评估，而非情绪表演。

**Announce at start:** "Using hatflow-receiving-code-review to evaluate the feedback."

## Overview

核心原则：先验证再实施，先确认再假设，技术正确性优先于社交舒适感。

## The Response Pattern

收到代码审查反馈时按此顺序处理：

1. READ：读完整条反馈，先不做反应
2. UNDERSTAND：用自己的话复述需求（或追问）
3. VERIFY：对照代码库的真实情况核查
4. EVALUATE：对**这个**代码库而言技术上是否成立
5. RESPOND：给出技术性确认，或给出有理有据的反驳
6. IMPLEMENT：一次只改一项，逐项测试

## Handling Unclear Feedback

<rule>
只要有任何一条反馈项不清楚，在不清楚的项被澄清之前，所有项都不实施。
Reason: 审查项之间往往彼此关联；基于不完整的理解去实施会产出错误结果，而一个做了一半的批次比事先发问更难纠正。
</rule>

**示例：**

```
用户："Fix 1-6"
你理解了 1、2、3、6，对 4、5 不确定。

正确做法："我理解了 1、2、3、6 项，开始实施前需要先澄清第 4、5 项。"
（不要先做 1、2、3、6 再回头问 4、5。）
```

## Source-Specific Handling

### 来自用户

- **受信任**——理解后即可实施
- 范围不清时仍需追问
- 直接进入行动，或给技术性确认

### From External Reviewers

实施前依次核查：

1. 对**这个**代码库而言技术上正确吗？
2. 会破坏现有功能吗？
3. 当前实现这样写有没有它的理由？
4. 在所有目标平台 / 版本上都成立吗？
5. 审查者是否了解完整上下文？

判断建议有误时，用技术理由反驳。无法轻易验证时，明说限制并交还决策权，例如："这点我无法在没有 [X] 的情况下验证，要我去调查 / 追问 / 继续吗？" 与用户先前的决定冲突时，先停下来与用户讨论再动手。

**核心态度：** 对外部反馈保持怀疑，但要仔细核查。

## YAGNI Check for "Professional" Features

审查者建议"做得更完整 / 更专业"时，先 grep 代码库确认实际有没有被调用：

- 没被调用 → "这个 endpoint 没有任何地方调用。按 YAGNI 删掉它？"
- 有被调用 → 那就好好实现

**核心态度：** 你和审查者的建议最终都要对用户的实际需求负责——不需要的功能就不加。

## Implementation Order

多项反馈的实施顺序：

1. 先澄清所有不清楚的项
2. 再按此顺序实施：
   - 阻断性问题（破坏、安全）
   - 简单修复（拼写、import）
   - 复杂修复（重构、逻辑）
3. 逐项单独测试
4. 确认没有引入回归

## When To Push Back

出现以下情况时反驳：

- 建议会破坏现有功能
- 审查者缺少完整上下文
- 违反 YAGNI（功能未被使用）
- 对当前技术栈而言技术上不正确
- 存在 legacy / 兼容性原因
- 与用户的架构决策冲突

**反驳方式：** 用技术理由而非辩解；提具体问题；引用能跑通的测试 / 代码；涉及架构时拉用户一起确认。

## Gracefully Correcting Your Pushback

反驳后发现自己错了，把更正写成事实然后继续，不长篇道歉、不为当初的反驳辩护、不过度解释：

- "You were right - 我查了 [X]，它确实 [Y]。现在实施。"
- "验证过了，你是对的。我最初理解有误，原因是 [reason]。修复中。"

## Patterns（正确默认）

| 场景 | 正确默认 |
|------|---------|
| 收到反馈 | 复述技术需求，或直接动手 |
| 实施前 | 先对照代码库验证 |
| 多项修复 | 一次一项，逐项测试 |
| 评估建议 | 先查会不会破坏现有功能，再判断是否正确 |
| 觉得难以反驳 | 技术正确性优先于舒适感，照常反驳 |
| 有项不清楚 | 先澄清全部项，再开始实施 |
| 无法验证 | 说明限制，交还决策权，不擅自继续 |

## Real Examples

**技术验证（删除 legacy 代码的请求）：**

```
Reviewer: "Remove legacy code"
回应："核查中……build target 是 10.15+，这个 API 需要 13+。向后兼容需要保留 legacy。
       当前实现的 bundle ID 写错了——是修掉它，还是放弃 pre-13 支持？"
```

**YAGNI：**

```
Reviewer: "Implement proper metrics tracking with database, date filters, CSV export"
回应："grep 过代码库——没有任何地方调用这个 endpoint。按 YAGNI 删掉它？还是我漏看了某处调用？"
```

**不清楚的项：**

```
用户："Fix items 1-6"
你理解 1、2、3、6，对 4、5 不确定。
回应："理解了 1、2、3、6。开始实施前需要先澄清第 4、5 项。"
```

## GitHub Thread Replies

回复 GitHub 上的 inline review 评论时，回到该评论所在的 thread 里回复（`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`），不要发成顶层 PR 评论。

## Dependencies

- 引用: task/plugins/review.md（review 插件消费本技能作反馈处理纪律）
- 引用: task/references/review-workflow.md
- 无预注入依赖
- 无 skill 调用依赖

## The Bottom Line

外部反馈是**待评估的建议**，不是待执行的命令。先验证、再质疑、然后实施；保持技术严谨，不做表演式认同。
