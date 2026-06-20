---
name: spec-task-skill
user-invocable: false
description: "Use when creating, modifying, or reviewing task workflow skills (task-init, task-design, task-plan, task-execute, task-test, task-end, task-cancel, task-revise, task-reopen, and the task orchestrator). Extends spec-skill with task-specific conventions. Do NOT use for non-task skills. 触发词: \"task skill 规范\", \"检查 task skill\", \"task 技能合规\""
---

# Task Skill Specification Guide

Task workflow skill 的专用规范。继承 `spec-skill` 的所有通用规则，增加 task 系列特有的约定。

**Announce at start:** "Using spec-task-skill to [write/modify/review] the task skill."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Red Flags

| If you think... | Reality |
|---|---|
| "This phase skill can handle its own transition" | Phase skills MUST return to orchestrator Step 3. Transition routing is the orchestrator's job. |
| "The hook output is just one segment, no need to verify" | Hooks can output multiple segments. All must execute, and artifacts must be verified. |
| "Phase numbers are stable, I can hardcode P3→P4" | phase_merge changes numbering. Use semantic names (Init/Design/Plan/Execute/Test/End). |
| "Revise is a quick fix, skip user confirmation" | Revise without confirmation leads to band-aid fixes. Confirmation loop is mandatory. |

---

## Base Specification (spec-skill pre-loaded)

<SPEC_SKILL>
!`cat "${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md"`
</SPEC_SKILL>

## Dependencies

- **继承**: `spec-skill`（已预注入上方）
- **适用范围**: `skills/task*/SKILL.md`（各 phase skill，含生命周期辅助 skill task-reopen）+ `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md`（编排器）+ `bin/hat-task-artifact-check`（门控脚本）+ `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.md`（插件指令 + 顶部 frontmatter 声明）+ `agents/*.md`（task 工作流派发的 subagent，如 task-executor、各 reviewer）+ `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/*.md`（review 协议）+ 协议文件（`DESIGN_PROTOCOL.md` / `PLAN_PROMPT.md` / `UNATTENDED_PROTOCOL.md` / `IMPLEMENTER_PROMPT.md`）

---

## Core / Plugin Separation

Task 流程分两层，必须始终分离：

- **Core**：phase skill（task-init/design/plan/execute/test/end）+ 生命周期辅助 skill（task-cancel/task-revise/task-reopen）+ 编排器 `task/SKILL.md` + 门控脚本 `bin/hat-task-artifact-check`。core 只定义骨架——阶段顺序、状态机、何时触发产物门控。
- **Plugin**：`plugins/*.md`（指令正文 + 顶部 `---` frontmatter 声明 hook 路由）。某项能力的全部逻辑只住在它自己的 plugin 文件里。

两层只通过 hook 边界连接：core 在阶段边界调 `hat-plugin-hook {folder} {hook-point}`，逐段执行返回的指令；插件关闭（`task-config.json` 翻 `enabled:false`）时 hook 不返回它的指令段，该能力自然消失。目标——**任一插件都能靠翻 `enabled:false` 干净拔除，无需编辑任何 core 文件**（门控脚本也算 core：它不得为某个具体插件硬编码产物文件名）。

<HARD-GATE>
Plugin-specific logic MUST NOT be written into any core file (a phase SKILL.md, the orchestrator, or hat-task-artifact-check). A plugin's behavior lives only in its plugins/*.md (instruction body + leading frontmatter); core merely invokes the hook and executes whatever instructions come back.
Reason: when plugin logic leaks into core, flipping enabled:false no longer removes the logic — disabling the plugin then requires surgically editing core files, and the pluggable promise silently breaks. When a stateful plugin's artifacts span phases, its lifecycle logic tends to spread across multiple phase skills and the gate script, turning a one-flag removal into multi-file surgery.
</HARD-GATE>

### Cross-Phase State Litmus

判断一项能力能否做成干净插件，看它是否需要**跨阶段产物**（在一个阶段产出、在另一个阶段消费）：

| 能力类型 | 易插拔 | 原因 |
|---|---|---|
| 边界即用、无跨阶段状态（在某 hook 点完成动作即结束） | ✅ | hook 在该边界注入指令即完成，逻辑全留在 plugin .md |
| 跨阶段有状态产物（A 阶段产出、B 阶段消费） | ❌ | hook 是「边界注入指令」的无状态机制，承载不了产物的跨阶段生命周期，逻辑会被迫溢出到 core |

