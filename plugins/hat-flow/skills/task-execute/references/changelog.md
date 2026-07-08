# task-execute changelog

（最新在最上）

## 2026-07-08 TODO Sync：P4 step 展开覆盖 resume 重建 + 并发批逐 task 翻状态

skill-revise 定向修订（与 task 套件同批，见 task 套件 changelog 2026-07-08 条）。TODO Sync 触发点从「phase 入口」扩为「phase 入口与 Bootstrap/resume 重建」；Phase 4 step 展开规则声明重建以 plan.md 为源（不按 phases.md 4a/4b 粒度），auto/parallel-agents 模式批内每 task 派发即翻 in_progress、completion 到达即翻 completed。为何：full 档下 resume 后 step 级 TODO 退化为 4a/4b 两行（用户实测只见阶段概览更新）；新会话交接机制落地后 P4 常从 resume 进入。另：transition rule 中「compact 建议」机制名随编排器改为「新会话交接建议」。

## 2026-07-07 正文瘦身至 word-budget 2000 内（2404 → 1997 词）

只压缩表述、未改结构性语义。所有步骤号（4a/4b）、hook 调用点（P4.per-task-pre / P4.per-task-post / P4.post-execute）、执行模式判据（auto/inline/parallel-agents、`layer_is_isolatable`、`fanout_min_batch`）、engine 分支（codex / headless-provider）、`capabilities.codex.cwd_control` spike 回填、`IMPLEMENTER_PROMPT.md` 注入契约、`route_model`、dirty-state 归因与 escalate/resolution menu、对 hatflow-dispatching-parallel-agents / hatflow-systematic-debugging 的引用路径、返回编排器 Step 3 均原样保留。

改法：
- TODO Sync 按薄引用纪律收敛——删 overview ASCII 示例与「执行中更新」重复段，保留 Phase-4 特有 per-plan-task step 展开规则 + metadata。
- 下沉到 `references/execute-workflow.md`：codex dirty-state baseline/post-snapshot 命令配方、auto/parallel-agents 分层调度机读算法骨架（规则权威仍在正文「约束」prose）。
- Workflow 执行后端三守卫收敛为一行 + 指回 execute-workflow.md（该文件已有三守卫详解）。
- 合并重复说理：mode 表指回下方 `layer_is_isolatable` 判据、模型分级两原则去掉与表格重复的复杂度/影响面注、phases.md Sync 的「4b 回归模式优先」并入 4b 分诊（去重）、契约门去掉重复的 debt B2 表述。
