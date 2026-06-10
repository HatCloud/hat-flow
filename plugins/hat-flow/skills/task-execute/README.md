# Task Execute Skill

## 目的

Phase 4（Execute）阶段 skill。主 session 协调执行 plan.md 中的所有任务，进行轻量验证和代码审查。

## 触发条件

- 通过 `/task` 编排器在 Phase 3 完成后自动调用
- 直接调用 `/task-execute`（手动进入执行阶段）

## 核心流程

1. 逐个执行 plan tasks（Sonnet/Opus subagent，按文件数和关键词选择）
2. 每个 task 后：Light verification + Code Review Light（Medium/High 必做）
3. 所有 tasks 完成后：自适应全量 Code Review
4. Phase 4 完成 → 转入 Phase 5（Test）

## 关键规则

- Phase 4 只负责执行和代码审查，不含验证/验收/归档
- TDD RED 步骤意外通过 → 立刻停下报告给用户
- Commit Guidelines 内联在 skill 中，传递给每个执行 subagent

## 产物

- 代码变更（通过 subagent 执行）
- 更新 `phases.md`（Phase 4 各步骤）
