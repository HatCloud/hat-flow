# task-execute

Phase 4（Execute）worker：主 session 协调逐个执行 plan.md 中的任务，每个 task 后轻量验证，全部完成后全量代码审查，review 发现系统性问题时经编排器触发 revise 子循环。由 `/task` 编排器在 Phase 3 完成后派发，也可单独调用。完整调度规则与执行循环以 `SKILL.md` 为准。

## 补充信息

- **hook 驱动的设计**：per-task 的 review / formatter / commit checkpoint 与收尾全量审查都由 `P4.per-task-post` / `P4.post-execute` hook 注入（`bin/hat-plugin-hook`），不在主流程内联手写——按 task-config.json 开关插件即可整段启停，这是插件化重构在 Phase 4 的核心收益点。
- **派发接线**：auto / parallel-agents 模式对可隔离批次派 `task-executor` native subagent，注入 `IMPLEMENTER_PROMPT.md`（同一份 prompt 被 headless-provider 后端复用）；codex 与 headless-provider 是 engine 维度的另两个执行后端。
- **codex 并发教训**（实测）：codex 后端在同一工作树写并发会 dirty-state 串扰，故同树串行；可隔离 layer 靠 per-task git worktree 隔离才能并行——实测各落各 worktree、互不污染。
