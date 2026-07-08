---
name: task-execute
user-invocable: false
self-evolving: inbox
description: "Use when executing Phase 4 (Execute) of a task. Can be called standalone or via /task orchestrator. Do NOT use without an approved plan.md. 触发词: \"开始执行\", \"task execute\", \"执行阶段\", \"运行任务\", \"跑 plan\""
word-budget: 2000
---

# Task Execute — Phase 4: Execute

主 session 协调逐个执行 plan.md 的任务，每个任务后轻量验证，全部完成后代码审查。

**Announce at start:** "Using task-execute for Phase 4: Execute."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Check (light): !`tc=$(find .tasks/open -maxdepth 2 -name task-config.json 2>/dev/null | head -1); v=$([ -n "$tc" ] && python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('check',{}).get('light','') or '')" "$tc" 2>/dev/null); if [ -n "$v" ]; then echo "$v"; else r=$(grep -A1 '轻量' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'; fi`
- Check (full): !`tc=$(find .tasks/open -maxdepth 2 -name task-config.json 2>/dev/null | head -1); v=$([ -n "$tc" ] && python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('check',{}).get('full','') or '')" "$tc" 2>/dev/null); if [ -n "$v" ]; then echo "$v"; else r=$(grep -A1 '完整' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'; fi`

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。本 skill 触发点：**phase 入口与 resume 重建**（`full` 删上一 phase step + 建本 phase step；`overview`/`off` 不动 step）；每个 plan task 开始 `in_progress`、完成 `completed`（4b 同理，仅 `full`）。下方展开规则仅 `full` 档适用。

**Phase 4 的 step 级 task 展开规则**（入口与 resume 重建同用）：解析 `{task-folder}/plan.md`，为每个 plan task 建独立 step 级 TODO（而非只建 `4a`/`4b` 两项），末尾附 `→ 4b. 代码 review` 作最后一个 step。每个 plan task 一个 `TaskCreate`，metadata `{"level": "step", "phaseNum": 4, "stepId": "4a-taskN"}`。已完成的 plan task（据 plan.md checkbox 或 Commit Checkpoint 推断）标 `completed`。auto/parallel-agents 模式下，批内每 task 派发即翻 `in_progress`、完成即翻 `completed`，不等整批。

**减少往返**：phase 切换的 delete/create 在单条消息内批量并行；耗时可忽略的步骤可只标 `completed`。

---

## Resume Support

如果 phases.md 存在且 Phase 4 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 4 步骤对应：**
- `4a. 执行任务` → Step 4a（包含所有 plan tasks）
- `4b. 代码 review` → Step 4b

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取。

---

## Process

### Unattended State（每次执行时加载）

1. **读取无人值守状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：
   - 执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
   - 读取全局配置：`cat ${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`（不存在则从 `.example` 复制），解析为 `task_config`
3. **若文件不存在或 enabled != true**：正常交互流程（引擎和 reviewer 从 `design.md` 读取——Design 阶段已确认）

> 无人值守的激活入口与契约（quiet / 交互主入口 / 后备入口、activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5；各阶段 skill 只读已有状态。
> `task_config` 仅 Unattended 模式下由 task-execute 直接读取；Interactive 模式用户已在 Design Step 6.5 基于其推荐值选择并写入 `design.md`，task-execute 读 `design.md` 即可。

---

### 4a. Execution

主 session 协调执行 plan.md 中的任务。读取 `{task-folder}/task-config.json` 确定执行模式。

#### 执行模式分支

| Mode | 行为 |
|------|------|
| **auto** | 按批次决策：整层可隔离（`layer_is_isolatable` 判据，见下方「约束」）**且** 层规模 ≥ `execution.fanout_min_batch`（缺省 3）→ parallel-agents 派发；否则整层 inline。 |
| **inline** | 主 agent 按 plan 顺序串行直接执行，不派发 subagent，保留完整对话历史。 |
| **parallel-agents** | 偏向派发：凡可隔离 layer（含单 task 层）都派 task-executor subagent；否则整层回退 inline。 |

**来源**：读取 `task-config.json` 的 `execution.mode`。

