---
name: task-test
user-invocable: false
self-evolving: inbox
description: "Use when executing Phase 5 (Test) of a task. Can be called standalone or via /task orchestrator. Do NOT use before Execute completes. 触发词: \"测试阶段\", \"task test\", \"验收\", \"验证阶段\""
word-budget: 2000
---

# Task Test — Phase 5: Test

任务测试阶段。运行完整验证，更新 Linear 状态，逐项引导用户验收。

工具落点按 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/harness-tools.md` 映射。

**Announce at start:** "Using task-test for Phase 5: Test."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- Check (light): !`tc=$(find .tasks/open -maxdepth 2 -name task-config.json 2>/dev/null | head -1); v=$([ -n "$tc" ] && python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('check',{}).get('light','') or '')" "$tc" 2>/dev/null); if [ -n "$v" ]; then echo "$v"; else r=$(grep -A1 '轻量' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'; fi`
- Check (full): !`tc=$(find .tasks/open -maxdepth 2 -name task-config.json 2>/dev/null | head -1); v=$([ -n "$tc" ] && python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('check',{}).get('full','') or '')" "$tc" 2>/dev/null); if [ -n "$v" ]; then echo "$v"; else r=$(grep -A1 '完整' CLAUDE.md 2>/dev/null | tail -1 | sed 's/^- //'); [ -n "$r" ] && echo "$r" || echo 'NOT_CONFIGURED'; fi`

> 若上方任一探测/注入行未展开（显示字面 `!` 前缀原文），先当场执行该命令 / Read 该文件取结果，再继续。

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**phase 入口**（`full` 删上一 phase step + 建本 phase step；`overview`/`off` 不动 step——概览符号由 orchestrator 在 phase 切换时更新）；步骤完成同步 phases.md（`full` 另 `维护进度清单，状态置 `completed``）。

---

## Resume Support

如果 phases.md 存在且 Phase 5 已有已完成的步骤（`[x]`），跳过这些步骤直接从第一个未完成步骤继续。

**phases.md 中 Phase 5 步骤对应：**
- `5a. 完整验证` → Step 5a
- `5b. Linear 状态更新` → Step 5b
- `5c. 验收清单` → Step 5c

**Task folder path**: 从 Runtime Context Tasks JSON 的 `open[0].path` 获取。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：`cat "{open[0].path}/unattended.json" 2>/dev/null`
2. **若 enabled == true**：
   - 执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
   - 读取全局配置（按第 0 节）：若 `task-defaults.json` 不存在，先从 `task-defaults.json.example` 复制创建，再 `cat` 读取，解析为 `task_config`（字段缺失时使用默认值）
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守的激活入口与契约（quiet / 交互主入口 / 后备入口、activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 只读取已有状态。

---

### 5a. Full Verification

<rule>
验证通过的前提是新鲜证据：① fresh 运行验证命令（Check (full)，不依赖记忆 / 上次结果）；② 读完整输出 + 退出码；③ 确认输出确实对应"验证通过"这一声明，三者齐备才标记通过。仅凭"应该通过""上次通过了""改动很小"的完成声明无效。
Reason: 证据优先于主张——未经新鲜验证的完成声明是虚假的，会让未测试的改动流向下游。依据见 `${CLAUDE_PLUGIN_ROOT}/skills/hatflow-verification-before-completion/SKILL.md`（Read 该文件获取完整 Iron Law、Rationalization Guard 托词对照表与 Claim Requirements 证据要求表）。
</rule>

**快速路径**：如果 Check (light) 和 Check (full) 均为 `NOT_CONFIGURED`（验证命令为 none），且 design.md `## Acceptance Tests` 中没有手动测试项（全为自动化验证），则 5a-5b 标记为 `[x]` 并跳到 5c 验收清单的自动化结果展示。

运行 **Full verification**（Runtime Context 中的 Check (full) 命令）。

如果通过，将 commit hash 记录到 `{task-folder}/.last-verified`。

（NO_GIT 模式下跳过 `.last-verified` 写入）

完成后：更新 phases.md，将 `5a. 完整验证` 标记为 `[x]`。

