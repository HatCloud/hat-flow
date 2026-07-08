---
name: task-design
user-invocable: false
self-evolving: inbox
description: "Use when executing Phase 2 (Design) of a task. Can be called standalone or via /task orchestrator. Do NOT use before Init or to revise an approved design (use task-revise). 触发词: \"开始设计\", \"task design\", \"设计阶段\", \"进入设计\""
word-budget: 2000
---

# Task Design — Phase 2: Design

任务设计阶段的**编排薄层**：announce、加载 runtime context、嵌入 DESIGN_PROTOCOL、调用 hooks、TODO sync、resume、配置精调、过渡。完整设计流程（步骤、模板、复杂度矩阵、原则）的单一来源是下方 `!cat` 嵌入的 DESIGN_PROTOCOL.md——本文件不重述其内容。

工具落点按 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/harness-tools.md` 映射。

**Announce at start:** "Using task-design for Phase 2: Design."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

> 若上方任一探测/注入行未展开（显示字面 `!` 前缀原文），先当场执行该命令 / Read 该文件取结果，再继续。

## DESIGN_PROTOCOL (pre-loaded):

设计流程的步骤、模板、复杂度矩阵、原则全部定义在此协议中。按 Step 1-8 顺序执行。

- **设计范围限于需求本身（YAGNI）**：只设计 prompt.md 已要求的内容，不主动加入需求外的功能 / 扩展点。

<DESIGN_PROTOCOL>
!`cat ${CLAUDE_PLUGIN_ROOT}/skills/task/DESIGN_PROTOCOL.md`
</DESIGN_PROTOCOL>

> 若上方 DESIGN_PROTOCOL 未展开（仅见字面注入行），先 Read `${CLAUDE_PLUGIN_ROOT}/skills/task/DESIGN_PROTOCOL.md` 再继续——按「协议单一来源」约定本文件不重述其内容，协议缺失等于整段设计流程丢失。

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**phase 入口**（`full` 删上一 phase step + 建本 phase step；`overview`/`off` 不动 step——概览符号由 orchestrator 在 phase 切换时更新）；每个 Step 完成后将对应 phases.md 行标记 `[x]`（`full` 另 `维护进度清单，状态置 `completed``）。

---

## Resume Support

如果 phases.md 存在且 Phase 2 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 2 步骤对应（DESIGN_PROTOCOL 的 Step）：**
- `探索项目上下文` → Step 1 + 1.5（联网调研折叠在本地探索之后执行，phases.md 无独立步——从本步恢复即覆盖 1.5）
- `澄清问题` → Step 2
- `提案` → Step 3
- `逐节展示设计` → Step 4
- `编写 design.md` → Step 5（Step 2e 配置精调折叠在此步之后执行，phases.md 无独立步——从本步恢复即覆盖 2e）
- `自我 review + Review 策略确认` → Step 6 + 6.5
- `独立 review` → Step 7
- `确认设计` → Step 8

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取（或由编排器传入）。

---

## Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议，后续所有停止点按协议自动决策
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守的激活入口与契约（quiet→task-init 1f / 交互主入口→编排器 Step 2A.1 / standalone 后备→本 skill Step 2e Activation Timing；activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 读取已有状态。

---

## Step 2e: 配置精调

design.md 初稿（DESIGN_PROTOCOL Step 5）完成后执行。task-config.json 已在 P1 Step 1b.3 写入并据此选定 preset；此处仅在**复杂度与已选 preset 明显偏离时**才弹面板修正，一致则静默沿用。

**Step 2e.1: 复杂度评估**

基于 design.md 内容，用 DESIGN_PROTOCOL 的 Complexity Assessment 信号矩阵评估复杂度（Low/Medium/High）。

**Step 2e.2: 偏离判断（轻量化条件触发）**

**[Quiet] headless 短路（最先判断）**：读取 `{task-folder}/task-config.json` 的 `_source` 字段。若 `_source == "headless"`（由无头入口在 1f 物化）→ 不弹面板，静默沿用现有 task-config.json；复杂度评估仍照常跑（结果写入下面 2e.3 的 design.md 策略段），直接进入 2e.3。无头流程在此不引入交互。

将评估出的复杂度与 P1 Step 1b.3 已选 preset 对应的复杂度对比：

- **一致 / 仅小幅偏离** → 静默沿用现有 task-config.json，不弹面板，直接进入 2e.3 写 design.md 策略段。
- **明显偏离**（如 preset 为 lite 但 design.md 评估为 High，或反之）→ 弹 向用户提问（结构化选项优先） 配置面板修正：

  | 配置项 | 当前值 | 推荐值 | 说明 |
  |--------|--------|--------|------|
  | 执行模式 | auto/inline/parallel-agents | ... | 基于复杂度推荐；auto 按 plan Depends 拓扑分批派发 |
  | 引擎 | auto/sonnet/opus | ... | auto 时按难度 + TDD 加权 + 架构 override 自动分流模型 |
  | Design review 轮次 | auto/0/1/2 | ... | 基于复杂度 |
  | Reviewer 模型 | claude | ... | 按矩阵 |
  | Plan review 模型 | sonnet/opus | ... | 按维度×难度 |
  | Code review 级别 | skip/light/medium/full | ... | 基于复杂度 |
  | Per-task review 粒度 | each/checkpoint | ... | checkpoint 缺省（省派发数、流程更短）；高敏感任务建议升级 each，仅 medium/full 下有意义（见 Step 2e.2b） |

  用户确认或调整后执行 2e.3。

**Step 2e.2b: 敏感度升级判断（独立触发，不依赖复杂度偏离）**

仅当 `code_review ∈ {medium, full}` 且当前 `per_task_review == "checkpoint"` 时评估（否则跳过本步）。基于 design.md 判断本任务是否触及**高敏感面**：对外契约/API、认证授权、资金/支付、数据迁移、安全边界、不可逆操作、核心数据 schema。

- **非高敏感** → 不动 `per_task_review`，沿用 checkpoint。
- **高敏感** → 弹 向用户提问（结构化选项优先） 建议把**整个任务**的 `per_task_review` 升级为 `each`（任务级，对所有 plan task 逐个派 code-reviewer）：选项 `升级 each（逐 task review，质量优先）` / `保持 checkpoint（仅全量兜底）`，并在问题里点明命中的敏感面。用户选 `each` → 并入下方 2e.3 写入 `task-config.json`（per_task_review 变更不改 phases.md 结构，phases.md 重生成对它为 no-op）。

**Step 2e.3: 变更执行**（仅当面板触发且有变更并经用户确认时执行前 2 步）

1. 就地更新 `{task-folder}/task-config.json`
2. 重生成 `{task-folder}/phases.md` 步骤列表（使用与 P1 Step 1b.3 相同的动态生成逻辑：按 `phase_merge` 合并 Phase 节、按 `plugins.*.enabled` 裁剪步骤）
3. 无论是否弹面板，将 `## Execution Strategy` + `## Review Strategy` 写入 design.md
4. **验证命令前置**（约定 9 Interaction Front-Loading）：把 Acceptance Tests 阶段确认的 light / full 验证命令写入 `{task-folder}/task-config.json` 的 `check` 字段（如 `"check": {"light": "...", "full": "..."}`），供 Execute 直接读、无需再问。无可自动验证项则写空/省略，Execute 视为「无 light 验证」静默跳过。
   落盘前按产物语言归类校验器：bash 脚本→shellcheck、python 脚本→py_compile/pytest（按扩展名/shebang 判），勿把 python 脚本列进 shellcheck 段——否则 Phase 5 完整验证报 SC1071 白扣一轮。

