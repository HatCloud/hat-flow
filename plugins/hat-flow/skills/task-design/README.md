# task-design

Phase 2（Design）worker：探索上下文、澄清需求、方案比选、逐节确认并产出 design.md，经 reviewer subagent review 后等待用户明确批准。由 `/task` 编排器在 Phase 1 完成后派发，也可单独调用。完整流程以 `SKILL.md` 及其嵌入的协议为准。

## 补充信息

- **薄层架构**：SKILL.md 本身只是编排薄层（announce / runtime context / hooks / resume / 配置精调 / 过渡），设计流程的步骤、模板、复杂度矩阵、原则的单一来源是运行时 `!cat` 嵌入的 `task/DESIGN_PROTOCOL.md`——改设计流程要改协议文件，不是改本 skill（spec-task-skill 的 Protocol File as Single Source 约定）。
- **visual companion**：需要像素级 mockup 确认时 just-in-time 起浏览器伴随页（仅 Interactive 路径，无头跳过），实现见 `visual-companion/visual-companion.md`。
- **联网调研接线**：Step 1.5 可选调 `web-research` 引擎（quick 档）补外部信息，verified 结论折进 design 探索段；无人值守保守档默认跳过。
