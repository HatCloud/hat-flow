# task-reopen

## 目的

将已完成、取消或推迟的任务重新移回进行中，供用户继续开发或修改。

## 触发条件

用户想重新激活某个已归档任务时使用。常见触发词：重新激活、reopen、重开任务、恢复任务。

## 核心流程

1. **选择任务** — 从 `.tasks/done/`、`.tasks/canceled/`、`.tasks/deferred/` 中选择要重开的任务
2. **选择阶段** — 用户决定从哪个 Phase 重新开始（Phase 2-6）
3. **移回 open** — `git mv` 到 `.tasks/open/`
4. **重置 phases.md** — 目标 Phase 及之后的步骤重置为未完成
5. **清除 unattended.json** — 重开后需用户重新决定是否启用无人值守
6. **更新 Linear** — 将 issue 状态改回 In Progress（`state` 取 `linear.json.statusMap["In Progress"]`，经 `get_status_map` 解析，无硬编码 UUID）
7. **提交 + 通知** — 独立 commit，提示用户调用 `/task` 继续

## 关键规则

- task-reopen 是人工操作，不支持全自动执行
- 重开后通过 `/task` 决定是否启用无人值守
- Linear 更新失败不中止流程

## 依赖

- 引用：`plugins/linear.md`（Linear 状态更新规范，通过 task-config.json 条件化）
- 读取: `{task-folder}/task-config.json`、`{task-folder}/linear.json`（若存在）
- 写入: `{task-folder}/phases.md`（重置步骤状态）
