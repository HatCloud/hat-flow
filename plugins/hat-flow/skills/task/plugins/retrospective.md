---
{
  "name": "retrospective",
  "description": "归档后流程审查（Part B 交互讨论）",
  "recommend_disable_when": [
    "hotfix 类紧急修复",
    "预计 30 分钟内完成的小任务"
  ],
  "recommend_enable_when": [
    "涉及流程改进或架构决策的任务"
  ],
  "hooks": {
    "P6.post-archive": {
      "priority": 70,
      "section": "## P6.post-archive",
      "on_error": "graceful"
    }
  }
}
---

# Retrospective Plugin

## P6.post-archive

### 流程审查

归档完成后执行流程回顾：

### 阶段 1: Process Review Part B（交互讨论）

基于 final.md 中 Process Review Part A 的分析，与用户讨论改进建议。

**汇总所有建议**为两类：

1. **Workflow / Skill improvements** — 流程偏差、token 优化
   - 例：设计阶段问题过多 → 调整提问策略
   - 例：低复杂度的 plan review 不必要 → 调整复杂度阈值
   - 例（取消）：过晚发现不可行 → 增加可行性预检
2. **Project configuration improvements** — 缺失或可优化的配置
   - 例：未配置验证命令 → 建议添加到 CLAUDE.md
   - 例：formatter 不由 git hook 管理 → 建议配置 husky

**如果有建议**，使用 AskUserQuestion，每条建议附带：
- 问题描述（一句话）
- 具体的改进方案
- 选项：**Execute now** / **Record to debt.md for later** / **Skip**

对于用户选择 "Execute now" 的建议：
- Workflow/Skill improvements → 直接修改对应的 skill 文件
- Project configuration improvements → 修改 CLAUDE.md 或相关配置文件

**如果没有建议**：跳过此步骤。

**[Unattended]** 自动选择 "Record to debt.md for later"，不阻断。

### 阶段 1.5: Severity-Case 喂养（code review 经验回流）

若本任务 code review 中出现 **severity 误判** 或 **新型 pattern**（如某类问题本应 Critical 却初判 Important），评估是否把它沉淀为 case 到 `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/severity-escalation.yaml`。

checklist（全部满足才加 case）：
- 该 pattern 有跨任务复用价值（非本任务特有）
- 可泛化表述——脱离具体文件名 / 行号 / 项目专有名词
- 与现有 `rules` 不重复

case 格式同 severity-escalation.yaml 的 `rules` 项（id / pattern / example / effect），example 必须泛化。

<rule>
In unattended mode, never auto-edit severity-escalation.yaml. Only propose the case and write it into final.md (committed with the archive); a human applies it later under review.
Reason: severity-escalation.yaml drives review gating — an unreviewed auto-appended rule could mis-escalate or mis-downgrade every future review. The rule file changes only under human review.
</rule>

**[Interactive]** AskUserQuestion：加入 severity-escalation.yaml / 仅记录到 final.md / 跳过。
**[Unattended]** 仅写入 final.md 的 severity-case 提案节（随归档 commit），不改 severity-escalation.yaml。