### 5b. Linear 状态更新

> 由 `P5.post-acceptance` hook 中 linear plugin 执行。

linear plugin 启用时，在验收完成后由 hook 将状态更新为 "In Review"。关闭时跳过。

- 验证通过不豁免 Linear 同步：plugin 启用时此步是团队可见性的固定环节，照常执行（仅在 plugin 关闭时跳过）。

完成后：更新 phases.md，将 `5b. Linear 状态更新` 标记为 `[x]`。

### Phase 5 Stop — Acceptance Checklist

**p5_auto_only 支持**：读取 `{task-folder}/task-config.json` 的 `p5_auto_only` 字段。
- `true` → 跳过手动测试项，仅执行自动化验收，acceptance-checklist.md 手动区域为空
- `false` / 不存在 → 正常流程（含手动测试项）

<rule>
手动测试项的用户确认是必经环节（p5_auto_only 模式除外）。自动化测试预填结果即可；手动测试由用户在清单文件中填写。
Reason: 提前收尾会跳过用户验收测试，让未验证的改动流向交付。
</rule>

从 `{task-folder}/design.md` 的 `## Acceptance Tests` 提取验收项（唯一来源），**分类**为自动化和手动两组：

- **可自动验证**：grep 匹配、命令行检查、文件存在性、构建/测试通过等——机器可判定结果
- **需人工判断**：UI 行为、主观体验、跨系统集成效果、运行时交互流程等——需要人类确认

对**纯声明式改动**（只改 SKILL/reference/config 的文案与契约、无新增可执行路径）的行为类 MUST，显式区分两档标注：**契约层可验**（grep/结构断言当场判）vs **需实跑 dogfooding**（本会话触达不到该行为路径）——后者预填 `DEFERRED(dogfooding)` 留痕，不默认当作已验证。

**Step 1: 批量执行自动化验收测试**

运行 5a 中的 light/full verification 结果 + design.md 中所有可自动验证的验收项。

**Step 2: 生成验收清单文件**

将自动化 + 手动测试结果写入 `{task-folder}/acceptance-checklist.md`。该文件是用户填写测试结果的**唯一界面**——对话可能因 context 推进而看不到测试项，文件不会丢失。

文件模板（极简 inline 格式——用户在箭头后填 PASS/FAIL + 可选备注）：

```markdown
# Acceptance Checklist

**Task**: {task-folder-name}
**Generated**: YYYY-MM-DD HH:MM

## Round 1

### 自动化测试（已预填，无需修改）

1. [MUST|SHOULD|MAY] 测试项描述
   → PASS
2. [MUST|SHOULD|MAY] 测试项描述
   → PASS
...

### 手动测试（请填写）

> 在 → 后填 PASS 或 FAIL（备注可选，写在结果后面）
> 例：→ PASS
> 例：→ FAIL 球还在动
> 注：无人值守 self_test 下人工项的 → 由系统预填 `DEFERRED（待 task-end 后人工验收）`，是第三种合法取值，留待 task-end Step 2.6 交还人工填 PASS/FAIL

1. [MUST|SHOULD|MAY] 测试项描述
   测试方法：具体操作步骤
   →
2. [MUST|SHOULD|MAY] 测试项描述
   测试方法：具体操作步骤
   →
...

### 追加修改（可选）

> 基于测试体验，如果有需要追加的修改或改进建议，请填写在下方。

-
```

**生成规则：**
- 首轮使用 `## Round 1` 显式编号（与后续 Round 结构统一）
- 自动化测试项：`→` 独占一行，预填 `PASS` 或 `FAIL`
- 手动测试项：`→` 独占一行留空，上方附 `测试方法：` 行
- Linear 同步状态附加到自动化测试区域
- 追加修改区域预留空行供用户填写

生成后告知用户：**"验收清单已生成到 `{task-folder}/acceptance-checklist.md`，请在模拟器上测试后填写手动测试项，填好后回复我。"**

**Step 2.5: 读取用户填写结果**