<rule>
未识别的 mode 值（含旧 schema 值 `subagent`）回落到 `inline`。
Reason: `subagent` 是旧 schema 值，已被 auto/parallel-agents 取代；未知 mode 静默并行或报错都会破坏执行，退化 inline 最安全（主 agent 串行、行为确定）。
</rule>

#### engine=codex 派发分支（串行 + dirty-state 协议，优先于 mode 判定）

读 `task-config.json` `execution.engine` + `capabilities.codex`。**engine ∈ {codex, auto} 时先走本分支的统一漏斗**（design Component F / Data Flow）；engine = sonnet/opus 或漏斗未通过 → 回落下方 `route_model()` mode-based 调度。

**A. 每 task engine 解析漏斗（hard gates 优先，与 P2/P3 同序）**：
1. **硬沙盒门槛**：**先 `export CODEX_GIT_ROOT="$(git rev-parse --show-toplevel)"`**（gate 据此判 git-root 子树内绝对写路径为合法；不设则任何绝对路径都判 root 外 → 误 hard-fallback），再对该 plan task 的 Steps + Guardrails 跑 `codex-sandbox-gate`（`hard-fallback:<reason>` exit 2 → 命中）。命中 / plan task 标 `codex:false` → **hard fallback** `route_model()`（`codex:true` 也不能 override 硬门槛）。
2. **capabilities 刷新 + codex-check**：读 `capabilities.codex.checked_at`，过期（>30min）或本 phase 首次 → 派发点 `codex-check` 刷新 `capabilities.codex`。`FALLBACK:`/exit1-fallback → `route_model()`。
3. **cwd 控制门**：见 B（`cwd_control==unsupported` → 硬降级 Claude）。
- engine=auto：过 1–3 → **codex-first**；否则 `route_model()`。engine=codex：同样须过 1–3，不具备则 fallback（不报错）。

**B. cwd 协议（design Component F，R2-Crit1）**：
- **首个 codex execute task 前先 spike**：从已知 `git_root`（`git rev-parse --show-toplevel`，worktree = worktree 根）派一最小 codex 写测试文件，检查其落点 git root 是否 = `git_root`，结果写 `capabilities.codex.cwd_control = verified | unsupported`，**后续所有 P4 dispatch 只读该字段**。spike 须在**首个 dirty-state baseline 采集之前**完成、**用后即删**（唯一临时名如 `.codex-cwd-spike-<rand>`，查完 `rm`；该前缀纳入 baseline 归因的 untracked 白名单），避免污染该 task 的 baseline 快照。
- `cwd_control==verified` → 每次派发前 `cd "$git_root"` 并验证 `pwd` 一致后再派（launch shell cwd 决定沙盒边界，**非** prompt 的 `Working directory is X` 行）。
- `cwd_control==unsupported` → **P4 engine=codex declared unsupported**，全程硬降级 Claude executor（write 正确性优先于卸载 token）。

**C. 并发：per-worktree 隔离**：engine=codex 写操作在**同一工作树**并发会 dirty-state baseline 串扰，故同树仍串行；但**可隔离 layer**（同 `layer_is_isolatable` 判据：每 task 带 `[P]` + Files 不重叠 + 契约门）可经 **git worktree 隔离并行**——每个并行 codex task 一独立 worktree，dirty-state 归因天然 per-worktree。非可隔离 layer / 单 task → 串行单工作树。**覆盖 `mode=inline`**（codex 本身即一次 dispatch）。worktree 生命周期 + 合并见 `references/execute-workflow.md` 的 codex 变体。

**D. mid-flight dirty-state 协议（owner=task-execute；codex `--write` 可能 partial edits）**：

**worktree 并行时**：baseline / `CODEX_GIT_ROOT` / 路径归因 / sandbox-gate 合法写路径全部锚定**该 task 的 worktree 根**（per-worktree，独立 index/status → 归因天然隔离、escalate 只影响该 worktree、不扩散到主树或其它并行 task）。下述「git root」在并行场景即读为「该 task 的 worktree 根」。

