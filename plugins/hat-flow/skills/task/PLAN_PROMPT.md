# Plan-Writing Template

本文件是 plan 编写的 prompt 模板，也是 plan 模板（Plan Format / File Structure 职责图 / Dependency 并行切割 / Bite-Sized / TDD / Verification / Commit Checkpoint / Forbidden Patterns / Self-Review）的**单一来源**。task-plan/SKILL.md 通过 `!cat` 嵌入本文件，不重述其内容；`reviewer/PLAN_REVIEW.md` 引用本文件的 Forbidden Patterns 清单。主 session 读取此文件并附带注入上下文一起编写 plan.md。

---

## Mindset: 为零上下文工程师写 plan

写 plan 时**假设执行工程师对本代码库零上下文、品味存疑**——他不知道现有约定，也不会替你补全省略的判断。因此每个 task 必须明确记录：改哪些文件、写哪些代码 / 测试、怎么验证。宁可显式到啰嗦，不要留模糊空间。

贯穿全程的原则：

- **DRY**：不重复造轮子，复用已有模块。
- **YAGNI**：只规划 design.md 要求的功能，不预加未来可能用到的能力。
- **TDD**：每个实现步骤都有先于实现的可验证预期（见下方 TDD Requirements）。
- **频繁提交**：按语义相关性分批落盘（见下方 Commit Checkpoint Guidance），不积压大 diff。

---

## Required Inputs (main session must provide the following)

主 session 必须在此 prompt 之后附加以下内容：

1. **Full design.md** — 完整的需求描述
2. **Project file structure** — `find src/ -type f | head -50` 或等效输出
3. **Git conventions** — 来自 `hat-git-conventions` 输出或 CLAUDE.md
4. **Complexity Tier** — Low / Medium / High（由主 session 确定）
5. **Verification Commands** — 来自 CLAUDE.md `## 验证命令` 的 Light 和 Full 命令
6. **Commit Guidelines summary** — git plugin 启用时由 `P3.phase-end` hook 注入；未启用时跳过

---

## File Structure 职责图（先于 tasks 列表）

定义具体 task 之前，**先列出本 plan 将创建 / 修改的全部文件及各自职责**，放在 tasks 列表之前。这张职责图迫使你在拆 task 前想清楚结构，也让执行工程师一眼看到全貌。

格式：

```markdown
## File Structure
- `path/to/fileA` — Create — 职责一句话（它对外提供什么）
- `path/to/fileB` — Modify — 改动职责
- `path/to/fileA.test` — Create — 测试 fileA 的哪些行为
```

设计这张图时遵循：

- **单一职责**：每个文件只承担一个明确职责；文件过大 = 职责过多，应拆分。
- **接口清晰**：消费者不读内部实现即可理解该文件的用途。
- **同变更同文件**：会一起变更的代码放同一文件，分散变更的代码拆开。
- **按职责拆分，而非按技术层**：按"独立问题域"组织文件（如"用户认证""支付结算"），而非按"全部 controller / 全部 model"的技术分层堆放。
- **列出相邻契约文件（防并行盲区）**：除本 plan 直接改动的文件外，还须列出"契约另一端"——即**引用了改动文件、或被改动文件引用的相邻文件**（如：改 A 的输出格式，则消费 A 输出的 B 也要列；删 A 的某节，则按节名引用 A 的 C 也要列），即使本 plan 不直接改它，也标注为"契约另一端（需核实 / 同步）"。否则并行切割（parallel-agents）时契约一端会无人认领、留下悬空引用，只能靠全量 review 兜底（Block 4 实证：reviewer 协议改了 Output Format，引用它的 plan-reviewer 文件因未列而遗漏）。

---

## Plan Format (plan.md output structure)

