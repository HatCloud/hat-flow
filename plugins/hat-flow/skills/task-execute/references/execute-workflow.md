# Execute 层并行实现 Workflow 后端（可选 · 探测回落）

P4.4a auto/parallel-agents 分层调度的「可隔离 layer 并行 task-executor 实现」的 Workflow 编排骨架。**仅当 `execution.dispatch_backend: workflow` 且探测到 Workflow 工具时启用；否则静默回落主 session 并行派发（≤3）**（见 `task-execute/SKILL.md` 的「执行后端」节）。

## auto / parallel-agents 分层调度算法骨架

`SKILL.md ## auto / parallel-agents 分层调度` 的机读形式（规则权威仍在 SKILL.md 的「约束」prose）：

```
fanout_min = config.execution.fanout_min_batch   # 缺省 3
layers = topological_layers(tasks)   # 按 plan 的 Depends 字段拓扑分批
for layer in layers:
  # auto：整层可隔离且 len>=fanout_min 才派（整层 gate，不拆 task 子集）
  # parallel-agents：任何可隔离 layer（含单 task 层）都派
  should_dispatch = (mode == "auto"            and layer_is_isolatable(layer) and len(layer) >= fanout_min) \
                 or (mode == "parallel-agents" and layer_is_isolatable(layer))
  if mode == "inline" or not should_dispatch:
    for task in layer: run_inline(task)        # 串行，主 agent 直接执行
  else:
    Read ${CLAUDE_PLUGIN_ROOT}/skills/hatflow-dispatching-parallel-agents/SKILL.md   # 取并行派发纪律
    # 并行派发后端：默认主 session（≤3）；dispatch_backend==workflow 且探测到 Workflow 工具 → Workflow parallel() barrier
    for task in layer (up to 3 parallel):
      model = route_model(task)                # 见 SKILL.md「模型自动分流」
      dispatch task-executor(agent_role=task-executor, model=model,
                             prompt = IMPLEMENTER_PROMPT.md 全文
                                    + 该 task 的 plan 段落 + Guardrails + TDD 指令)
    await_all(layer); handle_hooks_and_checkpoints(results)   # barrier + 主 session 收口（恒主 session）
```

## 三守卫（不得突破）

1. **不写 phases.md** —— Workflow 只跑实现返回 status，phases.md 由主 session 收口写。
2. **不触发 hook** —— per-task-post hook（tdd RED 检测 / review / git commit checkpoint）由主 session 在 barrier 后的 `handle_hooks_and_checkpoints` 调，Workflow 内不调 `hat-plugin-hook`。
3. **缺失静默回落** —— 探测不到 Workflow → 主 session 并行派 task-executor（现状 ≤3）。

## 适用前提（与主 session 路径同判据）

- `layer_is_isolatable`：每 task 带 `[P]` + Depends 完成 + Files 不重叠 + 契约门过。
- `engine ≠ codex`（codex 强制串行，不进 Workflow）。
- Files 不重叠 → 同工作树并行无写冲突，**不需 worktree**（worktree 留作未来放宽该判据的可选增强）。

## 输入（主 session 解析后经 `args` 传入）

- `tasks`: 该 layer 的 task 列表，每项 `{id, plan_excerpt, model, guardrails, tdd_directive}`。
- `implementer_prompt`: `IMPLEMENTER_PROMPT.md` 全文（主 session 读后传入；Workflow agent 不自读 plan 文件）。

## 脚本骨架

```javascript
export const meta = {
  name: 'execute-layer',
  description: 'P4 可隔离 layer 并行 task-executor 实现（无 hook 纯扇出）',
  phases: [{ title: 'Implement' }],
}
const STATUS = {
  type: 'object', additionalProperties: false,
  required: ['task_id', 'status', 'summary'],
  properties: {
    task_id: { type: 'string' },
    status: { type: 'string', enum: ['DONE', 'NEEDS_CONTEXT', 'BLOCKED'] },
    summary: { type: 'string' },
    files_touched: { type: 'array', items: { type: 'string' } },
  },
}

phase('Implement')
const results = await parallel(args.tasks.map(t => () =>
  agent(
    `${args.implementer_prompt}\n\n【本 task】\n${t.plan_excerpt}\n【Guardrails】\n${t.guardrails}\n【TDD】\n${t.tdd_directive || '(无)'}`,
    { label: `impl:${t.id}`, phase: 'Implement', model: t.model, agentType: 'task-executor', schema: STATUS })))
return { results: results.filter(Boolean) }
```

