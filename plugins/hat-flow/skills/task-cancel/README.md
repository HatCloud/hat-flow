# task-cancel

任务取消 / 推迟的生命周期关闭 skill：确认意图与原因、决定代码去留、同步 Linear、编写 final.md（取消 / 推迟报告）并归档到 `canceled/` 或 `deferred/`。用户决定放弃或推迟进行中任务时调用。完整流程、停点与取消 vs 推迟的完整差异以 `SKILL.md` 为准。

## 补充信息

- **设计立场**：取消也要付出记录成本——final.md 完整记录原因与经验，否则已投入的精力随归档一起蒸发；「推迟」与「取消」是两种本质不同的处置（deferred 默认保留代码、Linear 回 Backlog、留 Resume Notes 供 task-reopen 恢复），不是同一流程的两个标签。
- **接线**：Linear 同步、commit 规范、Process Review 分别由 linear / git / retrospective 插件 hook 承载（按 task-config.json 条件化）；任务识别与归档靠 `hat-task-detect` / `hat-task-archive`。