生成清单后，告知用户回复约定：
> "验收清单已生成。测试完成后请回复：
> - **`done`** — 我已在文件中填写了测试结果，请读取文件
> - **直接描述结果** — 如「全部通过」「XX没通过，表现为XXX，其他全通过」，我来帮你更新文件"

收到用户回复后，按以下方式处理：
- **用户回复 `done`**：读取 `acceptance-checklist.md` 文件解析结果
- **用户回复文本描述结果**（如"全部通过"、"XX没通过"等）：
  1. 读取当前 `acceptance-checklist.md`
  2. 根据用户描述代为填写所有 `→` 结果
  3. 保存文件后展示修改摘要，请用户确认

然后继续原有的解析逻辑：

等待用户回复后，读取 `{task-folder}/acceptance-checklist.md`：

1. 解析手动测试区域每行箭头后的结果（`→ PASS` / `→ FAIL ...`）+ 读取每项的 `[MUST|SHOULD|MAY]` 标签
2. **按标签门控**：`[MUST]` 或 `[SHOULD]` 的 FAIL → 读取备注文字，进入 5d（Handling Test Feedback）处理、**阻断 Phase 5 完成**（Interactive 下用户可显式接受现状跳出该项）；`[MAY]` 的 FAIL → **仅记录、不阻断**、不进修复循环
3. 解析"追加修改"区域 → 若有内容，逐条确认是否在当前 task 处理（简单修改直接做，复杂改动建议 defer）
4. 全部 MUST/SHOULD PASS（MAY 可 FAIL）且无追加修改 → 继续 Step 3
5. 有 MUST/SHOULD FAIL 项或追加修改需要代码变更 → 修复后进入 **Step 2.6**

**Step 2.6: 追加轮次**

修复完成后，**先重跑自动化验证**（light/full verification + 单元测试），确认新代码未引入回归。然后在同一文件末尾追加新的 Round section。前序轮次的结果保留作为历史记录。

追加格式：

```markdown
---

## Round N

### 自动化回归（已预填）

> 修改后重跑的自动化验证结果。

1. [—] `pnpm lint && pnpm typecheck`
   → PASS
2. [—] `pnpm test` (N/N passed)
   → PASS

### 手动测试（请填写）

> 包含上轮 FAIL 项的回归测试 + 追加修改的新测试项。

1. [MUST|SHOULD|MAY] 原测试项描述（上轮 FAIL / 回归）
   测试方法：具体操作步骤
   →
2. [SHOULD] 追加修改描述
   测试方法：具体操作步骤
   →

### 追加修改（可选）

-
```

**追加规则：**
- Round 编号从 2 开始递增（首轮隐含为 Round 1）
- 回归测试：上轮 FAIL 的项（含修复后的重测）
- 追加修改测试：上轮追加修改区域中需要代码变更的条目，转为测试项
- 前序轮次不修改——保留完整的测试历史
- 用户填写后再次执行 Step 2.5 读取结果，循环直到全部 PASS 且无追加修改

**验收项回写（修代码前执行）：**

追加修改是测试阶段发现的新需求，必须先回写到 `design.md` 的 `## Acceptance Tests` 再改代码——保持 design.md 为验收标准的单一事实源。

1. 为每条需要代码变更的追加修改在 design.md `## Acceptance Tests` 末尾追加新验收项
2. 形态 `[SHOULD] 可执行/可观察的验收项`（测试阶段发现的追加需求默认 `[SHOULD]`，用户可覆盖为 `[MUST]` / `[MAY]`）；按需附变体 / 反模式纯文字注记
3. 新 round 的追加修改测试项引用这些新验收项（而非 `[NEW]`）

**基础设施问题分流**（适用于 FAIL 项）：
- 环境/配置问题 → 标记 NOT_APPLICABLE，不触发修复
- Baseline 已有问题 → 标记 NOT_APPLICABLE
- 本次改动引入 → 标记 FAIL，触发修复流程

若所有验收项均为自动化（无手动测试项），跳过文件中的手动区域，直接进入 Step 3（仍生成文件，但手动区域为空）。

**Step 3: P5.post-acceptance Hook（Linear 同步）**