## 主 session 收口（barrier 后，恒主 session）

1. 读 `results`，对每个 task 按 status 处置：
   - `DONE` → light verify + per-task-post hook（tdd RED 检测 / review / git formatter / git commit checkpoint）。
   - `NEEDS_CONTEXT` / `BLOCKED` → 卡壳升级阶梯（补上下文重派 / 换更强模型 / 拆小），**计数器主 session 维护**。
2. 写 phases.md 4a 行状态。
3. 以上全部主 session 做，Workflow 不碰。

## A/B 对账（首次启用必做）

对同一可隔离 layer 跑两次：现状（主 session ≤3 并行派发）vs Workflow（`parallel()` barrier，并发可 >3）。`parallel-agents` 只省墙钟不减 token，故对账重点是**墙钟 + 稳定性（BLOCKED 率 / 合并冲突）**，净收益为正再常开 `execution.dispatch_backend`。

## codex dirty-state baseline / snapshot 命令配方

`SKILL.md` D 节 mid-flight dirty-state 协议的可复现命令（并行场景各命令锚定该 task 的 worktree 根）。

**派发前完整 baseline** → `{task-folder}/codex-exec-<taskid>.pre`：
```
git rev-parse HEAD
git status --porcelain=v1 -z
git status --ignored --porcelain=v1 -z          # 覆盖 gitignored（R5-Imp1）
git diff --binary ; git diff --cached --binary
# + pre-existing untracked/ignored 文件内容快照（复制/tar 到 artifact，使 baseline 可重放，R3-Crit1）
```

**中途 fallback 时采 post-snapshot** → `codex-exec-<taskid>.post`：post `git diff --binary` + post `git status --porcelain=v1 -z` + post `git status --ignored --porcelain=v1 -z`，与 baseline 比对得 **codex touched paths**，再按 SKILL.md D 节的路径归因表处置。

## codex 变体：per-worktree 并行（engine=codex）

engine=codex 的可隔离 layer 并行——codex 写操作在同一工作树会 dirty-state 串扰，故每个并行 codex task 分配**独立 git worktree**（codex runtime 按 workspace-root hash 隔离 broker/state；**实测**两个并发 codex 各落各 worktree、互不污染、不串主 repo）。

**worktree 生命周期（每个并行 codex task）**：
1. `git worktree add --detach <wt-path> HEAD`（基于当前 plan 基线）。
2. `cd <wt-path>`；设 `CODEX_GIT_ROOT=<wt-path>`、codex `-C <wt-path> -s workspace-write`。
3. 派 codex `/codex:rescue --write`；dirty-state baseline / 路径归因 / sandbox-gate 合法写路径全部锚定 `<wt-path>`（per-worktree，escalate 只影响该 worktree）。
4. codex 完成 → 该 worktree 内 `git add -A && git commit`（或取 `git diff` patch）。
5. barrier 后**主 session** 把各 worktree 的 commit 合并回主工作树（Files 不重叠 → cherry-pick / apply patch 无冲突）。
6. `git worktree remove --force <wt-path>`（失败用 `git worktree prune` 兜底）。

**守卫（同 Claude 变体）**：不写 phases.md、不触发 hook、缺失回落（Workflow / worktree 不可用 或 `cwd_control==unsupported` → 主 session 串行 codex，即现状）。

**与 Workflow 的关系**：可用 Workflow `parallel()` + `isolation:'worktree'`（每 agent 一 worktree 内跑 codex），或主 session 手动管理 worktree。codex 的 broker/state 按 worktree 天然隔离，与 Workflow worktree 隔离叠加无冲突。
