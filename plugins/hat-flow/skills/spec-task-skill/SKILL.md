---
name: spec-task-skill
user-invocable: false
description: "Use when creating, modifying, or reviewing task workflow skills (task-init, task-design, task-plan, task-execute, task-test, task-end, task-cancel, task-revise, task-reopen, and the task orchestrator). Extends spec-skill with task-specific conventions. Do NOT use for non-task skills. 触发词: \"task skill 规范\", \"检查 task skill\", \"task 技能合规\""
word-budget: 2000
---

# Task Skill Specification Guide

Task workflow skill 的专用规范。继承 `spec-skill` 的所有通用规则，增加 task 系列特有的约定。

**Announce at start:** "Using spec-task-skill to [write/modify/review] the task skill."

## Base Specification (spec-skill pre-loaded)

<SPEC_SKILL>
!`cat "${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md"`
</SPEC_SKILL>

## Dependencies

- **继承**: `spec-skill`（已预注入上方）
- **适用范围**: `skills/task*/SKILL.md`（各 phase skill，含生命周期辅助 skill task-reopen）+ `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md`（编排器）+ `bin/hat-task-artifact-check`（门控脚本）+ `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.md`（插件指令 + 顶部 frontmatter 声明）+ `agents/*.md`（task 工作流派发的 subagent，如 task-executor、各 reviewer）+ `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/*.md`（review 协议）+ 协议文件（`DESIGN_PROTOCOL.md` / `PLAN_PROMPT.md` / `UNATTENDED_PROTOCOL.md` / `IMPLEMENTER_PROMPT.md`）
- **消费方**：`skill-create`（Phase 1/2 之间）与 `skill-revise`（Phase 0）在目标 skill 名匹配 `task*` 或其 Dependencies 声明 `Invokes: task-*` 时，条件 `!`cat`` 本文件（本文件不复述 spec-skill 规则，只补 task 系列的增量约定）。新增第三个消费方时，同样在该消费方的对应阶段加条件注入分支，不要求本文件反向感知消费方数量。

---

## Core / Plugin Separation

Task 流程分两层，必须始终分离：

- **Core**：phase skill（task-init/design/plan/execute/test/end）+ 生命周期辅助 skill（task-cancel/task-revise/task-reopen）+ 编排器 `task/SKILL.md` + 门控脚本 `bin/hat-task-artifact-check`。core 只定义骨架——阶段顺序、状态机、何时触发产物门控。
- **Plugin**：`plugins/*.md`（指令正文 + 顶部 `---` frontmatter 声明 hook 路由）。某项能力的全部逻辑只住在它自己的 plugin 文件里。

两层只通过 hook 边界连接：core 在阶段边界调 `hat-plugin-hook {folder} {hook-point}`，逐段执行返回的指令；插件关闭（`task-config.json` 翻 `enabled:false`）时 hook 不返回它的指令段，该能力自然消失。目标——**任一插件都能靠翻 `enabled:false` 干净拔除，无需编辑任何 core 文件**（门控脚本也算 core：它不得为某个具体插件硬编码产物文件名）。

