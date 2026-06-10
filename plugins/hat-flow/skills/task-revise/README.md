# task-revise

任务修订循环。在 Phase 4（Execute）或 Phase 5（Test）中发现系统性问题时，运行 mini design→plan→execute 子流程来解决。

## 触发方式

由 task-execute（4b）或 task-test（5d）触发，通过 task 编排器路由。不单独使用。

## 流程

1. 识别系统性问题（非单点 bug）
2. Mini 设计：分析问题根因和影响范围
3. Mini 计划：制定修复方案
4. Mini 执行：实施修复并验证