**配置校验**（变更时执行）：
- `tdd.mode != "none"` 自动设置 `tdd.enabled = true`

**Step 2e.4: Codex capability 持久化**（reviewer/engine 含 codex/auto 时，**不依赖面板是否触发**）

当 `task-config.json` 的 `plugins.review.reviewer` ∈ {`codex`, `auto`} 或 `execution.engine` ∈ {`codex`, `auto`} 时，运行 `codex-check`（额度门已内含），把结果写入 `task-config.json` 的 `capabilities.codex`（**由本 phase skill 写入，非 `hat-task-config-resolve`**）：

```json
"capabilities": { "codex": { "checked_at": "<ISO>", "status": "ready|fallback", "reason": "<codex-check stdout/stderr 文本>", "quota_state": "ok|stale|unknown|low", "cwd_control": "unknown" } }
```

- `cwd_control` 此处先留 `"unknown"`，由 P4 task-execute 首个 codex execute 前的 cwd spike 回填 `verified|unsupported`。
- **失效规则**：`checked_at` 超 30min 或进入新 phase 即视为过期，由各派发点（P2/P3/P4 dispatch）二次 `codex-check` 刷新覆盖（design Component C）。
- reviewer/engine 均不含 codex/auto 时跳过本步（不写 capabilities）。

