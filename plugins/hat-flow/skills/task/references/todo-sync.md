# TODO Sync (TaskCreate / TaskUpdate) — Canonical

task 套件双层 TODO 同步契约的单一来源。orchestrator 与各 phase skill 引用本文件，不再各存副本。

phases.md 是跨 session 的持久化状态源，但用户在当前 session 中无法实时看到进度。**必须使用 Claude Code 内置的 TaskCreate / TaskUpdate 工具同步进度到 UI**。

## 双层结构

TODO 列表由两层组成：

1. **概览行 (overview)**：始终存在的一条 task，subject 格式为 `[任务名] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End`。status 始终为 `in_progress`（显示 spinner）。Phase 切换时更新 subject 中的符号：
   - `✔` = 已完成
   - `▶` = 当前进行中
   - `◻` = 未开始
   - Phase 标题用**一个英文单词**概括（Init / Design / Plan / Execute / Test / End）
   - metadata: `{"level": "overview", "task": "<task-folder-name>"}`

2. **当前阶段子步骤 (step)**：当前 phase 的每个步骤一条 task，subject 前缀 `→`。Phase 切换时：**删除旧阶段所有 step 级 task，创建新阶段的 step 级 task**。metadata: `{"level": "step", "phaseNum": N, "stepId": "Na"}`

## 显示效果

```
◼ [M0] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End
◻ → 3a. 生成 plan
◻ → 3b. Plan 忠实度评估
◻ → 3c. 提交任务文档
◻ → 3d. Linear 同步
```

## 生命周期规则

1. **任务启动时 (Phase 1 开始)**：**先**创建概览行 `[任务名] ▶P1:Init ◻P2:Design ◻P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End` 并**立即** `TaskUpdate(status: "in_progress")`，**再**创建 Phase 1 的 step 级 task（概览行必须拿到最小 ID 以固定在首行）。
2. **Phase 切换时**：
   - 删除当前阶段所有 `level: "step"` 的 task (TaskUpdate status: deleted)
   - 更新概览行 subject（把完成的 phase 改 `✔`，新 phase 改 `▶`）
   - 创建新阶段的 step 级 task
3. **步骤开始时**：`TaskUpdate(status: "in_progress")`
4. **步骤完成时**：`TaskUpdate(status: "completed")` + 同步更新 phases.md
5. **跨 session 恢复时（Bootstrap）**：TaskCreate 列表丢失（session 级）。恢复时先 `TaskList` 检查是否已有 `level: "overview"` 的 task；若有则 `TaskUpdate` 更新 subject，若无则**先**从 phases.md 重建概览行（确保拿到最小 ID）并**立即** `TaskUpdate(status: "in_progress")`。**然后**再重建当前阶段 step 级 task，已完成步骤标记 completed。
6. **任务结束时 (`/task-end`)**：概览行标记 completed，所有 step 级 task 删除。

<rule>
Every phase skill execution MUST maintain the two-layer TODO structure: one overview line + current phase steps. phases.md and TaskCreate/TaskUpdate must stay in sync at all times.
Reason: phases.md is invisible to the user during the session. The two-layer TODO is the only way the user sees both overall progress and current-step granularity.
</rule>
