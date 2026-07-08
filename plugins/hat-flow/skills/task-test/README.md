# task-test

Phase 5（Test）worker：运行完整验证、生成验收清单引导用户逐项验收、更新 Linear 状态，然后硬停等待用户显式调用 `/task-end`；验收发现的系统性问题经编排器路由 task-revise。由 `/task` 编排器在 Phase 4 完成后派发。完整流程以 `SKILL.md` 为准。

## 补充信息

- **硬停的设计立场**：验收通过与否只能由用户判定，Phase 5 永不自行推进到归档——「测试通过」与「关闭任务」之间必须隔一次人的显式动作（`/task-end`）；无人值守模式按 UNATTENDED_PROTOCOL 分级降级，而非静默跳过。
- **`.last-verified` 接线**：验证通过后写入任务文件夹的 `.last-verified`（含 commit hash），task-end Step 0 据此跳过重复验证——这是两个 skill 之间唯一的验证状态通道。