若一项能力需要跨阶段产物，要么**在它触及的每个阶段都开 hook、且全部逻辑留在 plugin .md**，要么承认它不适合做插件——绝不要把产物的跨阶段生命周期写进 phase skill。

---

## Task-Specific Conventions

### 1. Phase Transition Protocol

每个阶段 skill 都有一个 transition section（如"Execute 完成 → 过渡"）。此 section 必须遵守：

**必须包含：**
- 用用户配置的语言简要宣告阶段结果
- 声明"Phase N 完成。"
- 明确指令：**"此处停止输出，返回编排器 Step 3 执行过渡逻辑。"**
- `<rule>` 禁止在 transition 中提示用户调用任何 skill

**必须避免：**
- 提示用户调用 `/task-end`、`/task-test` 或其他 skill
- 自行判断下一阶段（过渡类型表由编排器维护）
- 给出 compact 建议（这是编排器 Step 3 的职责）

**唯一例外**：Test 阶段的 transition 是硬停，应该提示调用 `/task-end`。

<rule>
Phase skill transition sections MUST end with "返回编排器 Step 3" and MUST NOT suggest invoking any other skill. The orchestrator owns transition logic (artifact check, compact, unattended check).
Reason: phase skills lack knowledge of phase_merge, compact rules, and unattended state. Self-directing transitions bypasses these checks.
</rule>

### 2. Phase 语义命名

在所有文档中，优先使用 Phase 语义名称而非硬编码序号：

| 序号 | 语义名 | 用于描述过渡、触发条件等 |
|------|--------|----------------------|
| Phase 1 | Init | "Init 完成后" 而非 "P1→P2" |
| Phase 2 | Design | "Design 完成后" |
| Phase 3 | Plan | "Plan 完成后" |
| Phase 4 | Execute | "Execute 完成后" |
| Phase 5 | Test | "Test 完成后" |
| Phase 6 | End | — |

**何时可以用序号**：phases.md 中的步骤编号（`4a. 执行任务`）、Phase 路由表中的状态匹配——这些是结构化数据，不受 phase_merge 影响。

**何时必须用语义名**：过渡类型表、触发条件描述、compact/unattended 检查条件——这些描述逻辑关系，phase_merge 后序号会变化。

### 3. Hook Artifact Verification

当 skill 通过 `hat-plugin-hook` 委托工作时，hook 输出可能包含多段指令。必须：

1. **逐段全部执行** hook 输出的所有指令段
2. 在 hook 执行完毕后，**验证预期产物是否存在**
3. 产物缺失时执行 **fallback**（如主 agent 自行生成）而非跳过

这一规则尤其重要的场景：插件化重构后，原本硬编码在 SKILL.md 中的 `<rule>` 和 fallback 逻辑被移到了 hook 输出中。hook 输出是文本指令而非强制约束——agent 可能在执行完第一段后就认为步骤完成，跳过后续段。

**Checklist**（hook 调用处）：
- [ ] hook 输出有多段？是否标注了"必须逐段全部执行"？
- [ ] 哪些产物是预期输出？是否有验证 checkpoint？
- [ ] 产物缺失时的 fallback 是什么？是否有 `<rule>` 保护？

### 4. Revise Cycle Confirmation

Revise 流程（task-revise）中的 RN-design 和 RN-plan 步骤必须包含确认循环（参照 spec-skill 的 Confirmation Loop pattern）：

- RN-design：展示修订方案 → 纯文本确认 → 用户同意后写入 design.md
- RN-plan：展示任务列表 → 纯文本确认 → 用户同意后标记完成

没有确认循环的 Revise 容易产生治标不治本的修复。

### 5. Interactive / Unattended Duality

Task skill 在两种模式下执行：**Interactive**（用户在场）和 **Unattended**（无人值守，无人应答）。**任何新增或修改的步骤都必须同时设计这两条路径**——尤其是带停顿的地方（AskUserQuestion、纯文本确认循环、等待用户测试/回复、需人工的硬阻断）。每个停顿点用 `**[Unattended]**` 标注无人值守下如何**不靠人工就推进**。

