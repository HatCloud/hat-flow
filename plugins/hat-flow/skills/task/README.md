# Task Skill

## 目的

Task skill 是任务生命周期的编排器。读取任务文件夹中的 `phases.md` 确定当前阶段，加载对应的阶段 skill 执行，支持跨 session 恢复。

本 skill 不直接执行任何阶段逻辑——它只负责路由。

## 触发条件

- 用户提出新任务
- 继续正在进行中的任务
- 新 session 恢复中断的任务

## 阶段体系

| 阶段 | Skill | 触发 |
|------|-------|------|
| Phase 1: Setup | `/task-init` | 新任务或恢复 Phase 1 |
| Phase 2: Design | `/task-design` | Phase 1 完成后 |
| Phase 3: Plan | `/task-plan` | Phase 2 完成后 |
| Phase 4: Execute | `/task-execute` | Phase 3 完成后 |
| Phase 5: Test | `/task-test` | Phase 4 完成后 |
| Phase 6: End | `/task-end` | Phase 5 完成，用户手动调用 |
| Cancel | `/task-cancel` | 用户放弃任务，手动调用 |

## 跨 Session 恢复

`phases.md` 是保存在任务文件夹中的状态文件（由 task-init 创建）。包含所有阶段的颗粒度 todo 列表：

```markdown
## Phase 1: Init
- [x] 1a. 检查现有任务
- [x] 1f. 创建任务文件夹 + prompt.md
**Status**: DONE

## Phase 2: Design
- [x] 探索项目上下文
- [ ] 澄清问题   ← 从这里恢复
**Status**: IN_PROGRESS
```

新 session 调用 `/task` 时：读取 `phases.md` → 找到第一个未 DONE 的 Phase → 加载对应 skill 继续。

## 路由逻辑

编排器通过 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task-{phase}/SKILL.md` 加载阶段指令并执行。这是 `/task` 的全部工作。

## 子协议文件

| 文件 | 用途 | 引用方式 |
|------|------|---------|
| `DESIGN_PROTOCOL.md` | 设计阶段工作流（参考） | task-design 加载 |
| `PLAN_PROMPT.md` | Plan 模板（参考） | task-plan 加载 |
| `UNATTENDED_PROTOCOL.md` | 无人值守协议 | 条件加载 |
| `plugins/` | 7 个插件 manifest + 指令文件 | hat-plugin-hook 运行时解析 |
