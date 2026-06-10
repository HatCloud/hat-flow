# Task Design Skill

## 目的

Phase 2（Design）阶段 skill。探索代码上下文、提出方案、逐节展示设计、编写 design.md、运行 review 轮次。

## 触发条件

- 通过 `/task` 编排器在 Phase 1 完成后自动调用
- 直接调用 `/task-design`（手动进入设计阶段）

## 核心流程

1. 探索项目上下文（优先 Explore subagent）
2. 提出澄清问题（每次一个，优先选择题）
3. 展示 2-3 个方案，等待用户选择
4. 逐节展示设计，每节确认
5. 编写 design.md
6. 自我 review（占位符扫描、一致性、范围、歧义）
7. 确认 review 策略（轮数、code review 级别、模型）
8. 独立 reviewer subagent review（Medium 1 轮，High 2 轮）
9. 等待用户明确批准

## 关键规则

- 每次只问一个问题
- 明确批准 = 用户回复 "好"/"可以"/"LGTM"，不接受沉默或"收到"
- Medium/High 复杂度必须自动触发 reviewer subagent，不等用户提醒

## 产物

- `.tasks/open/YYYY-MM-DD-topic/design.md`
- 更新 `phases.md`（Phase 2 各步骤）