每个 codex execute task **派发前完整 baseline** → `{task-folder}/codex-exec-<taskid>.pre`，据此分出路径类：**pre-clean** / **pre-dirty** / **pre-untracked** / **pre-ignored**（baseline / post-snapshot 命令配方见 `references/execute-workflow.md`）。

**中途 fallback 时**（codex 输出 `FALLBACK:` 前缀 / quota / rate-limit）→ 采 **post-snapshot** → `codex-exec-<taskid>.post`，与 baseline 比对得 **codex touched paths**，按路径归因处置：
- 只碰 **pre-clean tracked** → 自动可验证 reverse patch（安全还原）。
- **codex 新建 untracked**（pre 不存在、post 新增）→ **先复制内容到 artifact 留存**，再**定向删除**该新建文件（**禁止全局 `git clean`**）。
- 碰 **pre-dirty / pre-untracked / pre-ignored 同路径** → **绝不自动回滚**（hunk 级归因不可证明、会覆盖用户改动）→ **escalate**。
- 写 **gitignored 路径** → 经 `--ignored` 快照归因，escalate（不自动处置 ignored 内容）。
- 任一不确定 → escalate。**绝不 `git reset --hard` / 绝不全局 `git clean`**。

**escalate（所有模式统一，P4 零阻塞交互）**：写 `fallback-log.jsonl`（`action=paused_dirty_conflict`）+ 保存 baseline，**在 session 内可见地停下并输出冲突报告**，等 `/task` 恢复经下方 resolution menu 决定保留/回滚——不调 AskUserQuestion、不自动续 Claude executor。

**`/task resume` 后 dirty-conflict resolution menu**：检测到 `paused_dirty_conflict` → 三选项（基于 baseline/fallback artifact）：① **keep codex edits** → 继续 Claude executor 接续；② **rollback using baseline**（用 baseline 还原冲突路径）→ 继续 Claude executor 重做；③ **cancel** → 转 task-cancel。**菜单优先读 `TASK_RESUME_CHOICE` 环境变量 / 可注入 menu input fixture（自动化测试接缝）**，把 `resolution=keep|rollback|cancel` 与 executor continuation 写入 `fallback-log`。

**E. fallback-log.jsonl**：任何降级/暂停向 `{task-folder}/fallback-log.jsonl` 追加一行，字段 `phase`（`P4-4a`）、`integration_point`、`requested_engine`、`actual_engine`、`reason`、`codex_check_output`、`agentId`、`action`（+ dirty-state 路径含 `resolution`）。P6 final.md 汇总引用。

> 处置完（非 hard-stop 暂停）后 Claude executor 接续。engine=codex 走通时执行循环以 codex dispatch 替代 inline/派发步骤，其余（light verify / per-task hook / TODO）不变。

#### engine=headless-provider 派发分支（engine 维度第四值，调 claude-dispatch）

`execution.engine == "headless-provider"` 时把实现 task 经 `claude-dispatch`（headless-scheduler 底座）下放给第三方 provider worker。这是 **engine 维度第四值**（与 auto/sonnet/opus/codex 并列，**非** dispatch_backend 扇出维度）；与 codex 分支同序位置——engine=sonnet/opus 或本分支不可用时回落 `route_model()` mode-based 调度。

- **档位边界**：仅派 **mid 及以上档**模型（查 `providers/model-tiers.json`）；命中 weak 档 → 不派、降级 Claude executor（实现质量优先于卸载 token）。
- **产出门**：worker 产出**仍经 P4 code review 门（4b，恒 claude）**，不裸落盘、不绕过 review——调度器中立、质量由 review 把关（design Component D 边界）。
- **派发**：构造 tasks.json（`provider`/`model`=选定 mid+ 档、`prompt`=`IMPLEMENTER_PROMPT.md` 全文 + 该 task plan 段 + Guardrails + TDD 指令、`permission_mode` 按需），`claude-dispatch --tasks ... --output ...` 收集结构化结果；主 session 接续 light verify / per-task hook / checkpoint（同 codex 后端）。
- **守卫（参照 codex 后端，语义一致）**：不写 phases.md / 不触发 hook / 缺失静默回落——`claude-dispatch` 不存在、provider 全不可用、或无 mid+ 档可选 → 回落 `route_model()` Claude executor，不报错。