```markdown
# [Feature] Implementation Plan

**Design**: design.md
**Complexity**: [Low/Medium/High]
**Tasks**: [count]

## Verification Commands
- Light: [command from CLAUDE.md]
- Full: [command from CLAUDE.md]

## File Structure
（见上方 File Structure 职责图，列出全部 Create/Modify 文件及职责）

## Task N: [Title]

**Difficulty**: easy/medium/hard（仅 mode=subagent 时使用）
**Depends**: []（列出前置 task 编号；空列表表示无前置依赖，可立即并行派发）
**Files**: Create/Modify/Test with exact paths

### Steps
- [ ] Step description (specific action, 2-5 min)
- [ ] Step description
...

### Implementation Guardrails
**Allow variations**: {允许的实现变体，自由文字}
**Anti-patterns**: {应排除的实现方式，自由文字}

### Verification
- [verification check]

### ✔ Commit Checkpoint M
`<type>(<scope>): <subject>`
（在一组语义相关 task 完成后落地一次 commit；见下方 Commit Checkpoint Guidance）
```

---

## Dependency Annotation 与并行切割

每个 task 标注 `Depends: [...]`，列出它依赖的前序 task 编号。整张依赖关系必须是 **DAG（拓扑有序、无环）**。

**为什么标 Depends**：task-execute 消费 `Depends` 字段做并行派发决策——`Depends` 字段 schema（连同 `Difficulty`）已被 task-execute 消费，不可删改。

**怎么切割并行批次**：按"独立问题域"分组（参考 hatflow-dispatching-parallel-agents 的"一域一 agent"原则——每个 agent 负责一个无共享状态、不改同一文件的独立子问题）。判断两个 task 能否并行，对齐 task-execute 的 `layer_is_isolatable` 判据：

> 一组 task 可并行派发 ⟺ 各自的 `Depends` 都已全部完成（无未满足的跨层依赖）**且** 改动文件集互不重叠（写同一文件的 task 不并行，避免写冲突）。

因此拆 task 时刻意让**同批 task 改动不同文件**，能显著提升并行度。两个 task 若必须改同一文件，应合并或串行（标注 `Depends`）。

---

## Bite-Sized Task Guidance

- 每步是**一个动作**，预计 2-5 分钟
- TDD 步骤格式见下方 TDD Requirements section
- Must use **exact file paths** — never write "relevant files" or similar vague references
- 尽可能提供**确切的命令和预期输出**
- No placeholder steps (e.g., "handle later")

---

## TDD Requirements

> 仅当 `task-config.json` 的 `plugins.tdd.mode` 不为 `none` 时适用。`mode: none` 时跳过本节所有 TDD 格式要求，步骤无需 RED/GREEN 标记。

每个 step 必须包含验证循环（Full TDD 或 Lite TDD，由主 session 指定）：

### Step 格式（Full TDD）
- [ ] RED: 写测试 `[测试文件路径]` — `[测试描述]`
- [ ] RED-VERIFY: `[运行命令]` → 期望 FAIL: `[预期错误信息]`
- [ ] GREEN: 实现 `[实现文件路径]` — `[实现描述]`
- [ ] GREEN-VERIFY: `[运行命令]` → 期望 PASS
- [ ] REFACTOR: `[重构描述]` → `[运行命令]` → 仍 PASS

### Step 格式（Lite TDD）
- [ ] RED: 验收命令 `[命令]`
- [ ] RED-VERIFY: 确认输出为 `[当前值/不存在]`（验证未满足目标）
- [ ] GREEN: `[实现动作]`
- [ ] GREEN-VERIFY: `[同一命令]` → 期望输出 `[目标值]`
- [ ] REFACTOR: `[清理]` → `[命令]` → 仍符合预期

---

## Verification Strategy (two-tier)

- **After each Task**: 运行 Light verification 命令
- **After all Tasks complete**: 运行 Full verification 命令
- If verification commands are not configured: note "verify manually" — do NOT invent commands

---

## Commit Checkpoint Guidance

**为什么有 Checkpoint**：避免两种极端——每个 task 一次 commit 太碎，全部 task 完成一次大 commit working tree 长期不干净。Checkpoint 让 task-execute 按"模块/语义"分批落盘。

**怎么划分 Checkpoint**：

