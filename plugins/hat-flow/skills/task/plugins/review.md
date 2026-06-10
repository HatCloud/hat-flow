# Review Plugin

## P2.post-design-draft

### 设计自我审查 + 独立 Review

design.md 写完、用户确认前执行。

### 自我审查（6 项）

以"新读者"视角审查 design.md：
1. **Placeholder scan**: TBD、TODO 或模糊描述？就地修复
2. **Internal consistency**: 各节之间是否矛盾？
3. **Scope check**: 是否足够聚焦？
4. **Ambiguity check**: 是否有歧义需求？选定一种理解并明确
5. **External assumptions audit**: 列出所有外部系统假设，每一项必须有证据支撑（源码引用、spike、文档 URL）。无证据 → 标记 UNVERIFIED
6. **Acceptance test coverage**: 每个 Success Criteria 是否有对应的 Acceptance Test？

就地修复所有问题。

### Review 策略确认

自我审查后、独立 review 执行前，AskUserQuestion 确认：
1. Review 轮数：按复杂度默认 N 轮，是否调整？
2. Code review 策略：Light / Medium / Full / 跳过
3. Reviewer 类型：Claude（推荐）

### 独立 Review（Reviewer Subagent）

根据复杂度自动触发（不等用户提醒）：

| Complexity | Rounds | 说明 |
|---|---|---|
| Low | 0 | Self-review 即足够 |
| Medium | 1 | R1：结构审查 |
| High | 2 | R1：结构审查 + R2：对抗审查 |

派发 design-reviewer（`subagent_type: design-reviewer`；保留 model override——R1 Sonnet / R2 Opus 在派发时指定），prompt 中注入：
- `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/DESIGN_REVIEW.md`
- `design.md`、`prompt.md`
- 当前轮次编号和审查重点

模型选择：
- R1（结构审查）：Sonnet
- R2（对抗审查）：Opus

R1 返回后处理：
- Medium 复杂度：Critical ≥ 1 或 Important ≥ 3 → 触发额外 R2
- High 复杂度：默认执行 R2
- 根据 reviewer 反馈就地修复 design.md

回退：reviewer subagent 失败时主 session 人工审查。

## P2.post-design-approved

### Review Strategy 写入

用户确认设计后，将 Review Strategy 写入 design.md：

```markdown
## Review Strategy
- Design review: N 轮（已完成）
- Code review: {策略}
- Per-task review: {each | checkpoint}
- Reviewer type: Claude
```

> `Per-task review` 取自 task-config.json `plugins.review.per_task_review`（缺省 `each`）。仅在 `Code review ∈ {medium, full}` 时有意义；`skip/light` 下逐 task review 本就不必做，该行可省略或记 `each`（无副作用）。

### 复杂度评估

在 Review Strategy 写入后执行：

| Signal | Low | Medium | High |
|---|---|---|---|
| Files involved | 1-2 | 3-6 | 7+ |
| New modules/arch | None | Local | Cross-module |
| New APIs/libraries | None | Few | Many |
| design.md words | <500 | 500-1500 | >1500 |

向用户展示评估。用户可覆盖。

## P3.post-plan

### Plan 忠实度评估

plan.md 生成后，评估其与 design.md 的一致性：

1. **Design alignment**: plan 覆盖了 design.md 所有 Success Criteria？
2. **Scope check**: plan 是否引入了 design 未提及的范围？
3. **Dependency consistency**: task 间的依赖关系是否合理？
4. **Verification completeness**: 每个 task 是否有验证步骤？

派发单个 plan-reviewer（`subagent_type` 对应 reviewer，注入 `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/PLAN_REVIEW.md` + plan.md + design.md）跑一次 single-pass review，**不按复杂度分 0/1/2 轮、不按维度派多个 subagent**。reviewer 返回 SC2 二元结论 `Verdict: Approved | Issues`：

- **Approved** → Issues 桶为空，Advisory 桶（如有）仅供参考，继续。
- **Issues** → 就地修复 Issues 桶中的 Critical / Important 条目后继续（Advisory 不阻断）。

## P4.per-task-post

### Per-Task 代码审查（按复杂度条件执行）

每个 task 完成后，根据 design.md 的 Review Strategy 中 code review 策略决定：

| Code Review 策略 | Per-Task Review |
|---|---|
| skip | 不执行 |
| light | 可选 |
| medium | 必做 |
| full / high | 必做 |

**先判 per-task 粒度（`Per-task review` 行，缺省 `each`）**：

