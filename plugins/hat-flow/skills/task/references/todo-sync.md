# TODO Sync（维护进度清单；Claude 落点见 harness-tools.md）— Canonical

task 套件 TODO 同步契约的单一来源。orchestrator 与各 phase skill 引用本文件，不再各存副本。

phases.md 是跨 session 的持久化状态源，但用户在当前 session 中无法实时看到进度，因此进度通过维护进度清单（Claude 落点见 harness-tools.md）同步到 UI。

**本文件契约按 `config.todo_sync` 三档执行**（`off | overview | full`）。档位由 1b.3 选定、1f 落盘、resolver 规范化 legacy boolean（`true→full` / `false→off` / 非法或缺失→`full`）。下方「触发点表」是**唯一权威的「何时建 / 何时切 / 何时清」**——取代了旧版散落的「Phase 1 开始就建」「每次维护双层」等表述。

## 三档语义

| 档 | 语义 |
|---|---|
| `off` | **完全静默**：不调用任何维护进度清单（Claude 落点见 harness-tools.md；不建概览、不建 step）；Bootstrap 时亦不重建、不刷新、不清理既有 UI（纯 no-op）。 |
| `overview` | 只维护**1 行概览**：1f 创建、phase 切换更新符号、收尾置完成。**不建 step**。 |
| `full` | **双层**（概览 + 当前 phase step），现状行为。 |

`off`/`overview` 档下，phases.md 仍照常 inline 写入（它是持久状态源，与 TODO UI 解耦）——仅 UI 同步动作按档裁剪。

## 双层结构（`full` 档）

1. **概览行 (overview)**：始终存在的一条 task，subject 格式 `[<task-folder-name>] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End`，status 始终 `in_progress`（显示 spinner）。符号：`✔`=已完成 / `▶`=当前 / `◻`=未开始；phase 标题用一个英文单词（Init/Design/Plan/Execute/Test/End）。metadata `{"level":"overview","task":"<task-folder-name>"}`。`overview` 档同样维护这一行。
2. **当前阶段子步骤 (step)**：当前 phase 每步一条 task，subject 前缀 `→`。metadata `{"level":"step","phaseNum":N,"stepId":"Na"}`。**仅 `full` 档存在**。

## 显示效果（`full` 档）

```
◼ [2026-06-22-todo-sync-tiers] ✔P1:Init ✔P2:Design ▶P3:Plan ◻P4:Execute ◻P5:Test ◻P6:End
◻ → 3a. 生成 plan
◻ → 3b. Plan 忠实度评估
◻ → 3c. 提交任务文档
◻ → 3d. Linear 同步
```

## 确定性触发点表（唯一权威）

每个触发点给出**按档动作**与负责该触发的**锚**（哪个 skill 的哪个决策点）。这张表消除「何时建 TODO」的歧义——overview 锚定 **1f 末**（任务名 / config 已落盘），不再依赖「Phase 1 开始」这一尚未定 tier / 名字的空窗。

| 触发点 | `full` | `overview` | `off` | 锚 |
|---|---|---|---|---|
| **1f 末**（任务夹 + config 已落盘，name/tier 已定） | 建 overview（首个维护进度清单；Claude 创建落点见 harness-tools.md；取最小 ID）+ `in_progress` + 建 P1 step | 仅建 overview + `in_progress` | no-op | task-init 1f |
| **每 phase 入口**（读 phases.md 后） | 删上一 phase step + 建本 phase step | 不动 step | no-op | 各 phase TODO Sync |
| **步骤完成** | 维护进度清单（Claude 更新落点见 harness-tools.md，状态 `completed`）+ 同步 phases.md | 仅同步 phases.md | 仅同步 phases.md | 各 phase |
| **phase 切换** | 更新 overview 符号 | 更新 overview 符号 | no-op | orchestrator Step 3 |
| **Bootstrap / 跨 session RESUME** | 先维护进度清单（Claude 列表落点见 harness-tools.md）：无 overview→重建（首个维护进度清单；Claude 创建落点见 harness-tools.md；保最小 ID）+ `in_progress`；有 overview→维护进度清单（Claude 更新落点见 harness-tools.md）刷新 subject/符号到 phases.md 当前态。再按 phases.md 校准/重建当前 phase step（已完成步骤标 `completed`）；**当前 phase 为 Execute 时例外**——step 重建按 task-execute 的「Phase 4 step 级 task 展开规则」以 plan.md 逐 plan task 重建，不用 phases.md 的 4a/4b 粒度（否则 resume 后 step 级进度退化为两行） | 同 full 的 overview 分支（重建或刷新概览），**不建 step** | no-op（不重建、不刷新、不清理） | orchestrator Step 2B / 各 phase resume |
| **task-reopen** | overview 由 `completed` 改回 `in_progress` + 符号回退到重开的 phase；重建该 phase step | 同左 overview 动作，不建 step | no-op | task-reopen |
| **task-revise（phase 内 Revise 子循环）** | 按 Revise section 步骤建/更新 step（`update_step`，同「步骤完成」语义） | no-op（仍在当前 phase，概览符号不变） | no-op | task-revise |
| **task-end / task-cancel** | overview 置 `completed`（cancel 可加标记）+ step 全清 | overview 置 `completed`（cancel 可加标记） | no-op | task-end / task-cancel |

**ID 顺序假设**：overview 首建→拿最小 ID 以固定首行。保证不了时仅影响 UI 行序（cosmetic，graceful 降级，不阻断流程）。

## 4 命名模板（payload 明确）

| 模板 | subject | metadata | 各档约束 |
|---|---|---|---|
| `update_overview` | `[<task-folder-name>] <P1..P6 符号串>` | `{"level":"overview","task":"<task-folder-name>"}` | 来源仅 task-folder-name + phases.md 符号（**不依赖 Linear**）；`off` 不调用；`overview`/`full` 均用 |
| `update_step` | `→ <step 文本>` | `{"level":"step","phaseNum":N,"stepId":"Na"}` | **仅 `full`**；`overview`/`off` 不调用 |
| `transition_phase` | （组合动作） | — | 删旧 phase step（仅 `full`）+ 更新 overview 符号（`full`/`overview`）；`off` no-op |
| `cleanup` | （组合动作） | — | overview→`completed`（cancel 可加标记）+ step 全清（`full`）；`overview` 仅置 overview completed；`off` no-op |

## Graceful

维护进度清单（Claude 落点见 harness-tools.md）调用失败 → 记录、继续（TODO 仅 UI 辅助，不阻断主流程）。phases.md 与 TODO 不一致时以 phases.md 为准，下个触发点按表校准。
