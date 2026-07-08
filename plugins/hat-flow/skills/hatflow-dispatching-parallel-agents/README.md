# hatflow-dispatching-parallel-agents

并行代理调度。当面对 2+ 个无共享状态、无顺序依赖的独立任务时，使用此 skill 同时派发多个 agent 并行工作。

采纳自 obra/superpowers 的 5 个原子技能之一（8f2a054），随 ISSUE 范式转变改写为陈述式中文（9ca3e42）。被 `task-execute` Phase 4 独立批次派发和 `hat-flow` 打包链路引用，正式收编维护，详见 `references/changelog.md`。
