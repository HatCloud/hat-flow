# task-plan

Phase 3（Plan + Commit）worker：把已批准的 design 按模板落成 plan.md（bite-sized tasks + 精确文件路径），经 plan-reviewer 忠实度评估收敛后提交任务文档、同步 Linear。由 `/task` 编排器在 Phase 2 完成后派发，也可单独调用。完整流程与收敛判据以 `SKILL.md` 为准。

## 补充信息

- **SC2 二元契约的由来**（历史决策）：plan review 曾按数值评分 + 阈值 + 分层轮次矩阵运作，后简化为单 plan-reviewer、single-pass、`Verdict: Approved | Issues` 纯二元判据——「计划是否忠实于设计」是契约式问题，数值分只添加伪精度。
- **模板来源**：plan.md 模板在 `task/PLAN_PROMPT.md`，运行时嵌入；改模板改该文件，不改本 skill。
- **codex reviewer 路径**：reviewer 解析为 codex 时输出改三级 severity + `bin/codex-findings-count` 判收敛，与 SC2 verdict 等价映射；quota / 不可用时自动降级 native plan-reviewer 并留 fallback 日志。