#### auto / parallel-agents 分层调度

`layers = topological_layers(tasks)`（按 plan `Depends` 拓扑分批），逐层判 `should_dispatch`：auto = 可隔离**且** `len(layer) >= fanout_min`（缺省 3）；parallel-agents = 任何可隔离 layer（含单 task 层）。`inline` 或不满足 → 整层串行 `run_inline`。派发前先 `Read ${CLAUDE_PLUGIN_ROOT}/skills/hatflow-dispatching-parallel-agents/SKILL.md` 取并行纪律，每 task 经 `route_model(task)`（见「模型分流」）派 `task-executor`（注入 IMPLEMENTER_PROMPT.md 全文 + plan 段 + Guardrails + TDD）；`await_all` 后 `handle_hooks_and_checkpoints` 恒在主 session 收口。派发后端默认主 session（≤3），`dispatch_backend==workflow` + 探测到 Workflow → `parallel()` barrier（见「执行后端」）。机读算法骨架见 `references/execute-workflow.md`。

**约束**：
- 同层最大并行 3（超出则分多批）。
- **`layer_is_isolatable(layer)` 判据**：层内**每个 task 标题带 `[P]`**（plan 作者对「与同批 task 真独立、无共享状态」的显式语义断言，机判文件重叠覆盖不到）**且** 每个 task 的 `Depends` 全部完成 **且** task 间改动文件集互不重叠 **且** 通过**契约完整性核验门**（见下）。**任一 task 缺 `[P]` / Files 重叠 / 契约门不过 → 整层为假 → 整层 inline，不拆分派发部分 task**。单 task 层满足这些也算可隔离——故 parallel-agents 对单 task 层也派发，auto 额外要求 `len(layer) >= fanout_min`。
- **契约完整性核验门（并行前必过，否则该层退 inline）**：**已知盲区（debt B2）**——两个 task 各改各的文件却共享一个未声明的契约（task A 改输出格式、task B 消费该格式，而契约另一端未出现在任何 task 的 `Files` 列表），「文件集不重叠」即为假独立、并行会留下悬空引用。核验：plan File Structure 已按 PLAN_PROMPT「列出相邻契约文件」标注契约另一端、且本层不共享未声明契约 → 通过；否则退 inline。**不引入新机制**（仅一道读 plan `Files` 声明的判断）。
- **缺 `Depends` 字段或 task 未标 `[P]`** → 无法判独立性 → 全部顺序串行 inline（旧 plan 无 `[P]` 天然走此路径，向后兼容；恢复并行须补 `[P]`）。
- 派发的 task-executor 注入 `IMPLEMENTER_PROMPT.md` 全文（不让 subagent 去读 plan 文件）。
- mode=inline 忽略 Difficulty/Depends/`[P]`，纯按 plan 顺序串行。

**`[P]` 解析规则（派发器机读）**：对 plan task 标题行按正则 `^##\s+Task\s+\S+:\s+\[P\]\s+\S` 判定——大小写敏感、`[P]` 须为冒号后第一个 token、其后须有非空白 title（末尾 `\S` 锚定）。任何 malformed / 变体标题（缺冒号、`[P]` 在中部或前有其它 token、冒号前空格变体、`[P]` 后无 title）一律判**无 `[P]` → 串行**：宁可保守 false-negative（漏判→inline），不冒 false-positive（误派并行）。

#### 执行后端：可选 Workflow（探测回落，默认主 session 并行派发）

上面 else 分支的「主 session 并行派 task-executor（≤3）+ await_all」是无 hook 的纯实现扇出，可由 Workflow 工具承担。**默认主 session 并行派发；仅当 `execution.dispatch_backend: workflow`（缺省主 session）+ 探测到 Workflow 工具时**，改用 Workflow `parallel()` barrier 派发该层 task-executor（并发上限 min(16,核数-2) 放宽当前硬上限 3）。任一不满足 → **静默回落**主 session 并行派发。

