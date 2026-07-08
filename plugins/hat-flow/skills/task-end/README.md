# task-end

任务完成后的生命周期关闭 skill：机械验证、技术债务对账、编写 final.md、Linear 同步、changelog / CLAUDE.md 更新、归档提交与分支处理。用户确认任务完成且测试通过后显式调用，是 Interactive 路径下 Phase 5 硬停后的唯一推进入口。完整步骤与全部强制停点以 `SKILL.md` 为准。

## 补充信息

- **Step 3.6 retrospective 独立 HARD-GATE**（设计决策）：流程回顾在 retrospective 插件启用时作为独立强门控步骤执行（归档后、最终确认前），与 `P6.post-archive` hook 的 git 段相互独立、不依赖 hook 逐段输出——避免 hook 段被跳过时回顾静默丢失。
- **关闭提交只含文档的原因**：final.md 是归档后唯一留存任务全貌的记录，关闭提交保持纯文档能让归档 commit 可独立回溯；发现的意外代码变更必须先单独处理。
- **脚本接线**：`hat-task-detect`（任务识别）、`hat-task-archive`（归档 + 提交）、`hat-plugin-hook`（P6 hook）、`hat-conversation-export`（会话导出，供 dogfooding 复盘定位）。