### Activation Timing（unattended activate_after，与编排器共享契约 SC3）

**standalone 后备入口**：交互主入口是编排器 Step 2A.1（经编排路径进入 Design 时必已先问过并写入文件）；本节仅在 task-design 被独立调用、`unattended.json` 尚不存在时兜底询问。

**守卫（先判）**：读取 `{task-folder}/unattended.json`。**文件已存在即跳过询问**——无论 `declined == true`（已拒绝，短路优先于 activate_after）、`enabled:true`（已激活，含 quiet 入口在 1f 物化的 headless 状态）还是 `enabled:false` 带 `activate_after`（延后激活已选定，重复询问即双问），各状态语义见 `UNATTENDED_PROTOCOL.md` §5。

文件不存在时用 向用户提问（结构化选项优先） 提供四个选项：

| 选项 | 含义 | 动作 |
|------|------|------|
| 现在启用 | 立即进入无人值守 | 写 `unattended.json`（`enabled: true`, `activate_after: "now"`） |
| Design 阶段结束后启用 | 本阶段仍交互，过渡后激活 | 写 `unattended.json`（`enabled: false`, `activate_after: "design"`） |
| Plan 阶段结束后启用 | Design + Plan 交互，Plan 后激活 | 写 `unattended.json`（`enabled: false`, `activate_after: "plan"`） |
| 否 | 全程交互 | 写拒绝哨兵 `unattended.json`（`{"enabled": false, "declined": true}`），使后续过渡点不再重复询问 |

`unattended.json` 字段 `activate_after: "now" | "design" | "plan"`（缺省视为 `now`）。激活动作（把 `enabled` 翻为 true）由编排器在对应阶段过渡时按 `activate_after` 触发。

---

## Step 6/7/8 Hooks 与 Review 循环

DESIGN_PROTOCOL 的 Step 6 / 6.5 通过 hook 委托 review plugin；Step 7 独立 review 与 Step 8 确认循环的编排细节如下。

### Step 6 — P2.post-design-draft Hook

```bash
hat-plugin-hook {task-folder} P2.post-design-draft
```

hook 输出可能含多段指令，逐段全部执行（review plugin：自我审查 + 独立 review）；遗漏任一段会让该 hook 的对应检查静默失效。review plugin 关闭时：执行最小化自我检查（placeholder scan + internal consistency），跳过独立 review。

### Step 7 — Independent Review 循环

<rule>
design_rounds > 0 时，至少派发一个 reviewer subagent。未实际跑 review 就把该步骤标记为 [x] 会让此 gate 形同虚设。
Reason: dogfooding 发现 design_rounds > 0 时 review 被静默跳过，导致设计缺陷流入执行阶段。
</rule>

**review plugin 关闭时**：跳过本步骤，直接标记 `独立 review` 为 `[x]`。

**Reviewer 解析（codex-aware，派发前先判）**：按 `review.md ## P2.post-design-draft` 的「Reviewer-aware 派发（codex 分支）」解析 reviewer（读 `task-config.json` `plugins.review.reviewer` + `capabilities.codex`；过期/跨 phase → 派发点二次 `codex-check` 刷新）。
- **解析为 `claude`/`sonnet`/`opus`** → 走下面 native design-reviewer 收敛循环（并行 R1/R2 矩阵）。
- **解析为 `codex`**（`auto` 且 codex-first 成立亦归此）→ 改走 review.md codex 分支：经 `/codex:rescue`（read-only）**串行** R1/R2（codex 不并发），输出 `## Critical/Important/Minor` + 末行计数，`codex-findings-count` 判 **C=0 & I=0** 收敛，round≥2 `定向续接某代理（按具体 agentId）` 续接。下面第 2–5 步的批判评估/修复/收敛检查逻辑**不变**，仅派发载体（codex vs native）与并发性（串行 vs 并行）不同。中途 `FALLBACK:`/quota → 降级 native design-reviewer（见 review.md，写 `fallback-log.jsonl`）。

<rule>
Reviewer 解析为 codex（reviewer=auto 且 `codex-check` READY，或 reviewer=codex）时，派发走 review.md 的 codex 分支。只有在 hard-fallback 触发条件下（需要 network / sandbox gate / quota / codex 输出 `FALLBACK:`）才允许降级到 native design-reviewer，且每次降级都向 `{task-folder}/fallback-log.jsonl` 追加一行（`requested_engine:"codex", actual_engine:"claude", reason:<text>`）。"native 更简单 / 更快" 不构成 fallback 触发条件。
Reason: dogfooding 抓到一次运行解析为 codex（auto + READY）却"为了快"派发了 native design-reviewer，静默降低了 review 深度——随后那次 codex review 暴露出 2 个 Critical 发现，native 路径很可能会漏掉。一次未记录的降级会掩盖"配置的 reviewer 其实从未真正运行过"这一事实。
</rule>

