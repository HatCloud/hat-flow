# Task Test Skill

## 目的

Phase 5（Test）阶段 skill。运行完整验证、更新 Linear 状态，展示验收清单等待用户手动测试。

## 触发条件

- 通过 `/task` 编排器在 Phase 4 完成后自动调用
- 直接调用 `/task-test`（手动进入测试阶段）

## 核心流程

1. Full verification（5a/5b）
2. 生成并展示验收清单（5c）
3. Linear 状态更新为 "In Review"（P5.post-acceptance hook）
4. **硬停，等待用户调用 /task-end**（测试反馈走 5d）

## 关键规则

- 永远不要自动调用 /task-end 或开始归档流程
- 测试反馈阶段（5d）：分析 → 修复 → 用户确认 → 再 commit
- 架构级问题必须 triage，不能直接原地修

## 产物

- `{task-folder}/.last-verified`
- 更新 `phases.md`（Phase 5 各步骤）