**三守卫（与现状语义一致，脚本骨架 + 详解见 `references/execute-workflow.md`）**：① Workflow 只跑 task-executor 实现、`schema` 强制返回 status，barrier 后 `results` 交回主 session；② `handle_hooks_and_checkpoints` 恒在主 session（per-task-post hook / 卡壳升级计数 / phases.md 写入）；③ 不触发 hook、不写 phases.md、缺失回落。

**适用边界**：engine=codex 不介入（已强制串行）；TDD 指令仍由 prompt 注入、RED 检测仍在收口；现判据已要求 Files 不重叠，同工作树并行无冲突、**不需 worktree**。

#### 模型自动分流（engine=auto，仅作用于被派发的 task）

`route_model(task)` = f(难度, TDD mode, 复杂度/影响面)，优先级 **架构 override > TDD 加权 > 难度基线**：

| 信号 | 规则 |
|------|------|
| 难度基线 | easy/medium → Sonnet；hard → Opus |
| TDD 加权 | tdd.mode=full 且 hard 且**无**架构触发（机械型，spec 清晰 + 红绿灯兜底）→ 降 Sonnet |
| 架构 override（最高优先级，**即"复杂度/影响面"信号的落地**） | task 触 3+ 文件 **或** 含架构关键词（设计/架构/重构/状态机/调度/路由）→ Opus，**不被 TDD 权重压下** |

- engine=sonnet / opus：全部用该模型，不做 per-task 选型。
- **inline task 跑主 agent 当前模型**，不做 per-task 选型。
- **成本依据**：执行大头走 Sonnet（≈ Opus 1/5 价）；parallel-agents 只省墙钟、不减 token 总量（前提 plan 任务已切细自足）。

**模型分级两原则（阈值不变）**：

1. **mid-tier 下限**：派发的 executor 与 design/plan reviewer **不低于 Sonnet**（现有矩阵已满足：难度基线与 reviewer 矩阵均以 Sonnet 为底、code review 恒 Opus/claude）。以防今后误降到 Sonnet 以下。
2. **便宜模型多步反而更贵**：hard / 架构类 task 让 Sonnet 硬扛多步往返时，试错 token 与返工成本常超过 Opus 一次做对——这正是「架构 override → Opus、不被 TDD 权重压下」的理由。

#### 执行循环（每个 plan task）

1. 将当前任务标记为 in_progress（TODO Sync）
2. **P4.per-task-pre hook**：
   ```bash
   hat-plugin-hook {task-folder} P4.per-task-pre
   ```
   hook 输出按段全部执行（tdd: TDD 循环指令注入）。tdd 禁用时该点天然输出空、跳过（无需额外条件化逻辑）。
3. 执行任务（inline 直接执行 / auto·parallel-agents 派发 task-executor）。派发时 prompt 注入 `IMPLEMENTER_PROMPT.md` 全文 + 当前 task 的 Steps + Implementation Guardrails + TDD 指令（P4.per-task-pre 的 tdd 段），并追加 `Report your status as one of: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED.`
4. 处理返回状态：

| Status | 处理 |
|--------|------|
| **DONE** | 继续 |
| **DONE_WITH_CONCERNS** | 正确性问题 → 先解决；观察性 → 记录 |
| **NEEDS_CONTEXT** | 主 agent 提供上下文，重派（最多 2 次） |
| **BLOCKED** | 走 **卡壳升级阶梯**（见下）——非立即上报，先经根因调试 |

5. 运行 **Light verification**（Runtime Context 中的 Check (light) 命令）
6. **P4.per-task-post hook**：
   ```bash
   hat-plugin-hook {task-folder} P4.per-task-post
   ```
   hook 输出按段全部执行（顺序：tdd: RED 异常检测 → review: per-task review → git: formatter → git: commit checkpoint）。
7. 将任务标记为 completed，并**同步勾选 plan.md 中该 task 的 checkbox**（与 phases.md/TODO 同属每步同步集——只更新 phases.md 会让 plan.md 完成态与实际长期脱节）
8. 重复直到所有任务完成