- `each`（缺省） → 按上表逐 task 派发（质量优先，默认行为）。
- `checkpoint` → **跳过逐 task 派发**，不论 code review 策略是 medium 还是 full。per-task 覆盖改由 P4.post-execute 全量 review 兜底（届时全量 review **不降档**、按 full 规模跑——见 `## P4.post-execute/full-review` 降档前置）。适用于 prose-only 多-task 重构：逐 task 派发边际收益递减时，用一次足规模全量 review 替代 N 次逐 task 派发以省 token。
- 当 code review = `skip/light` 时 per-task 粒度无意义（本就不必做或可选），忽略此行。

`each` 下派发 code-reviewer（`subagent_type: code-reviewer`），prompt 中指示：
1. 读取 `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/CODE_REVIEW.md`（Light checklist）
2. 自行运行 `git diff HEAD~1 HEAD -- <task_files>` 获取 diff
3. 读取 plan.md 对应 task 段落

Two-Stage Review：

| Stage | Focus | 不通过时 |
|---|---|---|
| Stage 1: Spec Compliance | 实现是否匹配 plan？ | 修复 → 重试（最多 2 次） |
| Stage 2: Code Quality | 代码是否做好了？ | 修复 → 重试 |

Stage 1 必须通过后才开始 Stage 2。

Review scope 限定为当前 task 变更的文件。

## P4.post-execute/full-review

### 全量代码审查

所有 task 执行完毕后进行。维度数 / agent 数**自适应**——不死绑 full→4，由 diff 性质决定。

#### 降档前置（进维度自适应表之前先判）

进入维度自适应表前，先判是否可降档全量 review 的 agent 规模。

- **信号源**：`design.md Review Strategy 的 code review ∈ {medium, full}` **且** `Per-task review = each`（缺省）**且** phases.md `4a` 已完成。在 medium / full + `each` 策略下 per-task review 逐 task 必做（见 P4.per-task-post），故各 task 在执行中已被逐个审过——per-task 覆盖已成立，全量 review 无需再以最大规模重审。
- **成立** → 设 `agent_count_cap=2`（全量 review 的 agent 数上限封顶为 2），随后**仍进**下方维度自适应表做维度分配，并**保留 ARCHITECTURE 维度的 opus 隔离**（架构型 review 命中时该维度照常 override opus，不受 cap 影响其模型选择）。
- **不成立** → 不设 cap，直接走下方原表。命中任一即不降档：① code review = skip/light；② `Per-task review = checkpoint`（逐 task 未派发，全量 review 是唯一 review，必须足规模兜底）；③ 4a 未完成。

降档只封 agent 数上限，不改下方表的判据本身。

#### 维度自适应（AND 双信号）

判"架构型 review"需 **两个信号同时成立（AND）**：
1. **触架构文件**（见下方清单）
2. **结构性改动**（改到 hook 调用 / 停止点 / 路由逻辑 / 状态机 / 调度，**非纯措辞**）

| 情形 | Agent 数 / 维度 |
|---|---|
| 纯 prose / 措辞改动（即便落架构文件，无结构性改动） | **1 合并 agent**（覆盖全部维度 checklist），**不论 diff 行数** |
| 非架构文件的常规代码改动 | 2 agent：Agent 1 PLAN_ALIGNMENT + ARCHITECTURE；Agent 2 CODE_QUALITY + TESTING |
| 架构文件 **且** 结构性改动（架构型） | **4 agent**，每维度独立，**隔离 ARCHITECTURE 维度**（该维度 override opus） |
| skip | 跳过 |

- **"纯 prose / 措辞改动" 定义**：变更内容为自然语言文本（文档、注释、描述字段），不含控制流、条件判断、调用关系的增删。非架构文件的纯 prose 也走 1 合并 agent。
- **术语区分**："架构文件"（AND 信号 1）指**文件身份**——是否工作流结构文件（见下方清单）；"ARCHITECTURE 维度"指 CODE_REVIEW.md 的代码质量 checklist（Pattern Consistency / 关注点分离 / 模块边界），对**任何代码**都适用。故"非架构文件的常规代码改动"档仍跑 ARCHITECTURE 维度（检查代码级模式一致性），与该文件是否属架构文件无关。
- **diff 行数（~150 参考）仅作粗筛次信号**——大 diff 倾向多维度，但 AND 双信号是主判据；纯措辞改动即便行数多也走 1 合并 agent。
- **模型**：默认用 code-reviewer agent 定义的 model（sonnet）；**仅架构型 review 的 ARCHITECTURE 维度**在派发时 override opus，其余维度一律 sonnet。

#### 架构文件清单（单一事实源）