验收完成后运行：

```bash
hat-plugin-hook {task-folder} P5.post-acceptance
```

hook 输出可能包含多段指令，**必须逐段全部执行**（linear: 状态更新为 In Review）。

更新 phases.md，将 `5c. 验收清单` 标记为 `[x]`，Phase 5 `**Status**: DONE`。

验收完成后是硬停，不自动推进 Phase 6（权威规则见「Test 完成 → 过渡」）。

---

### 5d. Handling Test Feedback

如果用户在测试后报告 bug：

1. **先分析，后行动** — 复现 → 找到根因 → 向用户解释 → 修改前获得确认
2. **改后待测** — 告知用户变更内容，让他们再次测试（commit 在用户确认后才进行）
3. **多轮反馈** — 每轮：分析 → 修改 → 用户确认 → 然后提交

commit 的前置条件是用户确认；未经验证的修复可能引入新问题。

#### P5.test-feedback Hook（架构级问题时触发）

测试发现架构级问题时，运行：

```bash
hat-plugin-hook {task-folder} P5.test-feedback
```

按输出指令执行（review: Revise 触发检测）。review 关闭时跳过，走下方手动判别。

#### Architectural Issue Triage（架构级问题判别）

<rule>
5d 测试发现的问题分两类：**局部 bug**（在 design 前提之内，原地修复）和 **架构级问题**（与 design 前提相悖，原地修复会让 task 边界失控）。后者必须 STOP 当前修补，向用户提问（结构化选项优先） 决定走向。

判别一个问题是否属于架构级 — 满足任一即是：
- 根因落在 design.md 显式或隐式假设之外（例如 design 假设"X 由 A 模块负责"，实际 X 落在 B）
- 修复方案需要扩展 design.md 才能合理表达
- 修复跨越当前 task 的模块边界（涉及未在 plan.md task 列表中的模块）
- 修复引入新的长期运行实体（进程、守护、bot、cron、外部依赖）
- 修复改变跨进程 / 跨 session / 跨服务的契约（路由、状态语义、消息格式）

确认是架构级后，向用户提问（结构化选项优先） 三个选项：
1. **触发 Revise Cycle** — 结构化的自适应单循环（根因分析 → 按需 design/plan → execute → verify），有完整状态追踪（phases.md 中 Revise section）。**不再选深度**——是否触及 design/plan 由 task-revise 的根因分析决定。
2. **Defer to a new task** — 本 task 仅做最小兜底（或不做），开新 task 处理
3. **Patch in place** — 仅限真正的局部修补（无状态追踪，直接改→测→commit），涉及多文件/多步骤时应选 Revise Cycle

**Revise 触发执行**（当用户选择选项 1 时）：
1. 在 phases.md 中相关验收项后追加 `[→ REVISE R1]`
2. 在 phases.md 末尾追加 `## Revise R1` section，包含字段：Trigger（5d）、Return（5c）、Reason（问题描述）、**Rootcause hint**（5d 架构判别已定位的层级：命中的判据 + 一句根因，供 task-revise RN-rootcause 作起点验证、不必从零重做）、Started（当前时间）、Status（IN_PROGRESS），步骤列表为单循环基线 `- [ ] R1-rootcause` / `- [ ] R1-execute` / `- [ ] R1-verify`（design/plan 由 task-revise 在 rootcause 后按需插入，**不预填、不用 `[~]`**）
3. 声明："Revise R1 已触发，返回编排器。"
4. **不标记 5c 为 `[x]`**——5c 在 revise 完成后的回归模式中才标记

**回归模式检测**（在 5c 验收清单中）：
- 检查 phases.md 中是否有 DONE 状态的 Revise section 且 Return 步骤为 5c
- 如有：进入回归模式——仅重跑触发 revise 的相关测试项，而非完整验收
- 回归通过后：**task-test（非编排器、非 task-revise）负责**标记 Revise RN Return 步骤完成 + 5c `[x]`