**If Light verification is not configured**: **静默跳过、不询问**（约定 9：Execute 零阻塞交互）。运行期权威是 **task-config.json `check.light/full`**（Design 2e.3 落盘），缺失才回退 CLAUDE.md 验证命令节——此解析顺序已固化在 Runtime Context 的 `Check (light)/(full)` 取值。两者皆无即视为「无 light 验证」，直接继续。

<rule>
包裹外部 CLI 的脚本（如调用 `claude` / `claude-hl` / 其它命令行的 bash）在 P4 开发期跑一次真实冒烟，不延到 Phase 5。stub 单测只验「调用方传了什么」，建模不了外部 CLI 的真实语义（变长参数贪婪吞后续位置参数、bash IFS 连续空白折叠吞空字段、PATH 解析）。
Reason: 这类脚本的 stub 单测会全绿、端到端却全挂——契约层与真实调用语义之间有 gap，唯有真实冒烟能在开发期暴露；延到 Phase 5 才跑等于把可在 P4 发现的失败拖到验收期。
</rule>

#### 卡壳升级阶梯

Light verify 失败、或 inline 卡壳、或被派发 task-executor 返回 BLOCKED，统一走这条阶梯——**首步固定为根因调试**：上报与换模型均后置于根因定位（非一卡即触发）。

1. `Read ${CLAUDE_PLUGIN_ROOT}/skills/hatflow-systematic-debugging/SKILL.md`（Iron Law：无根因不修——先复现/定位，再动手）。
2. 按根因做**单点修复**，重跑 verify。
3. **计数 per stuck-point**（同一 task 内同一卡点累计；换到下一个 task 时归零）：
   - **计数由主 agent 在会话上下文维护**（task-executor 无状态、重派不记得上一轮）。每次 BLOCKED / inline 卡死时比对卡点描述是否与上次同一（同 task + 同根因症状），是则 +1，否则视为新卡点从 1 起算。
   - **< 3 次** → 回到本阶梯第 1 步（hatflow-systematic-debugging 的根因定位，**不是** task 的 Phase 1 Init）继续调试。
   - **≥ 3 次，或判定为架构级问题** → 升级。
4. **升级动作**（subagent BLOCKED 与 inline 卡死同属此阶梯）：补上下文重派 → 换更强模型（Sonnet→Opus）重试一次 → 拆小 task → 仍无解则按模式终结，**不弹阻塞菜单**（约定 9：Execute 零阻塞交互）：在 session 内**可见地停下并输出清晰报告**（卡点描述 + 已尝试的根因修复 + 建议下一步如转 Revise/拆分），phases.md 状态不变，用户回来后 `/task` 恢复。Telegram 通知为 best-effort **叠加**，不替代可见停止。

完成后（所有 plan tasks 执行完）：更新 phases.md，将 `4a. 执行任务` 标记为 `[x]`。

### P4.post-execute Hook（4b. 代码 review）

所有 task 完成后，运行：

```bash
hat-plugin-hook {task-folder} P4.post-execute
```

hook 输出包含多段指令，**必须逐段全部执行**（顺序：review: 全量代码审查 → review: Revise 触发检测）。

<rule>
`P4.post-execute` hook 输出的所有指令段按顺序全部执行（full-review → revise-detection）；4b 标完成的前提是两段都已执行——只完成 full-review 段不算完成。
Reason: 部分执行 hook 会静默丢掉 revise-detection 段，于是本应触发 Revise Cycle 的系统性问题漏检。
</rule>

**4b 自验范围判据**：本任务含改名、跨模块改动、或改了受 golden/fixture 覆盖的源文件时，4b 自验跑**全量测试套件**而非仅本批次直接相关测试——间接波及（如改名连带 golden 快照失配）只有全量才能在 pre-commit 之前暴露。

