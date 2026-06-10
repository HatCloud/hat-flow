# Task Plan Skill

## 目的

Phase 3（Plan + Commit）阶段 skill。按模板编写实施计划 plan.md、运行 reviewer review、提交任务文档、同步 Linear。

## 触发条件

- 通过 `/task` 编排器在 Phase 2 完成后自动调用
- 直接调用 `/task-plan`（手动进入规划阶段）

## 核心流程

1. 按内置模板编写 plan.md（bite-sized tasks + TDD steps + exact file paths）
2. Self-review checklist（无占位符、每需求对应 task、路径精确）
3. Reviewer subagent review（Low 0 轮，Medium 1+条件第2轮，High 2轮）
4. 展示计划，确认执行模式 + TDD 策略
5. 提交任务文档（`git commit`）
6. 同步 Linear（更新描述、发布评论、上传文档）

## 关键规则

- plan.md 中绝不出现占位符（TBD、"similar to Task N"等）
- Linear sync 由 P3.phase-end hook 中 linear plugin 执行（条件化）

## 产物

- `.tasks/open/YYYY-MM-DD-topic/plan.md`
- 更新 `phases.md`（Phase 3 各步骤）