**收敛模式核心循环：**

1. **并行派发** R1（结构审查）+ R2（对抗审查），均派发只读 reviewer 子代理 `design-reviewer`（保留模型档位 override，按下方矩阵在派发时指定；Claude 档位见 `harness-tools.md`）：

   | 轮次类型 | Low | Medium | High |
   |----------|-----|--------|------|
   | 常规轮次 (R1) | 常规档 | 常规档 | 加强档 |
   | 对抗轮次 (R2) | 常规档 | 加强档 | 加强档 |

   R2 prompt 追加"对抗审查员"角色说明 + R1 findings + design.md diff。

2. **主 agent 批判性评估**所有发现：逐条 Accept/Reject，每条附理由——Accept 与 Reject 均需具体理由支撑，逐条独立裁决。
3. 对接受的问题修复 design.md，对拒绝的问题记录反驳理由。
4. **检查收敛**：分别记录 R1 和 R2 是否仍有未解决的 C/I：
   - 两者都无 C/I → 收敛完成，进入 Step 8
   - 仅 R1 有 C/I → 下轮只重跑 R1
   - 仅 R2 有 C/I → 下轮只重跑 R2
   - 两者都有 → 下轮并行重跑两者
5. **下轮 prompt** 注入上轮 findings + 修复/反驳清单（防止已反驳问题反复出现）。
6. 循环直到收敛或达 `max_rounds`。
7. **max_rounds 退出**时：展示剩余 findings + 向用户提问（结构化选项优先） 确认是否接受当前状态推进。

轮次数量由 `review.design_rounds` 决定（auto 按复杂度：Low:0, Medium:1, High:2），`max_rounds` 上限兜底（**reviewer-aware**：`max_rounds` 为标量则两 reviewer 共用；为对象 `{claude:N, codex:M}` 时 claude 取 `.claude`、codex 取 `.codex`，缺省 claude 3 / codex 8——codex 更严、收敛更慢）。`design_rounds: 0` 时跳过本步骤。

### Step 6.5 — P2.post-design-approved Hook

```bash
hat-plugin-hook {task-folder} P2.post-design-approved
```

按输出指令执行（review plugin: 确认 Review Strategy 在 design.md 中已正确记录）。

### Step 8 — User Review 确认循环

1. Step 7 reviewer 收敛后（无 Critical/Important），展示**本轮 review 修改的变更差异**（仅本轮修改，非累积差异）
2. 纯文本询问用户是否有补充："以上是本轮 review 的修改内容，是否有补充？回复「继续」推进到 Plan 阶段。"
3. 用户说"继续" → 推进（须满足 DESIGN_PROTOCOL 顶部 HARD-GATE）
4. 用户给建议 → 澄清建议 → 修改 design.md → 判断是否重跑 Step 7：
   - 修改涉及架构决策、模块职责、接口定义 → 重跑 Step 7
   - 仅措辞/格式调整 → 可跳过 reviewer
   - 若重跑：展示新一轮差异 → 回到步骤 2
   - 若跳过：展示修改差异 → 回到步骤 2

**轮次计数**：跨确认循环累积不重置。若已达 max_rounds 则跳过 reviewer 直接进入确认。

**无 review 轮次时（Low 复杂度跳过 Step 7，仅 Interactive）**：直接询问："设计各节已确认，是否有补充？回复「继续」推进到 Plan 阶段。"

**变更差异显示规则**：每轮重置，只展示从上次确认点到现在的改动。

---

## phases.md Sync

每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

**Phase 2 完成时**：将 Phase 2 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

---

## Design 完成 → 过渡

Phase 2 完成，phases.md 已更新。

若 Activation Timing 选择了 "Design 阶段结束后启用"，在此过渡处确认 `unattended.json` 的 `activate_after: "design"` 已写入（实际翻 `enabled:true` 由编排器在过渡时执行）。

用用户配置的语言简要宣告设计结果（design.md 位置、复杂度评估），然后声明：**"Design 完成。"** 此处停止输出，返回编排器 Step 3 执行过渡逻辑。