判"触架构文件"以此清单为准：
- `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md`（编排器）
- `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.manifest.json`（hook 点声明）
- `${CLAUDE_PLUGIN_ROOT}/skills/task/plugins/*.md`（plugin 指令文件——承载派发/评分/状态机等结构性逻辑，含 review.md 自身）
- `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`
- `agents/*.md`
- `bin/*`
- 各 `skills/task-*/SKILL.md`（phase skill）

派发 code-reviewer（`subagent_type: code-reviewer`；仅架构型 review 的 ARCHITECTURE 维度 override opus，其余用 agent 默认 sonnet），prompt 中注入：
1. `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/CODE_REVIEW.md` 对应维度 checklist（1 合并 agent 时为全部维度）
2. 运行 `git diff` 获取 diff
3. 如 `{task-folder}/design.md` 含 `## Acceptance Tests`：在 prompt 中注入这些验收项（含 `[MUST|SHOULD|MAY]` 标签与变体 / 反模式注记），指示 reviewer 按 CODE_REVIEW.md 的 Acceptance Context 章节把它们当作"合法实现"判断上下文（**不输出 VERDICT、不打分**）

在 reviewer subagent prompt 中注入：
> Do not trust the implementer's claims about code quality or completeness. Verify all changes by reading the actual diff.

#### 收敛场景派发：后台 + 捕获 agentId（衔接 convergence 复活）

当 code review 策略为 medium / full（可能进入收敛循环，见下方 convergence）时，**Round 1 的 code-reviewer 一律用 `run_in_background=true` 派发**（background 派发是预备动作，Round 1 即便 C=0/I=0 不进循环也不损失），并**捕获每个 agent 返回的 `agentId`**，建立 **agent→{它覆盖的维度}** 映射：

- 1 合并 agent → 该 agentId 覆盖全部维度 checklist。
- 2 agent → 各 agentId 覆盖 2 个维度。
- 4 agent（架构型）→ 各 agentId 覆盖 1 个维度。

映射粒度随维度自适应表的 agent 数自然变化。后台派发后主线程结束回合，由 convergence 的 JOIN 协议收齐结果——故派发与 join 是 convergence 的统一控制流，本节只负责「用 background 派 + 记 agentId + 建映射」这一前置动作。映射 + agentId 写入 phases.md 4b 行 `[→ 收敛 R1 agents:...]` 标注（格式见 convergence）。

## P4.post-execute/convergence

### 收敛循环（修复 → 重 review 直到 C/I 清零或达 max_rounds）

4b 收敛是**带显式 join 的跨回合异步循环**：Round 1 后台派发 reviewer（见 full-review「收敛场景派发」），主线程结束回合等 completion notification；Round≥2 用 `SendMessage` **复活已结束的同一 reviewer**——它从自身 transcript 完整恢复跨轮上下文，主线程每轮只发一句极短消息，不再重灌上轮 findings / 修复 diff / plan 正文（消除主线程收敛轮 output token，这是本机制的收益核心）。

> **派发原语 vs 等待语义**：复用 ISSUE 的派发原语（`run_in_background=true` Agent + completion notification），但**不是** fire-and-forget。linear-sync 可静默丢失、由下个 phase 兜底；4b 收敛是**强 join 门控**——必须收齐全部 reviewer 结论才能判 C/I，下游 P5 无兜底，带病推进即漏审。故在派发原语之上叠加下方 JOIN 协议。

全量 code review 返回后，按 severity 统计 findings（依据 CODE_REVIEW.md 的三级 severity + severity-escalation.yaml）。轮次计数从 1 起，上限取 `task-config.json` 的 `plugins.review.max_rounds`（默认 3）。

收敛判据：**Critical = 0 且 Important = 0**。Important 在收敛中与 Critical 同等对待、不放过——这是修掉旧"Important 永不阻断"失明问题的核心。

**消费 review 反馈的纪律**：主 agent 在就地修复 findings 前，应用 `hatflow-receiving-code-review`（已导入，`${CLAUDE_PLUGIN_ROOT}/skills/hatflow-receiving-code-review/SKILL.md`）纪律——不附和式接受、先验证每条 finding 是否真实（读 diff / 跑命令）、以 YAGNI 视角避免过度修复、对错误的 finding 用技术理由反驳而非照单全收。验证后再修，避免把 reviewer 的误报也"修"进去。

#### JOIN 协议（收齐期待 agentId 集合才推进）

主线程维护「本轮**期待 agentId 集合**」（= Round 1 派发的全部 agentId / Round≥2 复活或改派的 agentId）。每个 completion notification 重入时，按 notification 的 `task-id` 匹配该集合：

- **命中** → 记录该 agent 的 review 结果，标记其已报。
- **未命中**（linear-sync / 用户消息 / 其他后台 subagent）→ **不计入 join、不推进**，正常吸收后继续等。