**核心行为保留**：
- Revise Cycle 检测：核心步骤 4a 进入时先检查 phases.md 是否有 IN_PROGRESS 的 Revise section
- 回归模式：检查 4b 是否有 `[→ REVISE RN]` 标记，如有则限定 review scope
- 回归模式下 Return 步骤标记由 task-execute 负责
- review 阶段的修复提交顺序：分析 → 修复 → 用户测试 → 用户确认 → 之后才提交（即便修复看似显然，commit 前置于用户确认）

**4b 收敛是跨回合异步 join 循环**（机制单一来源 = `review.md ## P4.post-execute/convergence`，此处仅接线）：
- Round 1 reviewer 用 `run_in_background=true` 派发、捕获 agentId；主线程派发/复活后**结束本回合**，completion notification 按 `task-id` 重入累积，收齐「期待 agentId 集合」才推进判 C/I（未命中的 linear-sync / 用户 notification 正常吸收、不推进）。
- agent→{维度}→agentId 映射写入 phases.md 4b 行 `[→ 收敛 Rn agents:...]` 标注，与 `[→ REVISE RN]` 回归标注**互斥**（进入 Revise 即清收敛标注；回归检测精确匹配 `REVISE` 前缀、不误捕 `收敛`）。
- **进入 4b 标注分诊**（resume / compaction / 首次统一适用，消除入口歧义）：① 有 `[→ REVISE RN]` → 回归模式；② 否则有 `[→ 收敛 Rn agents:...]` → 从标注恢复 agentId 尝试复活，失效（agent 已死 / resume 新 session）则该维度全新派发（兜底见 review.md convergence）；③ 皆无 → 正常首轮。

完成后（非 revise 触发路径）：更新 phases.md，将 `4b. 代码 review` 标记为 `[x]`。

### Execute 完成 → 过渡

Phase 4 完成，phases.md 已更新。

用用户配置的语言简要宣告执行结果（执行的 task 数量、code review 状态），然后声明：**"Execute 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

<rule>
Phase skill 完成后返回编排器 Step 3；transition section 不提示用户调用 `/task-end`、`/task-test` 或其他 skill。过渡路由（产物检查、新会话交接建议、unattended 检查等）归编排器。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、新会话交接、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## phases.md Sync

每个步骤完成后更新 phases.md。每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

**Phase 4 完成时**：将 Phase 4 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

**Revise 触发时**：Phase 4 的 Status **保持 `IN_PROGRESS`**，不标记为 DONE（4b 回归模式入口分诊见上方「进入 4b 标注分诊」）。

---

## Mandatory Stop Points

> **约定 9 Interaction Front-Loading**：Execute(P4) 零阻塞交互。下表无「要求用户应答才能继续」的停顿点——P4 不弹 AskUserQuestion。

| Step | When | 行为（非阻塞） |
|------|------|-------------|
| 4a | Light verification 未配置 | **静默跳过验证**，不询问（验证命令前置到 Design 决定） |
| 4a | 卡壳升级阶梯 ≥3 次或架构级问题（含 subagent BLOCKED 升级末端） | session 内可见停下 + 报告（不弹菜单） |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Reads**: `{task-folder}/plan.md`, `{task-folder}/task-config.json`（含 `execution.engine` + `capabilities.codex`）
- **Writes**: `{task-folder}/phases.md`；**engine=codex 时**：`{task-folder}/fallback-log.jsonl`、`{task-folder}/codex-exec-<taskid>.pre`/`.post`（dirty-state baseline/快照）、`capabilities.codex.cwd_control`（spike 回填）
- **Injects（派发 task-executor 时）**: `IMPLEMENTER_PROMPT.md`（全文注入实现者 prompt）
- **References**: `hatflow-dispatching-parallel-agents`（独立批次并行派发纪律）, `hatflow-systematic-debugging`（卡壳升级阶梯根因定位）, `review.md`（engine 解析漏斗与 P2/P3 同序）
- **Scripts（engine=codex）**: `codex-sandbox-gate`（硬门槛）, `codex-check`（capability 刷新）；测试接缝 `TASK_RESUME_CHOICE` 环境变量
- **Hooks**: `P4.per-task-pre`（tdd）, `P4.per-task-post`（tdd + review + git）, `P4.post-execute`（review）
- **Scripts**: hat-plugin-hook