如果独立调用（非编排器），提示用户："请调用 `/task` 继续。"

<rule>
phase skill 完成后将控制权交回 orchestrator Step 3。过渡路由归属 orchestrator；phase skill 若提示用户去调用另一个 skill，就绕过了 orchestrator 的过渡检查。
Reason: 阶段 skill 不知道完整的过渡逻辑（phase_merge、新会话交接、unattended 等），自行发出过渡指示会跳过这些检查。
</rule>

---

## Visual / Semantic Decisions — Use Previews

设计期遇到**视觉 / 语义选择**（图标 / emoji、命名格式与缩写、键位、文案、布局）时，在 Step 2 澄清里用 向用户提问（结构化选项优先） 的 `preview` 字段把候选**画出来**让用户一次性选定，并写进 design.md 的验收/决策。这类选择在设计期用 preview 一次性定下，归属设计期决策。

<rule>
视觉 / 语义选择（图标 / emoji、命名格式与缩写、keybindings、文案、布局）在 Step 2 澄清阶段经 向用户提问（结构化选项优先） preview 呈现并记入 design.md。一旦推迟到实现阶段，它们在纯文字往返中迭代代价高昂。
Reason: 视觉 / 语义决策在前期用并排 preview 能廉价收敛，但若拖到实现阶段在纯文字里反复迭代则代价高昂——已有真实案例：emoji / 缩写 / keybinding 的选择耗费约 25 轮 向用户提问（结构化选项优先），且大多发生在实现阶段内。在设计期用 preview 定下它们能大幅压缩这些往返。
</rule>

### 浏览器 Visual Companion（像素级 mockup）

向用户提问（结构化选项优先） preview 适合终端内的 ASCII / 语义选择；当问题需要**真实像素级渲染**（UI 线框图、布局对比、架构图）时 preview 表达不出，改用浏览器 visual companion——纯 node（零 npm）本地 server 把 HTML mockup 推到用户浏览器、用户点选、选择写回事件文件。

just-in-time 提供：第一次真正遇到「画出来比说出来清楚」的视觉问题时，单独发一条消息征询（不与澄清问题或其它内容捆绑），用户同意后再起 server；整个设计期没有视觉问题就不提。逐问决定通道——内容本身是视觉的（mockup / 线框 / 布局对比 / 架构图）走浏览器，内容是文字的（需求 / 概念选择 / 取舍清单 / 文字 A/B/C）走终端。仅 Interactive；无头 / 无人值守模式跳过（无浏览器）。

详细使用指南（起 server / 写 HTML 片段 / 读取选择 / session-key 安全）见 `visual-companion/visual-companion.md`，用户同意后再读。

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 1.5 | 本地探索完成后（仅 Interactive） | 是否联网调研补充外部信息？是 / 否 |
| 2 | 需要澄清问题 | 合并提问（最多 4 个）+ 末尾纯文本确认补充 |
| 3 | 提案完成后 | 用户选择方案 |
| 4 | 每节设计展示后 | 这部分看起来对吗？ |
| 2e | 复杂度与 preset 明显偏离时 | 配置面板修正 + activate_after 时机 |
| 2e.2b | 任务高敏感且当前 checkpoint 时 | 建议把 per_task_review 升级为 each（仅 Interactive） |
| 6.5 | 自我 review 完成后 | Review 轮数、code review 策略、reviewer 模型 |
| 8 | 所有 review 完成后（仅 Interactive） | 等待用户明确批准 design.md（HARD-GATE） |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Reads**: `{task-folder}/prompt.md`, `{task-folder}/task-config.json`（P1 已写入）, `{task-folder}/unattended.json`
- **Writes**: `{task-folder}/design.md`, `{task-folder}/task-config.json`, `{task-folder}/phases.md`, `{task-folder}/unattended.json`（activate_after 时）
- **Pre-injected**: `DESIGN_PROTOCOL.md`（设计流程单一来源）
- **On-demand read**（用户同意后，仅 Interactive）: `visual-companion/visual-companion.md` + `visual-companion/scripts/`（浏览器像素级视觉确认工具，源自 Superpowers brainstorming 6.0.3，脚本逐字保留便于安全更新）
- **Hooks**: `P2.post-design-draft`（review: self-review + independent review）, `P2.post-design-approved`（review: strategy write-back）（P2.phase-end 已无 hook——linear 描述更新并入 P3.phase-end，见 B1）
- **Scripts**: hat-plugin-hook