**用户主动触发**：如果用户在 Phase 5 任意时刻主动提出大 bug 或新需求（超出逐 bug 修复范围），提供 Revise Cycle 作为选项：向用户提问（结构化选项优先）——**触发 Revise Cycle** / **Defer to new task** / **继续逐 bug 修复**

Reason: 架构级问题若在 5d 直接原地修，会出现：commit 序列与 plan.md 脱节；final.md 难以解释偏差；后续相关 task 的 design 失去前置上下文。Revise Cycle 通过结构化子流程让偏差被显式记录而非隐式吞掉。
</rule>

<rule>
Test 阶段累计追踪已接受的**新功能**（不含 bug 修复）。累计达 3 项，或新功能改动体量明显超过本 task 的 Execute 阶段时，触发停点 + 向用户提问（结构化选项优先）：开新任务（记入 next-task-prompt.md）/ 触发 Revise Cycle / 继续。单次请求体量并非唯一触发条件，累计蔓延同样触发。
Reason: Test 阶段的新需求常是渐进式的——每条单看都低于单次请求阈值，合起来却把 Test 变成第二个 Execute（已有真实案例：P5 占产出 42% 反超 P4 的 35%，命名/状态/恢复/palette 全在 P5 内迭代）。累计闸门能捕获逐条检查漏掉的蔓延。
</rule>

即便用户在蔓延闸选择「本任务做」，**feature-sized 追加（体量接近独立 feature、或需要新的数据源/架构设计）也不经 task-revise 落地**——Revise Cycle 定义为 systemic-fix 循环，塞入 feature 属语义错配（design.md 会被反复追加 R 段）。此时改为：记入 next-task-prompt.md 分流新任务；用户坚持本任务做则作为显式标注的范围扩展直接走 Execute 增量（不开 Revise section）。

---

## phases.md Sync

每个步骤完成后更新 phases.md。每次更新步骤标记时，同步更新 `**Updated**` 时间为当前时间（格式 YYYY-MM-DD HH:MM）。

<rule>
每个步骤完成即更新 phases.md：标记步骤 [x]、更新 Updated 时间，所有步骤完成时更新 Status。
Reason: phases.md 是跨 session 的状态记录，遗漏更新会让下次 session 无法正确恢复。
</rule>

**Phase 5 完成时**（所有测试完成后）：将 Phase 5 的 `**Status**: PENDING` 改为 `**Status**: DONE`，更新 `**Updated**` 时间。

---

## Test 完成 → 过渡

Test 完成后**不自动推进**。用用户配置的语言简要宣告测试结果（自动化验证状态、Linear 同步状态、用户确认结果），声明 **"Phase 5 完成。"**，然后声明：**"所有测试已完成，请调用 `/task-end` 关闭任务。"**

声明后**停止输出，返回编排器 Step 3 执行过渡逻辑**（artifact check / 新会话交接 / unattended check）。

<rule>
Test 阶段是硬停：即便所有验收测试均为自动化且通过，也不自动推进到 End 阶段，须由用户显式调用 `/task-end`（无人值守例外见 UNATTENDED_PROTOCOL.md §6 task-test 表）。
Reason: 关闭任务前用户需要一个有意识的决策点——自动测试通过不等于用户验收。
</rule>

---

## Mandatory Stop Points

| Step | When | What to Ask |
|------|------|-------------|
| 5d | 架构级问题确认后 | 触发 Revise Cycle / Defer / Patch in place |
| 累计新功能 | 累计 ≥3 或体量超 Execute | 新任务 / Revise / 继续 |
| 5c 回归 | 回归 review 不通过 | 触发 R(N+1) / 手动修复 / 终止 |
| Phase 5 Stop | 所有测试完成后 | 硬停，告知用户调用 `/task-end`（不自动推进） |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经上方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## Dependencies

- **Reads**: `{task-folder}/design.md`, `{task-folder}/task-config.json`
- **Writes**: `{task-folder}/phases.md`, `{task-folder}/.last-verified`, `{task-folder}/acceptance-checklist.md`
- **Hooks**: `P5.post-acceptance`（linear: 状态更新为 In Review）, `P5.test-feedback`（review: Revise 检测）
- **Scripts**: hat-plugin-hook