`已报 == 期待全集`？ —— 否 → 结束回合继续等；是 → 汇总全部 findings、按 severity 统计，进入收敛判据。

> JOIN 必须按 `task-id`(=agentId) 严格绑定，**严禁**被 linear-sync / 用户 notification 误触发推进——否则会在 reviewer 未收齐时就判 C/I，等于漏审。

#### Round≥2 复活（SendMessage + 显式 diff range）

对「本轮需重评维度」（见下方瘦身）映射回「覆盖这些维度的 agent」，对各 agentId 发**极短** `SendMessage`：

```
已修复 findings {ids}（{一句话摘要}）。请对 `git diff {显式range}` 复评你负责的维度，
按 CODE_REVIEW.md severity 报告剩余 Critical/Important。
```

- **复活前先 `git commit` 本轮修复（或记录稳定 ref）**，消息给定该 commit 区间 / ref 作为**显式 diff range**——与主线程统计 finding 用的同一快照，不让 reviewer 裸跑 `git diff` 各自解读。
- 消息**不含** findings / diff / plan 正文——reviewer 从自身 transcript + 指定 range 自取（粘贴正文会抵消 token 收益，属反模式）。
- 复活后新一轮的期待集合 = 本轮复活/改派的 agentId，回到 JOIN。

#### 改派触发判据（默认继续等，避免「永远等」或「收到第一个就改派」两极）

仅以下两种情形对某维度**改派全新 reviewer**（新 agentId 纳入期待集合，回到 JOIN）：

1. **派发 / 复活即报错** → 该维度立即改派。
2. **掉队者（straggler）**：期待集合中其余 agent 全部已报、**仅剩最后 1 个**未报，且其后**主线程再被其他 completion notification 被动唤醒 2 次**（是主线程被动重入、**不是**主动 ping 该 straggler）该 straggler 仍未报 → 判定不会再回，对其改派。

其余情况（尚有多个未报、且无报错）→ 结束回合继续等。绝不无限挂死。

#### 收敛循环触发模式（Interactive vs Unattended）

> 下表是收敛循环的**顶层触发条件**（是否就此 finding 进入下一轮），与上方「改派触发判据」（单个 agent 超时/报错的处理）是两个独立概念，勿混。

| 模式 | 触发循环 | 行为 |
|---|---|---|
| **Interactive** | 存在 Critical | 推荐进行一轮收敛：验证并就地修复 C/I → 复活受影响维度的 reviewer（轮次 +1，失败则全新派发兜底）→ JOIN 收齐后重新统计。修复前 AskUserQuestion 确认（用户可让继续循环、可指出额外问题再循环、也可接受现状停止）。Important-only 时建议修复但不强制循环。 |
| **Unattended** | ≥1 Critical **或** ≥2 Important | 自动验证并就地修复 → 复活受影响维度的 reviewer（轮次 +1，失败则全新派发兜底）→ JOIN 收齐后重新统计，**不询问**。 |

退出条件：
- **已收敛**（C=0 且 I=0，或 Interactive 下用户明确接受现状）→ 标记 4b 完成，继续。
- **达 max_rounds 仍未清零**：
  - **[Interactive]** AskUserQuestion：再加轮次 / 接受现状并记录 / 转 Revise / 终止。
  - **[Unattended]** 停下，发送 Telegram 通知 `[task-name] code review 达 max_rounds（{N}）仍有未清 C/I：[清单]`，等待人工。

#### 收敛轮瘦身（round ≥ 2 只重派受影响范围）

第 1 轮按维度自适应全量派发。**从第 2 轮起，不无脑全量重跑**：

- **只复活受影响维度**——上一轮仍有未清 C/I 的维度才复活其 reviewer；已清零的维度不再触动。
- **只复评受影响范围**——复活消息指定的 range 即本轮修复范围，reviewer 只重评与未清 findings 关联的代码 / 验收项，不全量重评。
- 若上轮某维度的修复**触及了原本已清零维度的代码**（跨维度回归风险），把该维度也纳入复活。**可操作判据**：对比本轮修复 diff 的文件集合与各已清零维度上轮 findings 引用的文件集合——有交集则该维度纳入复活（不靠直觉"我没动那块"）。
- 故「本轮需重评维度 = 仍有未清 C/I 的维度 ∪ 跨维度回归命中维度」，映射回覆盖这些维度的 agent 复活之。

这样收敛轮的 token 随未清范围收窄而递减，而非每轮重复全量审查。

#### 状态存储 + 降级兜底

