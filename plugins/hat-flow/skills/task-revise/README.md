# task-revise

Revise Cycle 处理器：Phase 4/5 发现系统性问题时，在 phase 内执行一个自适应单循环（根因分析 →（按需）改 design/plan → 执行修复 → 验证收尾）。由 task-execute（4b）/ task-test（5d）触发、经 `/task` 编排器路由，不单独使用。完整步骤与规则以 `SKILL.md` 为准。

## 补充信息

- **弃深度档位的历史决策**：早期版本按 Full/Partial/Lite 三档预设修订深度，后改为自适应单循环——是否触及 design/plan 由根因分析决定、按需把步骤插入 phases.md 的 Revise section（不出现的步骤即不执行，无 `[~]` 跳过标记），预设档位与真实根因经常错配。
- **Root-Problem 立场**：修复中暴露根本性问题时升级为 DEFERRED + WIP commit，绝不 `git reset` 丢弃代码——已写的代码是后续任务的输入而非废料。
- **链式防护**：R3+（第三次 revise）触发 Chain Detection 警告（继续 / 拆新任务 / 重做设计）——连环 revise 是「任务本身该重切」的信号，不是继续修的理由。