| 停顿元素 | Interactive | Unattended |
|---|---|---|
| AskUserQuestion 决策点 | 正常询问 | 按默认/协议选项自动决定，不询问 |
| 纯文本确认循环 | 等用户回复 | 跳过等待，直接推进 |
| 等待用户测试/填写 | 停下等待 | 按 `task_type` 自测继续，或 Telegram 通知后按约定停/继续 |
| 需人工的硬阻断（如验证失败） | 报错停下 | 重试 → 仍失败则 Telegram 通知 + auto-cancel |

无人值守的具体默认值见 `UNATTENDED_PROTOCOL.md`。

<rule>
Every stop point or user-decision branch added to a task skill MUST carry an explicit [Unattended] path that resolves without human input. Never leave a pause that only an interactive user can clear.
Reason: an unattended run has no one to answer — a single unguarded AskUserQuestion or "wait for user reply" stalls the whole automated flow indefinitely. The pause must auto-resolve (default option, protocol decision, or notify-then-cancel), not block.
</rule>

### 6. Protocol File as Single Source

当 phase skill 用 `!`cat`` 预注入某协议文件（如 `DESIGN_PROTOCOL.md`、`PLAN_PROMPT.md`），该文件是对应内容的**单一来源**。SKILL.md 中**不得重述**该协议的流程步骤、提问节奏、模板或矩阵——SKILL.md 只承载编排层内容：announce / runtime 入口 / hook 调用时机 / TODO sync / resume 逻辑 / transition section / mandatory stop points。

理由（本架构的 dogfooding 教训）：Block 4 中 `DESIGN_PROTOCOL.md` 与 `task-design/SKILL.md` 长期双写同一设计流程，运行时两份内容同时被加载，导致：① 提问节奏出现两个版本（"One question at a time" vs "合并提问"）；② 复杂度矩阵出现两个版本——任一版本的修改都不会同步到另一处，增加维护成本，并在 Design / Plan 阶段放大认知负担。

<rule>
When a phase SKILL.md pre-injects a protocol file via `!`cat``, the SKILL.md MUST NOT restate the protocol's process steps, question cadence, templates, or decision matrices. Those live only in the protocol file; the SKILL.md carries only orchestration-layer content (announce, hook invocations, transition, stop points).
Reason: dual-writing the same content produces two diverging versions that both load at runtime. Any edit to one is silently missed by the other, creating contradictory instructions. The protocol file is the single source of truth for its domain; the phase skill is the single source of truth for orchestration.
</rule>

### 7. 剥离 / 删除类任务的验收 grep 范围

当任务目标是"删净某机制的所有痕迹"并以 grep 残留扫描作验收时，grep 的范围与模式必须排除两类合法命中，否则验收项会与 Out-of-Scope 自相矛盾、永远 FAIL：

1. **刻意保留的产物**：明确保留到后续 block / 历史说明 / changelog 的消费侧产物或历史记录，须排除出 grep 范围（或限定到非保留区域）。
2. **会误伤合法标识符的子串模式**：宽松的关键词（无词边界）会命中合法的文件名 / 标识符（例如关键词 `fact-check` 命中脚本名 `artifact-check`）。须加词边界，或用 `| grep -v <排除模式>` 过滤这些合法子串命中。

**过滤的反向副作用**：`| grep -v <排除>` 是**行级**过滤——若一行同时含合法子串与真实残留，整行被丢弃，真残留被掩盖。故凡用 `grep -v` 收窄验收，须辅以对**被过滤掉的行**人工 / reviewer 抽查，或改用词边界精确模式（给关键词加 `\b` 词边界，只匹配独立词、不匹配作为子串嵌入合法标识符的情形）只排子串误命中而不吞同行真残留。

<rule>
A removal/strip task that uses a residual-grep as an acceptance gate MUST scope the grep to exclude (a) artifacts deliberately kept (later-block consumers, history, changelog) and (b) substring false-positives where a loose keyword matches a legitimate identifier. Otherwise the "zero residual" acceptance contradicts the Out-of-Scope set and can never pass.
Reason: dogfooding found a strip task whose acceptance grep matched the very script names it was meant to keep — the gate was logically unsatisfiable. Define the grep's exclusions as part of the acceptance criterion, not as an afterthought.
</rule>

### 8. Hook Manifest Closure