- **跨回合状态**：期待集合、轮次、未清 findings 存对话上下文（同 session 跨回合天然保留）。**agent→{维度}→agentId 映射写入 phases.md 4b 行 `[→ 收敛 Rn agents:dim=<agentId>;..]` 标注**（如 `[→ 收敛 R2 agents:ARCHITECTURE=a1b2..;CODE_QUALITY=c3d4..]`），作为 compaction 后恢复 agentId 的依据。
- **统一降级**：任何导致 agentId 失效的情形——resume 新 session / 同 session compaction 丢 in-memory / 目标 agent 已死 / 复活结果异常（空 / 格式损坏 / 跑错 range）——**该维度回退全新派发**，无 self-brick。同 session compaction 后先从标注恢复 agentId 尝试复活，agent 仍活则成功、已死则全新派发。
- **回退上下文来源**：全新派发**不依赖主线程持有的上轮 findings**——全新 reviewer 只需 `plan.md`（磁盘）+ 指定 range 的 `git diff`（repo）即可做该维度全量 review（等同 round-1 单维度行为）。回退路径可行、非空壳；代价是该分支无 token 收益，在净收益对账中如实计入。

#### 路由互斥（与 REVISE 标注）

`[→ 收敛 Rn ...]` 与既有 `[→ REVISE RN]` 在 4b 行**互斥**：收敛是 revise 触发的前置，二者不同时存在；进入 Revise 即清除收敛标注。`收敛` 与 `REVISE` 前缀不同，不会被 revise-detection 的回归模式检测误捕（见下节）。

> **净收益判定（SHOULD）**：本机制的收益在主线程收敛轮 output token（不再重灌 findings/diff/plan，dogfooding 标记 avg 3426 token/次），代价是被复活 subagent 重载自身 transcript（input token）。若实测净收益不成立，**保持现状（全新派发）**——复活是优化、非正确性前提。

<HARD-GATE>
A single Critical finding triggers the convergence loop. In unattended mode, never let any Critical — or ≥2 Important — pass review unaddressed.
Reason: the old multi-Critical-count threshold let one or two genuine Critical issues pass silently, and Important never blocked at all — the exact blindness that let a severe bin-unit-tests issue ship as "Important, skippable". Severity must gate; the loop runs until C/I clear or a human is paged at max_rounds.
</HARD-GATE>

> 收敛循环处理的是**可就地修复**的 C/I findings。若问题是系统性的（同一根因跨多文件、需重新设计或重做 plan），改走下方 Revise 触发（设计/计划返工），而非反复就地修复。

## P4.post-execute/revise-detection

### Revise 触发检测

全量 code review 完成后，检查是否需要触发 Revise Cycle：

### 回归模式检测

检查 phases.md 中 4b 步骤是否有 `[→ REVISE RN]` 标记（精确匹配 `REVISE` 前缀；**`[→ 收敛 Rn]` 是收敛循环的临时标注、非回归触发，不在此匹配**）：
- 如有：进入回归模式——scope 限定为 `git diff revise-rN-start..HEAD`
- 回归 review 通过后：标记 4b `[x]` + 确认 Revise RN Return 完成
- 回归 review 不通过：AskUserQuestion——触发新 R(N+1) / 手动修复 / 终止

### AI 触发检测（首次执行模式）

收敛循环（见上 P4.post-execute/convergence）负责清理可就地修复的 C/I。Revise Cycle 仅用于**系统性**问题——就地修复无法解决、需返工设计 / 计划：

- 同一根因跨 3+ 文件 → 建议触发 Revise
- 架构级缺陷（修复需跨模块重新设计）→ 建议触发 Revise
- **[Interactive]** AskUserQuestion：触发 Revise（Full/Partial/Lite）/ Defer to new task / 继续手动修复
- **[Unattended]** 自动选择深度：跨 3+ 文件或架构级 → Full；局部多文件 → Partial；≤ 2 文件 → Lite

### Revise 触发执行

1. 在 phases.md 4b 步骤后追加 `[→ REVISE R1]`
2. 在 phases.md 末尾追加 Revise section
3. 声明 "Revise R1 已触发，返回编排器。"
4. **不标记 4b 为 `[x]`**

## P5.test-feedback

### 测试阶段 Revise 检测

测试发现架构级问题时，评估是否需要触发 Revise Cycle（5e 架构问题判别）：

- 功能级 bug（局部修复即可）→ 不触发 Revise，正常修复
- 架构级问题（修复需跨多个模块/重新设计）→ 建议触发 Revise
- **[Interactive]** AskUserQuestion：触发 Revise / 局部修复 / 终止
- **[Unattended]** 自动评估并决定
