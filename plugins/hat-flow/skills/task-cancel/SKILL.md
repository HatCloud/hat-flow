---
name: task-cancel
description: "Use when the user decides to abandon or defer an in-progress task. Handles cleanup and archives the task folder from .tasks/open/ to canceled/ or deferred/. Do NOT use for completed tasks (use task-end). 触发词: \"取消任务\", \"放弃任务\", \"推迟任务\", \"defer 任务\""
word-budget: 1000
---

# Task Cancel — Lifecycle Closure

生命周期关闭 skill。记录任务被取消或推迟的原因，处理代码清理，并归档任务文件夹。

**Announce at start:** "Using task-cancel to close this task."

## Mandatory Stop Points

<rule>
每个 Mandatory Stop Point 都由 AskUserQuestion 把关，越过它需要用户明确确认。
Reason: 在决策点上自主推进，会在用户偏好与默认值不一致时造成无用功。
</rule>

| Step | When | What to Ask | Type |
|------|------|-------------|------|
| Step 1 | 多个打开的任务 | 选择要取消/推迟的任务 | Decision |
| Step 1.3 | 确认取消原因 | 需求变更 / 方案不可行 / 优先级调整 / 其他 | Decision |
| Step 1.4 | 确认处置方式 | Cancel permanently / Defer | Decision |
| Step 2.2 | 代码变更处理 | Keep / Discard / Partial | Decision |
| Step 3.0d | 子 issue 处理（仅 Canceled） | Cancel together / Detach to Backlog / Leave as-is | Decision |
| Step 3.3b | Process Review 有改进建议 | 逐条确认：立即执行 / 记录到 debt / 跳过 | Decision |
| Step 3.5 | Feature 分支处理 | 删除分支 / 保留分支 | Decision |

> 无人值守下各停点的自动决策见 UNATTENDED_PROTOCOL.md §6（经下方 Unattended State 加载器进入）。
> 停点状态信号（外部驱动可机读）由编排器停点 rule 统一写入，契约见 task/references/headless-driving.md。

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**cleanup（cancel 标记）**——`full`/`overview` 将 overview 置 `completed`（可加 cancel 标记）+ step 全清（`full`）；`off` no-op。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：`cat "{task-folder}/unattended.json" 2>/dev/null`（task-folder 从 Step 1 解析到的 phases.md 所在路径获取，而非 `open[0].path`——phases.md 是唯一权威状态源，多任务时按 `open[0].path` 取会取错）
2. **若 enabled == true**：执行 `Read ${CLAUDE_PLUGIN_ROOT}/skills/task/UNATTENDED_PROTOCOL.md`，加载完整协议
3. **若文件不存在或 enabled != true**：正常交互流程

> 无人值守的激活入口与契约（quiet / 交互主入口 / 后备入口、activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 只读取已有状态。

---

### Step 1: Identify Task

1. 检测任务：

   **Script** (preferred): `hat-task-detect .tasks` — exit 0 → 解析 JSON。`open` 数组包含任务对象，字段有 `name`、`path`、`linear`。

   **Fallback**: 手动读取 `.tasks/open/` 目录。

   - 一个任务 → 与用户确认："取消 [任务名称]？"
   - 多个 → AskUserQuestion 让用户选择
   - 没有 → "没有打开的任务。" **End skill.**
2. 读取任务的 `design.md`（如果存在）
3. AskUserQuestion 询问原因：
   - 需求变更
   - 方案不可行
   - 优先级调整
   - 其他（用户描述）
4. AskUserQuestion 询问任务处置方式（Cancel 与 Defer 语义截然不同：Defer 保留代码与子 issue 以备恢复；Cancel 是永久关闭）：
   - **Cancel permanently** — 任务不再需要，归档到 `canceled/`，Linear → Canceled
   - **Defer** — 任务将在以后恢复，归档到 `deferred/`，Linear → Backlog

### Step 2: Assess Completed Work

1. 检查是否有任何实现进展（`git diff --stat`、在分支上对比 main 运行 `git log --oneline`）
2. AskUserQuestion — 如何处理代码变更（推迟的任务默认为 **Keep**）：
   - **Keep** — 代码留在分支上，不合并（供将来使用或恢复）
   - **Discard** — 回退所有变更，删除分支
   - **Partial** — 用户指定要 cherry-pick 到 main 的 commit

### Step 3: Execute Cleanup

**3.0 Linear Sync** (conditional)

> 读取 `{task-folder}/task-config.json`，检查 `plugins.linear.enabled`。为 false 时跳过本步骤。

- 检查 `linear.json` 存在 → 按 `plugins/linear.md` 中的规范执行 Linear 状态更新（Canceled → Canceled UUID, Deferred → Backlog UUID）、评论发布、子 issue 处理
- 未找到 → 跳过

**3.1 Handle Code Changes** (基于 Step 2 的用户选择)：

如果 **Discard**：
```bash
git status --porcelain
git restore .
git clean -fd --dry-run  # 显示将要删除的内容 — 执行前与用户确认
git clean -fd
git status
```

如果 **Keep**：不需要代码清理。保留分支现状。

如果 **Partial**：将指定的 commit cherry-pick 到 main，然后清理其余部分。

**3.2 Switch to Main for Documentation** (如果在非 main 分支上)

