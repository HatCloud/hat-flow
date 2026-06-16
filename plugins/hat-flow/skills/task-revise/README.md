# task-revise

任务修订循环。在 Phase 4（Execute）或 Phase 5（Test）中发现系统性问题时，运行一个**自适应单循环**来解决。

## 触发方式

由 task-execute（4b）或 task-test（5d）触发，通过 task 编排器路由。不单独使用。

## 流程

单循环步骤序列（design/plan 两步按需产生，不再有 Full/Partial/Lite 深度档位）：

```
Initialization → RN-rootcause → [按需] RN-design → [按需] RN-plan → RN-execute → RN-verify
```

1. **Initialization** — 读取 phases.md 中 IN_PROGRESS 的 Revise section 及 design/plan 上下文
2. **RN-rootcause** — 接 hatflow-systematic-debugging 定位根因，据此判定本次需触及哪些步骤，按需把 RN-design / RN-plan 插入 section
3. **RN-design / RN-plan（按需）** — 仅当根因需要时产生；各带确认循环
4. **RN-execute** — 执行修复；遇根本性问题走 Root-Problem Handling（DEFERRED + WIP commit，不 reset 代码）
5. **RN-verify** — 标记 revise 执行完毕（Status = DONE），返回编排器；实际回归验证由原 phase skill 重跑

## 关键规则

- 是否动 design/plan 由根因分析决定，不预设深度档位
- Revise cycle 不嵌套
- 根本性问题升级为 DEFERRED，绝不 git reset 代码
- R3+ 触发 Chain Detection 警告（继续 / 拆分新任务 / 重做设计）
- 完成后必须返回编排器，不自行路由下一步