<HARD-GATE>
任何 core 文件（phase SKILL.md、编排器、hat-task-artifact-check）中出现插件专有逻辑，均 out of scope。插件的行为只住在它自己的 plugins/*.md（指令正文 + 顶部 frontmatter）；core 仅调用 hook 并执行返回的指令。
Reason: 插件逻辑一旦泄漏进 core，翻 enabled:false 就不再能移除这段逻辑——关闭插件随之需要外科手术式地编辑 core 文件，可插拔的承诺静默破裂。当一个有状态插件的产物跨阶段时，它的生命周期逻辑往往散布到多个 phase skill 与门控脚本，把「翻一个 flag 即移除」变成多文件手术。
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

每个阶段 skill 都有一个 transition section（如"Execute 完成 → 过渡"）。此 section 的构成：

**包含项：**
- 用用户配置的语言简要宣告阶段结果
- 声明"Phase N 完成。"
- 明确指令：**"此处停止输出，返回编排器 Step 3 执行过渡逻辑。"**
- 一条 `<rule>` 把「transition 中提示用户调用任何 skill」划为 out of scope

**排除项（这些职责归编排器，transition 不承载）：**
- 提示用户调用 `/task-end`、`/task-test` 或其他 skill
- 自行判断下一阶段（过渡类型表由编排器维护）
- 新会话交接建议（属编排器 Step 3 的职责）

**唯一例外**：Test 阶段的 transition 是硬停，此处提示调用 `/task-end`。

<rule>
phase skill 的 transition section 以「返回编排器 Step 3」结束，不提示调用任何其他 skill。过渡逻辑（artifact check、新会话交接、unattended check）归编排器所有。
Reason: phase skill 不掌握 phase_merge、交接规则与 unattended 状态。自作主张的过渡会绕过这些检查。
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

**何时必须用语义名**：过渡类型表、触发条件描述、交接/unattended 检查条件——这些描述逻辑关系，phase_merge 后序号会变化。

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
task skill 中新增的每个停顿点或用户决策分支，都带一条无需人工即可解决的显式 [Unattended] 路径。只有交互式用户才能清除的停顿，out of scope。
Reason: 无人值守的运行没有人来应答——单个未设防的 AskUserQuestion 或「等用户回复」会让整条自动化流程无限期卡死。该停顿靠自身自动解决（默认选项、协议决策，或 notify-then-cancel），而非阻塞。
</rule>

### 6. Protocol File as Single Source

当 phase skill 用 `!`cat`` 预注入某协议文件（如 `DESIGN_PROTOCOL.md`、`PLAN_PROMPT.md`），该文件是对应内容的**单一来源**。SKILL.md 中**不得重述**该协议的流程步骤、提问节奏、模板或矩阵——SKILL.md 只承载编排层内容：announce / runtime 入口 / hook 调用时机 / TODO sync / resume 逻辑 / transition section / mandatory stop points。

理由（本架构的 dogfooding 教训）：Block 4 中 `DESIGN_PROTOCOL.md` 与 `task-design/SKILL.md` 长期双写同一设计流程，运行时两份内容同时被加载，导致：① 提问节奏出现两个版本（"One question at a time" vs "合并提问"）；② 复杂度矩阵出现两个版本——任一版本的修改都不会同步到另一处，增加维护成本，并在 Design / Plan 阶段放大认知负担。

<rule>
当 phase SKILL.md 经 `!`cat`` 预注入某协议文件时，该协议的流程步骤、提问节奏、模板与决策矩阵只留在那个协议文件里；在 SKILL.md 中重述它们 out of scope。SKILL.md 只承载编排层内容（announce、hook 调用、transition、停止点）。
Reason: 双写同一内容会产生两份逐渐分叉的版本、且运行时都被加载。对其中一份的任何修改都会被另一份静默遗漏，从而产生互相矛盾的指令。协议文件是其领域的单一来源；phase skill 是编排的单一来源。
</rule>

**薄引用纪律**：把某 section 收敛为对权威文件的薄引用时，section 只列**触发点名 + 指回权威**，不复述 per-tier / 档位的具体动作——复述会与权威表二次漂移，且容易把分属不同触发点的动作捆进一句（实证：todo-sync 收敛时 worker section 复述「overview 仅更新概览符号」，与触发表的触发点归属冲突，到全量 review 才捕出）。

### 7. 剥离 / 删除类任务的验收 grep 范围

当任务目标是"删净某机制的所有痕迹"并以 grep 残留扫描作验收时，grep 的范围与模式必须排除两类合法命中，否则验收项会与 Out-of-Scope 自相矛盾、永远 FAIL：

1. **刻意保留的产物**：明确保留到后续 block / 历史说明 / changelog 的消费侧产物或历史记录，须排除出 grep 范围（或限定到非保留区域）。
2. **会误伤合法标识符的子串模式**：宽松的关键词（无词边界）会命中合法的文件名 / 标识符（例如关键词 `fact-check` 命中脚本名 `artifact-check`）。须加词边界，或用 `| grep -v <排除模式>` 过滤这些合法子串命中。

**过滤的反向副作用**：`| grep -v <排除>` 是**行级**过滤——若一行同时含合法子串与真实残留，整行被丢弃，真残留被掩盖。故凡用 `grep -v` 收窄验收，须辅以对**被过滤掉的行**人工 / reviewer 抽查，或改用词边界精确模式（给关键词加 `\b` 词边界，只匹配独立词、不匹配作为子串嵌入合法标识符的情形）只排子串误命中而不吞同行真残留。

<rule>
以 residual-grep 作验收门控的删除/剥离类任务，其 grep 范围排除两类合法命中：(a) 刻意保留的产物（后续 block 的消费侧、历史记录、changelog），以及 (b) 宽松关键词命中合法标识符的子串误报。否则「零残留」验收会与 Out-of-Scope 集合自相矛盾、永远无法通过。
Reason: dogfooding 发现过一个剥离任务，其验收 grep 命中了它本应保留的脚本名——该门控在逻辑上不可满足。grep 的排除项属于验收标准本身，而非事后补救。
</rule>

### 8. Hook Manifest Closure

插件通过 frontmatter 声明的 hook section 与 plugin `.md` body 中的 section 标题必须**双向闭合**，否则会出现「声明了但 .md 无此段」或「.md 写了 handler 段但从未被声明、永不 emit」的静默失效。

- **① 正向闭合**：每个 frontmatter hook 的 `section` 字段值，必须在对应 `.md` body 中存在为一个 `## ` 标题。
- **② 反向闭合**：每个 `.md` body 中作为 hook handler 的 `## ` section 标题，必须被某 frontmatter hook 的 `section` 字段引用。
- **③ 闭合判据是 section 字符串的集合包含，不是「hook 点名 == section 名」**：frontmatter hook 的 `section` 是任意字符串，允许**一段多 hook 复用**——多个 hook 点可声明同一 `section`（一个 `.md` 段被多个 phase 边界共享）。判据为「frontmatter 全部 `section` 值 ⊆ `.md` 的 `## ` 标题集」**且**「`.md` 的 hook handler `## ` 标题 ⊆ frontmatter 全部 `section` 值」。**不得**用「hook 点名等于 section 名」做判据——否则会把合法的泛化复用段误判为未声明，爆假阳性。
- **④ 段落提取机制（决定哪些标题算 section、正文到哪截断）**：`hat-plugin-hook` 按「`## ` 标题 → 下一个 `^## `」提取段落正文。仅行首恰好「`## ` + 空格」触发截断；段内 `### ` / `#### ` 子标题**不**截断；代码块内（``` fence 之间）的 `## ` 被 fence-aware 忽略、不算 section。（运行时后果——未被任何 frontmatter 声明的 `## ` section 永不被 emit——见下方 `<rule>` Reason。）
- **⑤ 校验配方**：对每个 plugin 跑双向 grep——正向遍历 frontmatter 每个 `section` 在 `.md` body 查找标题；反向列 `.md` body 的非代码块 `## ` 标题与 frontmatter `section` 值集求差，差集为空即闭合。

<rule>
当每个 frontmatter `section` 字符串都在 plugin .md body 中存在为一个 `## ` 标题、且 .md body 中每个 hook-handler `## ` 标题都被某 frontmatter `section` 引用时，闭合成立。校验是 section 字符串在两个方向上的集合包含；名称相等判据（hook 点名 == section 名）不可靠。
Reason: 未声明的 handler section 会被静默地永不 emit（正是「某质量门控的正文写了却从未到达 agent」那种失败），而声明了却缺失的 section 会在 hook 时报错。section 字符串是任意的、可跨 hook 点复用，因此名称相等判据会产生掩盖真实闭合状态的假阳性。
</rule>

**与约定 3「Hook Artifact Verification」的边界**：约定 3 管运行时——hook 输出后验证**预期产物**是否生成；本约定管静态结构——frontmatter ↔ .md body 的 **section 声明**是否闭合。两者单一职责，不合并。

### 9. Interaction Front-Loading（交互前置）

用户交互必须前置到流程早期，使用户「写完 Design/Plan 即可离开、放心等待执行自动跑完」。这是修改 task 系列 skill 时的硬约束。

**分阶段约束：**

| 阶段 | 交互约束 |
|---|---|
| Init (P1) / Design (P2) | **收集一切需用户决策的事项**（提交节奏、验证命令、分支策略、无人值守时机、scope 等）。交互集中在此。 |
| Plan (P3) | **尽量少交互**——只保留 plan review 收敛的轻量确认。新增交互前先问：能否前置到 Design？ |
| Execute (P4) | **任何模式（含 Interactive）零阻塞交互**——不新增 AskUserQuestion / 等用户应答的停顿。P4 真卡死时，终态是「在 session 内可见地停下并输出清晰报告」（用户回来即见）；Telegram 通知为 best-effort **叠加**而非替代，无投递路径的「静默暂停」不在此终态之列。 |
| Test (P5) / End (P6) | **豁免**。用户测试、End 决策（分支处理、CLAUDE.md、debt 对账确认）是自然决策点，受约定 4（Revise Confirmation）/ 约定 5（Interactive/Unattended Duality）管辖，不在本约定的「零交互」范围内。 |

**边界澄清：**
- 本约定的「零交互」只约束到 **Execute(P4) 末**。P5/P6 的既有交互合法。
- 独立 on-demand skill（如 `/dogfooding`、各 spec-* skill）**不属于 task Execute 流程**，其交互不受本约定约束。
- 因 P4 行为在两模式下一致（零阻塞），**Interactive 与 Unattended 的差异落在 P1-P3（交互收集）与 P5-P6（测试/End 决策）**，而非 Execute。
- **对外不可逆动作的「就绪后确认」（发布 / push / 删除）天然无法前置**——它必须等产物全绿才有意义，无法在 Design 预先拍板。这类确认**不放进 P4**，而是建模为 **P6 End 决策**（P6 豁免本约定）由 End 阶段做门控；若任务在 P4 就撞上它，说明该动作本应是一条独立的收尾步骤，而非 Execute 的一环。

**Patterns（正确默认 · 出现以下念头时按此校正）：**

- 确认事项一律前置到 Design/Plan 一次性收集；"放 Execute 里问一下"不在 P4 的零阻塞约束之内。
- front-loading 让 Interactive 的 P4 也零交互——用户写完 Plan 即可离开，不被 Execute 拦住（Interactive 允许运行中交互不构成在 P4 加交互的理由）。
- P4 卡死的终态是「可见停下 + 报告」，而非阻塞菜单（用户可能已离开）。
- Plan 新增交互前先问能否前置到 Design；Plan 交互保持最小。
- 发布/push/删除需等编译/测试全绿才有意义——这正说明它属 P6 而非 P4，建模为 End 决策（P6 豁免），不塞进 Execute 的零阻塞区。

<rule>
task 工作流中新增的任何交互（AskUserQuestion、纯文本确认、wait-for-user）都属于 Init/Design；Plan 保持交互最小化；Execute(P4) 在所有模式（含 Interactive）下零阻塞交互。P4 的死路终态是在 session 内可见地停下 + 输出报告（Telegram 为 best-effort 叠加）；静默暂停或阻塞菜单 out of scope。P5/P6 决策点与独立 on-demand skill 豁免。
Reason: 用户声明的工作流是「写完 Design/Plan，然后离开、让 Execute 自动跑完」。Execute 中单个阻塞交互即破坏它——在 Interactive 模式下它会卡到（不在场的）用户回来；把它导向仅 Telegram 的「暂停」更糟，因为 Interactive 用户可能没有 Telegram 路径、运行会静默死掉。把每个决策前置到 Init/Design，是兑现「写完 Plan 即可离开」的唯一办法。
</rule>

---

### 10. 任务文档路径引用约束

任务文档内引用**当前任务**的其他文件时，采用 `任务文档/<relative_path>` 占位符。

- **绝对路径**（worktree 路径、`.tasks/open/` 路径等）out of scope，即使当下路径有效
- **例外**：`docs/` 目录下的文档沿用原有路径写法（相对路径或直接文件名），不受占位符约束
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
- [ ] **Interaction Front-Loading（约定 9）**：新增交互是否前置到 Init/Design？Plan 交互是否最小化？Execute(P4) 是否零阻塞交互（含 Interactive）、卡死为「可见停下+报告」而非静默暂停/阻塞菜单？对外不可逆动作（发布/push/删除）的就绪后确认是否建模为 P6 End 决策、而非塞进 P4？P5/P6 与独立 skill 豁免是否未被误伤？
- [ ] Dependencies 中列出了所有 Writes？
