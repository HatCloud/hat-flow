---
name: hatflow-verification-before-completion
user-invocable: false
description: "[hat-flow bundled dep — invoked explicitly by the task workflow, not auto-triggered] Use when about to claim work is complete, fixed, or passing, before committing or creating PRs. Do NOT use for driving the app itself to observe behavior end-to-end (use `verify`) — this skill governs the claim/evidence discipline, not the verification execution. 触发词: \"验证后再声称完成\", \"完成前验证\", \"先跑测试再说\", \"证据优先\", \"声称完成之前"
disable-model-invocation: true
---

# Verification Before Completion

完成声明须以新鲜的验证证据为前提：先运行验证命令、确认输出，再声称工作完成 / 修复 / 通过。未验证就声称完成等于不诚实，而非高效。

**Announce at start:** "Using hatflow-verification-before-completion to check the evidence before claiming success."

核心原则：先有证据，后下结论（Evidence before claims, always）。

<rule>
完成声明须以当前这条消息内产生的验证证据为依据；没有新鲜运行过验证命令，该声明就不成立。
Reason: 上一次运行、读代码推断或「应该能过」都不算证据——代码可能已经变更，或假设本身就是错的。遵字面而跳过实际运行，违背本规则的本意。
</rule>

## The Gate Function

声称任何状态、或表达对成果的满意之前，逐步走完这道门：

1. **IDENTIFY** — 哪条命令能证明这个声明？
2. **RUN** — 完整执行该命令（fresh、complete，不复用旧输出）
3. **READ** — 读全部输出，检查 exit code，数失败项
4. **VERIFY** — 输出是否支持该声明？
   - 不支持 → 陈述真实状态并附证据
   - 支持 → 陈述声明并附证据
5. **CLAIM** — 此时才做出声明

跳过任一步即为臆断而非验证；门未走完，声明无依据。

## Claim Requirements

各类声明所需的证据，以及不足以采信的依据：

| 声明 | 所需证据 | 不足以采信 |
|------|----------|-----------|
| 测试通过 | 测试命令输出：0 失败 | 上一次运行、"应该能过" |
| Linter 干净 | linter 输出：0 错误 | 局部检查、外推 |
| 构建成功 | 构建命令：exit 0 | linter 通过、日志看着正常 |
| Bug 已修 | 复测原始症状：通过 | 改了代码、假定已修 |
| 回归测试有效 | 完成 red-green 循环 | 测试跑过一次 |
| Agent 已完成 | VCS diff 显示改动 | agent 自报 "success" |
| 需求已满足 | 逐条对照 checklist | 测试通过 |

## Key Patterns（正确默认）

直接陈述每类声明的成立条件：

- **测试** — 跑测试命令 → 看到 34/34 pass → 声称 "测试全部通过"。仅凭 "应该过了" / "看起来对" 不成立。
- **回归测试（TDD Red-Green）** — Write → Run（pass）→ 还原 fix → Run（必须 FAIL）→ 恢复 → Run（pass）。仅 "我写了回归测试" 而未走 red-green 不成立。
- **构建** — 跑构建 → 看到 exit 0 → 声称 "构建通过"。linter 通过不等于构建通过（linter 不检查编译）。
- **需求** — 重读 plan → 建 checklist → 逐条核对 → 报告缺口或完成。"测试通过即阶段完成" 不成立。
- **Agent 委派** — agent 自报成功后，独立核查 VCS diff、确认改动，再报告真实状态。agent 的自报不可直接采信。

## Rationalization Guard

以下托词均不构成验证；每条对应一个事实，照事实办：

| 托词 | 事实 |
|------|------|
| "现在应该能跑了" | 跑验证命令 |
| "我很有把握" | 把握 ≠ 证据 |
| "就这一次" | 无例外 |
| "linter 过了" | linter ≠ 编译器 |
| "agent 说成功了" | 独立核查 |
| "我累了" | 疲惫 ≠ 例外 |
| "局部检查够了" | 局部证明不了整体 |
| "换了说法所以规则不适用" | 规则的精神先于字面 |

构成风险的高发信号：用 "should" / "probably" / "seems to" 等措辞；验证前先表达满意（"Great!" / "Perfect!" / "Done!"）；未验证就准备 commit / push / PR；任何在未运行验证的情况下暗示成功的表述。出现这些信号即回到 Gate Function 第 1 步。

## When To Apply

适用于一切暗示成果状态的表述，无论字面措辞：

- 任何形式的成功 / 完成声明，或对成果的满意表达
- 任何对工作状态的正面陈述
- commit、PR 创建、任务完成、进入下一任务
- 委派给 agent 前

规则覆盖：精确措辞、同义改写、对成功的暗示，以及任何暗示完成 / 正确的沟通。换措辞不豁免——精神先于字面。

## Why This Matters

未验证即声称完成的代价是真实的：信任破裂（"I don't believe you"）、未定义的函数上线即崩溃、缺失需求带着不完整功能上线、在错误的完成判断上反复返工。诚实是核心价值。

## Dependencies

- 引用: spec-skill（约束与语言范式）
- 无预注入依赖
- 无 skill 调用依赖

## The Bottom Line

跑命令 → 读输出 → 再声称结果。验证无捷径。
