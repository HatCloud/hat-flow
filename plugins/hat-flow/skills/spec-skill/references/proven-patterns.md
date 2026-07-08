# Proven Patterns（spec-skill 参考）

> 从 spec-skill 正文下沉的设计模式参考（经 ISSUE/238 两轮 dogfooding 验证）。Skill 作者按需采用；spec-skill SKILL.md 的 `## Proven Patterns` 指向本文件。

## Verification-Driven Development

TDD 的泛化——不要求测试框架，但要求每个实现步骤都有可验证的预期：

| 模式 | 适用场景 | 验证手段 |
|------|---------|---------|
| **Full TDD** | 有测试框架（Jest, pytest 等） | 测试用例 |
| **Lite TDD** | 无测试框架（markdown、配置文件等） | grep / wc / build 命令 |

两种模式共享 **5 步标准**：RED → RED-VERIFY → GREEN → GREEN-VERIFY → REFACTOR。具体 step 格式模板见 `PLAN_PROMPT.md ## TDD Requirements`。

Skill 中涉及实现步骤时，应在 Plan 阶段指定 VDD 模式（Full/Lite/跳过），并在每个 step 中包含验证循环。

## Mandatory Stop Points

当 skill 包含多个需要用户决策的节点时，使用集中式停止点表格 + `<rule>` 保护模式：

1. 在 skill 顶部定义 **Mandatory Stop Points** 表格，列出所有需要 向用户提问（结构化选项优先） 的节点
2. 每个停止点在流程中用 `<rule>` 包裹，防止 agent 自主跳过

```markdown
| Phase | When | What to Ask |
|-------|------|-------------|
| 2     | 设计完成后 | 确认复杂度和 review 策略 |
| 3→4   | Plan 确认后 | 执行模式 + TDD 策略 |
```

此模式确保所有用户决策点集中可见，避免遗漏。

## Two-Stage Review

代码 review 分两阶段执行，确保实现正确性优先于代码质量：

1. **Stage 1 — Spec Compliance**: 实现是否匹配 plan？
2. **Stage 2 — Code Quality**: 代码是否做好了？

<rule>
Stage 2 开始前 Stage 1 必须先通过；不对错误的实现做 code quality review。
Reason: 在错误的代码上 review 质量既浪费 token，又会产生误导性的反馈。
</rule>

使用 `<!-- STAGE-1-START/END -->` HTML 锚点在 checklist 文件中标记边界，避免硬编码 checklist 内容到多处（ISSUE R2 发现的同步风险）。

## Implementer States

执行 subagent 返回后，按声明状态分流处理：

| Status | 含义 | 处理 |
|--------|------|------|
| **DONE** | 完成 | 进入 review |
| **DONE_WITH_CONCERNS** | 完成但有疑虑 | 正确性问题先解决；观察性记录后继续 |
| **NEEDS_CONTEXT** | 缺少信息 | 提供上下文 + 进度报告，重派（最多 2 次） |
| **BLOCKED** | 无法完成 | 向用户提问（结构化选项优先）：更多上下文 / 更强模型 / 拆分 / 终止 |

在 implementer subagent prompt 末尾要求声明状态：`Report your status as one of: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED.`

## Scope Freeze

设计批准后，范围变更需要显式用户确认。来源：ISSUE 中范围从 8→13 组扩大了 62%。

<rule>
设计批准之后，任何范围扩张都须先经 向用户提问（结构化选项优先） 确认再继续。
Reason: 执行过程中失控的 scope creep 会导致 token 浪费和交付延迟（ISSUE lesson）。
</rule>

如果执行中发现新需求，记入 `next-task-prompt.md` 而非当场处理。

## Dogfooding Execution

Skill 写完/改完后用它跑一次真实任务验证的具体做法（spec-skill SKILL.md `## Dogfooding` 指向本节）：

（可选）写**新** skill 前，可先在没有该 skill 的 pressure scenario 下观察 agent 如何失败，据此针对性写规则——可选实践，非每次必做。

没有真实任务时，检测目标项目是否 git 仓库：
- **是 git** → 用 worktree 创建隔离副本，模拟执行流程，完成后丢弃
- **不是 git** → dry run（走流程但不执行写操作）

让用户选择方式。

检查点：
- 流程是否能顺畅走完？哪一步卡住了？
- 有没有 model 不遵守的约束？（需要加 `<rule>` 或陈述式规则）
- 有没有不必要的停止点拖慢了节奏？
- 有没有缺失的分支或失败处理？

发现的问题应立即修复，而非记录到 debt。

## Confirmation Loop

在任何需要用户审核产物（设计方案、计划、review 结果等）的环节使用统一的确认循环模式：

1. **展示结果**（产物内容或变更差异）
2. **纯文本询问**（非 向用户提问（结构化选项优先））："是否有需要调整的地方？"
3. **用户说"继续"** → 推进到下一步
4. **用户给建议** → 澄清 → 修改 → 重新展示 → 回到步骤 2

关键规则：
- 确认使用纯文本（非 向用户提问（结构化选项优先）），让用户可以自由输入反馈
- 差异展示每轮重置——只展示本轮修改，不累积
- 若涉及自动审查（reviewer subagent），审查轮次计数跨循环累积不重置

适用场景：设计确认、计划确认、review 后确认、Revise cycle 确认等。