<rule>
任务文档（final.md + 归档提交）在 main 分支上提交，而非在 feature 分支上。
Reason: 这样无论 feature 分支被保留还是删除，任务历史在 main 上始终可见。
</rule>

```bash
git status --porcelain  # 切换前必须是干净的
```

- 有未提交的变更：在此停下，显示文件，由用户先解决。
- 工作区干净：`git checkout main`。
- 已经在 main 上：跳过。

**3.3 Write final.md**

<rule>
final.md 完整记录任务被取消/推迟的原因以及从中获得的经验；不完整的取消报告会浪费已经投入的精力。
Reason: 取消报告是团队知识——未来的决策依赖于对过往失败的理解。
</rule>

在任务文件夹中创建 `final.md`（此时已在 main 分支上）：

**如果 Canceled：**
```markdown
# Task Cancellation Report

**Task**: [task name]
**Date**: YYYY-MM-DD
**Status**: Canceled

## Reason
[为什么取消]

## Work Completed
[列出已完成的工作，如果有]

- [x] 已完成项
- [ ] 未完成项

## Code Changes
[代码如何处理：保留/丢弃/部分保留]

## Lessons Learned
[可选：对未来工作的洞察]
```

**如果 Deferred：**
```markdown
# Task Deferral Report

**Task**: [task name]
**Date**: YYYY-MM-DD
**Status**: Deferred

## Reason for Deferral
[为什么推迟 — 什么阻塞因素或优先级调整]

## Work Completed
[列出目前已完成的工作]

- [x] 已完成项
- [ ] 未完成项

## Resume Notes
[恢复前需要做什么；下次 session 的关键上下文]

## Code Changes
[分支名和状态：保留供将来使用]
```

对于 Cancel 场景，特别关注：
- 取消的根本原因是否可以更早发现？（例如可行性预检）
- 设计阶段是否在最终被否决的方案上花费了过多 token？
- DESIGN_PROTOCOL 是否应包含快速可行性评估步骤？

**3.3c Clean Up Todo List**

归档前，确保所有 Tasks（Flow 级 + Exec 级）已标记为 completed 或已删除。扫描 TaskList 并更新所有剩余的 pending/in_progress 项：
- 已完成但未标记 → completed
- 因取消而跳过 → completed（附注释 "skipped due to task cancellation"）
- 用户手动完成 → completed

**3.4 Archive and Commit** (single commit)

暂存范围：仅 add 属于本次任务关闭的具体文件。`git add -A` 会拖入无关改动，因此不适用。

根据处置方式确定目标路径：
- **Canceled** → `.tasks/canceled/`
- **Deferred** → `.tasks/deferred/`

归档移动**之前**先写终态信号（先戳后移；Cancel → `--outcome canceled`、Defer → `--outcome deferred`；graceful，失败不阻断）：

```bash
hat-task-state terminal "{task-folder}" --outcome <canceled|deferred>
```

**Script** (preferred):
```bash
hat-task-archive "YYYY-MM-DD-topic" <canceled|deferred> --message "docs: <cancel|defer> and archive task [YYYY-MM-DD-topic]"
```
返回 JSON，包含 `archived`、`committed`、`commitHash`。

**Fallback** (如果脚本不可用):
```bash
mkdir -p .tasks/<canceled|deferred>/
git mv .tasks/open/YYYY-MM-DD-topic .tasks/<canceled|deferred>/YYYY-MM-DD-topic
git commit -m "docs: <cancel|defer> and archive task [YYYY-MM-DD-topic]"
```

使用 `git mv`（而非普通 `mv`），从 `open/` 删除和添加到目标路径原子性地暂存。

**3.4.1 Verify Commit Content**

提交后，运行 `git show --stat HEAD`。确认所有预期文件（final.md、任务文件夹移动、extra-files）都在提交中。如果缺少 → `git add -f` 然后 `git commit --amend --no-edit`。

**3.4.2 Clean Up Revise Tags** (conditional)

```bash
git tag -l 'revise-*' | xargs git tag -d 2>/dev/null
```

如果有 tag 被删除，输出清理结果。无 revise tag 则跳过。

**3.5 Handle Feature Branch** (如果之前在非 main 分支上):

已经在 main 上（在 3.2 中切换）。根据 Step 2 的用户选择：
- **Discard**: `git branch -D <branch>` — 如果已推送到远程，询问是否清理远程分支
- **Keep**: 保持分支不变（供将来使用或恢复）
- **Partial**: 分支已在 3.1 中处理

### Step 4: Confirmation

输出最终清单：

- [x] 原因已记录
- [x] final.md 已编写（在 main 分支上）
- [x] 代码变更已处理（保留/丢弃/部分保留）
- [x] 任务文件夹已归档到 canceled/ 或 deferred/
- [x] Feature 分支已处理（如适用）
- [x] Linear issue 已同步（如适用）
- [x] Linear 子 issue 已处理（如适用）
- [x] Git 已在 main 上提交（单次关闭提交）

## Dependencies

- **Reads**: `{task-folder}/task-config.json`
- **Scripts**: hat-task-archive, hat-task-detect, hat-task-state（终态信号）
- **Conditionalized**: Linear operations（`plugins.linear.enabled`）, Git branch cleanup（`plugins.git.enabled`）
- **References（按需 Read）**: `task/UNATTENDED_PROTOCOL.md`（无人值守）, `task/references/todo-sync.md`（TODO 同步契约）