插件通过 frontmatter 声明的 hook section 与 plugin `.md` body 中的 section 标题必须**双向闭合**，否则会出现「声明了但 .md 无此段」或「.md 写了 handler 段但从未被声明、永不 emit」的静默失效。

- **① 正向闭合**：每个 frontmatter hook 的 `section` 字段值，必须在对应 `.md` body 中存在为一个 `## ` 标题。
- **② 反向闭合**：每个 `.md` body 中作为 hook handler 的 `## ` section 标题，必须被某 frontmatter hook 的 `section` 字段引用。
- **③ 闭合判据是 section 字符串的集合包含，不是「hook 点名 == section 名」**：frontmatter hook 的 `section` 是任意字符串，允许**一段多 hook 复用**——多个 hook 点可声明同一 `section`（一个 `.md` 段被多个 phase 边界共享）。判据为「frontmatter 全部 `section` 值 ⊆ `.md` 的 `## ` 标题集」**且**「`.md` 的 hook handler `## ` 标题 ⊆ frontmatter 全部 `section` 值」。**不得**用「hook 点名等于 section 名」做判据——否则会把合法的泛化复用段误判为未声明，爆假阳性。
- **④ 段落提取机制（决定哪些标题算 section、正文到哪截断）**：`hat-plugin-hook` 按「`## ` 标题 → 下一个 `^## `」提取段落正文。仅行首恰好「`## ` + 空格」触发截断；段内 `### ` / `#### ` 子标题**不**截断；代码块内（``` fence 之间）的 `## ` 被 fence-aware 忽略、不算 section。（运行时后果——未被任何 frontmatter 声明的 `## ` section 永不被 emit——见下方 `<rule>` Reason。）
- **⑤ 校验配方**：对每个 plugin 跑双向 grep——正向遍历 frontmatter 每个 `section` 在 `.md` body 查找标题；反向列 `.md` body 的非代码块 `## ` 标题与 frontmatter `section` 值集求差，差集为空即闭合。

