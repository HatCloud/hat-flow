# task-reopen

将已完成 / 取消 / 推迟的任务从归档目录移回 `.tasks/open/` 重新激活：用户选起始 Phase，重置 phases.md 对应步骤，恢复 Linear 状态，最后提示经 `/task` 继续。人工操作，不支持全自动执行。完整流程以 `SKILL.md` 为准。

## 补充信息

- **无硬编码 UUID**（分发决策）：Linear 状态恢复取 `linear.json.statusMap`（经 `get_status_map` 解析）而非写死状态 UUID——hat-flow 公开分发后每个 workspace 的状态 ID 都不同，写死的值无法跨 workspace 使用。
- **unattended.json 一律清除**：重开是人的决策，归档前的无头授权不自动延续——是否继续无人值守由用户在 `/task` 恢复时重新决定。
- **容错立场**：Linear 更新失败不中止流程——归档移动与状态重置是主体，外部同步失败降级为提示。