- 2-3 个 task 形成 1 个 Checkpoint 比较常见。Low complexity 整个 Phase 4 可能只有 1 个 Checkpoint；High complexity 通常 3-5 个。
- 划分的依据是**语义相关性**而非数量：
  - "基础设施 / 框架接入 / 工具配置"成一组（如 Preact 接入 + tsconfig/esbuild + tokens）
  - "UI 组件群"成一组（如 Hero + TaskList + CompleteOverlay）
  - "设置 + 边界 toggle"成一组（如设置手风琴 + SwiftBar toggle + 状态栏 toggle）
  - "测试 / 验收 / 收尾"成一组
- 跨模块的"被多处依赖的小改动"（如 types.ts、constants.ts 加字段）划到首次使用它的 Checkpoint，不单独成组。
- 每个 Checkpoint 应该是**可独立 build + 部分跑通**的状态（不能落地一个让仓库构建失败的 commit）。

**Checkpoint 在 plan.md 中的格式**：放在该 Checkpoint 覆盖的末个 task 的 `### Verification` 之后，作为该 task 的 sibling 子小节：

```markdown
## Task 3: Hero + RingTimer + TaskSwitcher
...
### Verification
- npm run build 成功
- Hero 视觉与 panel-bold.jsx 1:1

### ✔ Commit Checkpoint 1
`feat(hat-pomodoro): preact 接入 + 设计 token + Hero`
覆盖 Task 1-3
```

`task-execute` 在执行到 Checkpoint task 时，完成该 task 的所有 Steps 后会 propose `git add <specific-files> && git commit -m "<message>"`，落盘后再进入下一 task。

---

## No Placeholders — Forbidden Patterns

以下模式会导致 plan 被自动拒绝：

- TBD, TODO, "to be determined"
- "Add error handling"（must specify which errors）
- "Similar to Task N"（must fully expand）
- "Implement the rest"（must list each item）
- "Update tests accordingly"（must specify which tests, what assertions）
- "Add appropriate validation"（must specify what to validate）
- "验收: 手动检查"（must be executable command）
- "验收: 确认正确"（must specify expected output）
- 把验收测试单列成一个独立 task（验收测试在 Phase 5 执行，plan 中不包含此类 "Acceptance Tests" 收尾项）
- 无 RED/GREEN 标记的 step（tdd 启用时每步必须有验证循环）

**为什么"Similar to Task N"被禁、要求每个 task 重复完整代码**：执行工程师可能乱序读 task（尤其 subagent 各自独立 session、只拿到单个 task 段落）。引用"见 Task N"会让他读不到被引用的内容。因此每个 task 必须**自包含、重复完整代码 / 步骤**，而非交叉引用其他 task。

---

## Self-Review Checklist

plan 编写完成前必须完成此 checklist：

- [ ] design.md 中的每个需求都有对应的 task
- [ ] plan 顶部有 File Structure 职责图，覆盖全部 Create/Modify 文件
- [ ] 每个 task 都有 **Implementation Guardrails** section（allow_variations + anti_patterns）
- [ ] 无占位符文本（扫描上方 Forbidden Patterns）
- [ ] 类型名、方法名、变量名在各 task 间保持一致
- [ ] 所有文件路径是精确的（无模糊或相对路径）
- [ ] 验证命令引用了项目实际的检查命令
- [ ] task 依赖是显式的（每个 task 有 `Depends`，后续 task 不引用尚未创建的文件）
- [ ] 每个 task 有明确的验证标准
- [ ] **跨 task 文件引用一致性**：当 Task B 创建的文件需要与 Task A 的产物交互时（如 CSS 选择器匹配 HTML 元素、JS 操作特定 DOM id、API 契约），plan 中必须显式声明引用关系和命名约定。若使用 subagent 执行（各 task 独立 session），这些约定是唯一的一致性保障

Self-review 通过后，在 plan.md 末尾追加：

```
Self-review checklist: passed
```

---

## Execution Handoff Note

plan.md 编写完毕且 self-review 通过后，主 session 继续执行以下步骤：

1. 将 plan.md 保存到 `.tasks/open/YYYY-MM-DD-topic/plan.md`
2. 创建 Exec 级 Todo List（每个 plan task 对应一项）
3. 向用户展示计划以供审核