<rule>
Every frontmatter `section` string MUST exist as a `## ` heading in the plugin .md body, and every hook-handler `## ` heading in the .md body MUST be referenced by some frontmatter `section`. Verify by set-inclusion of section strings in both directions — never by assuming the hook-point name equals the section name.
Reason: an undeclared handler section is silently never emitted (the exact failure where a quality gate's body was written but never reached the agent), and a declared-but-missing section errors at hook time. Section strings are arbitrary and may be reused across hook points, so a name-equality check produces false positives that mask the real closure state.
</rule>

**与约定 3「Hook Artifact Verification」的边界**：约定 3 管运行时——hook 输出后验证**预期产物**是否生成；本约定管静态结构——frontmatter ↔ .md body 的 **section 声明**是否闭合。两者单一职责，不合并。

### 9. Interaction Front-Loading（交互前置）

用户交互必须前置到流程早期，使用户「写完 Design/Plan 即可离开、放心等待执行自动跑完」。这是修改 task 系列 skill 时的硬约束。

**分阶段约束：**

| 阶段 | 交互约束 |
|---|---|
| Init (P1) / Design (P2) | **收集一切需用户决策的事项**（提交节奏、验证命令、分支策略、无人值守时机、scope 等）。交互集中在此。 |
| Plan (P3) | **尽量少交互**——只保留 plan review 收敛的轻量确认。新增交互前先问：能否前置到 Design？ |
| Execute (P4) | **任何模式（含 Interactive）零阻塞交互**。不得新增 AskUserQuestion / 等用户应答的停顿。P4 真卡死时，终态是「在 session 内可见地停下并输出清晰报告」（用户回来即见），Telegram 通知为 best-effort **叠加**而非替代——**绝不**改成无投递路径的「静默暂停」。 |
| Test (P5) / End (P6) | **豁免**。用户测试、End 决策（分支处理、CLAUDE.md、debt 对账确认）是自然决策点，受约定 4（Revise Confirmation）/ 约定 5（Interactive/Unattended Duality）管辖，不在本约定的「零交互」范围内。 |

**边界澄清：**
- 本约定的「零交互」只约束到 **Execute(P4) 末**。P5/P6 的既有交互合法。
- 独立 on-demand skill（如 `/dogfooding`、各 spec-* skill）**不属于 task Execute 流程**，其交互不受本约定约束。
- 因 P4 行为在两模式下一致（零阻塞），**Interactive 与 Unattended 的差异落在 P1-P3（交互收集）与 P5-P6（测试/End 决策）**，而非 Execute。

**Rationalization 自检**（命中任意一条即停下，把交互前置）：

| Rationalization | Reality |
|---|---|
| "这个确认放 Execute 里问一下没关系" | P4 零阻塞交互是硬约束。把决策前置到 Design/Plan 一次性收集。 |
| "Interactive 模式本来就允许运行中交互" | front-loading 让 Interactive 的 P4 也零交互——用户写完 Plan 就能离开，不该被 Execute 拦住。 |
| "卡死了就弹个菜单让用户选" | P4 卡死应「可见停下 + 报告」，不是阻塞菜单（用户可能已离开）。 |
| "Plan 阶段加个询问更稳妥" | 先问能否前置到 Design。Plan 交互要尽量少。 |

<rule>
Any interaction (AskUserQuestion, plain-text confirmation, wait-for-user) added to the task workflow MUST be placed in Init/Design; Plan keeps interaction minimal; Execute(P4) has ZERO blocking interaction in all modes (including Interactive). A P4 dead-end resolves as a visible in-session stop + report (Telegram best-effort additive), never a silent pause or a blocking menu. P5/P6 decision points and standalone on-demand skills are exempt.
Reason: the user's stated workflow is "finish Design/Plan, then leave and let Execute run to completion." A single blocking interaction in Execute breaks that — in Interactive mode it stalls until the (absent) user returns; routing it to a Telegram-only "pause" is worse, since an Interactive user may have no Telegram path and the run dies silently. Front-loading every decision to Init/Design is the only way to honor "leave after Plan."
</rule>

---

### 10. 任务文档路径引用约束

任务文档内引用**当前任务**的其他文件时，必须使用 `任务文档/<relative_path>` 占位符。

- **禁止写入绝对路径**（worktree 路径、`.tasks/open/` 路径等），即使当下路径有效
- **例外**：`docs/` 目录下的文档遵循原有路径写法（相对路径或直接文件名），不受占位符约束
- 完整规范见 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/path-placeholder.md`

**Checklist**（任务文档编写处）：
- [ ] 自引用路径已使用 `任务文档/X` 形式，无绝对路径？
- [ ] 是否 `docs/` 目录下文档（豁免）？

---

## Compliance Checklist

在 spec-skill 的通用 Checklist 基础上，task skill 额外检查：

- [ ] 改动未把任何插件专有逻辑写入 core 文件（phase skill / 编排器 / hat-task-artifact-check）？
- [ ] 跨阶段产物的插件逻辑全部留在 plugin .md，未溢出到 phase skill？
- [ ] artifact-check 未新增硬编码的插件产物文件名（应由 frontmatter 声明）？
- [ ] Hook Manifest Closure 正向：每个 frontmatter 声明的 `section` 在对应 plugin `.md` body 存在为 `## ` 标题？
- [ ] Hook Manifest Closure 反向：每个 plugin `.md` body 的 hook handler `## ` section 都被某 frontmatter `section` 字段引用（按集合包含判据，容忍一段多 hook 复用）？
- [ ] Transition section 包含"返回编排器 Step 3"指令？
- [ ] Transition section 有 `<rule>` 禁止提示调用其他 skill？
- [ ] 过渡描述使用语义名称（Init/Design/Plan...）而非硬编码序号？
- [ ] Hook 调用处有产物验证 checkpoint？
- [ ] Hook 多段输出标注了"必须逐段全部执行"？
- [ ] Revise 相关步骤有确认循环？
- [ ] 新增/修改的每个停顿点都有 `[Unattended]` 分支（不会阻塞无人值守）？
- [ ] 若 SKILL.md 预注入了 PROTOCOL 文件，SKILL.md 中没有重述 PROTOCOL 的流程/模板/矩阵内容？
- [ ] **Interaction Front-Loading（约定 9）**：新增交互是否前置到 Init/Design？Plan 交互是否最小化？Execute(P4) 是否零阻塞交互（含 Interactive）、卡死为「可见停下+报告」而非静默暂停/阻塞菜单？P5/P6 与独立 skill 豁免是否未被误伤？
- [ ] Dependencies 中列出了所有 Writes？
