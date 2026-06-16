# Task Execute Skill

## 目的

Phase 4（Execute）阶段 skill。主 session 协调执行 plan.md 中的所有任务，进行轻量验证和代码审查。

## 触发条件

- 通过 `/task` 编排器在 Phase 3 完成后自动调用
- 直接调用 `/task-execute`（手动进入执行阶段）

## 核心流程

1. 逐个执行 plan tasks（按执行模式 auto/inline/parallel-agents 调度，按文件数和关键词分流模型）
2. 每个 task 后：Light verification + `P4.per-task-post` hook（tdd RED 检测 → review per-task 审查 → git formatter → commit checkpoint）
3. 所有 tasks 完成后：`P4.post-execute` hook（全量代码审查 → Revise 触发检测）
4. Phase 4 完成 → 返回编排器，转入 Phase 5（Test）

## 关键规则

- Phase 4 只负责执行和代码审查，不含验证/验收/归档
- TDD RED 步骤意外通过 → 立刻停下报告给用户
- review / commit 由 hook 驱动（per-task 经 `P4.per-task-post`，全量经 `P4.post-execute`），不在主流程内联手写

## 产物

- 代码变更（通过 subagent 执行）
- 更新 `phases.md`（Phase 4 各步骤）
