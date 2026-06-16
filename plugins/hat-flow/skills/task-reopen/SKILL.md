---
name: task-reopen
description: "Use when the user wants to reactivate a completed, canceled, or deferred task. Moves the task folder back to .tasks/open/, resets phases.md, and updates Linear status. 触发词: \"重新激活\", \"reopen\", \"task reopen\", \"重开任务\", \"恢复任务\""
---

# Task Reopen

将已完成/取消/推迟的任务重新移回进行中，供用户继续开发或修改。

**Announce at start:** "Using task-reopen to reactivate a task."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Write every message you show to the user in the user's configured language (the project's language preference, e.g. via `/config` or CLAUDE.md). Technical terms and code identifiers stay in their original form.

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

---

## Red Flags

| If you are thinking... | The reality is... |
|---|---|
| "Task is reopened, let me run the next phase myself" | reopen only moves the folder back and resets state. It hands off to `/task`; it never executes a phase itself. |
| "Reset every phase's checkboxes to be safe" | Only the target Phase and everything after it reset to `[ ]`. Earlier completed `[x]` stay — re-doing already-done early phases wastes work. |
| "Skip Linear update if the MCP call looks flaky" | Linear update is conditional on `plugins.linear.enabled`; when enabled, attempt it and on failure skip silently — do not silently drop it when it would have succeeded. |
| "Hardcode the In Progress state UUID, it's faster" | State must resolve via `statusMap["In Progress"]` through `get_status_map`. Hardcoded UUIDs break across workspaces. |
| "Keep the old unattended.json so it resumes unattended" | Always delete `unattended.json` on reopen. The user must re-decide unattended mode via `/task`; carrying it over auto-drives a task the user may want to drive manually. |
| "Use plain `mv` to move the folder" | Use `git mv` so the deletion from the source dir and addition to `open/` stage atomically. |

---

## TODO Sync

### Bootstrap（执行开始时）

`TaskList` 检查当前 Phase 的 step 级 task 是否存在。若不存在（session 恢复或 context compaction），从 phases.md 重建概览行 + step 级 task（已完成步骤标记 completed）。

### 执行中更新

每个步骤开始时 `TaskUpdate(status: "in_progress")`，完成时 `TaskUpdate(status: "completed")`，同步更新 phases.md。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：task-reopen 执行时任务可能尚未处于 open 状态，跳过 unattended.json 读取
2. **若文件不存在或 enabled != true**：正常交互流程（task-reopen 的预期路径）
3. **Note**：task-reopen 是人工操作，不支持全自动执行。重开后用户需通过 `/task` 决定是否启用无人值守。

> 无人值守模式的激活（unattended.json 创建）统一由 `/task` 编排器的 Step 2A.1 处理。各阶段 skill 仅负责读取已有状态。

---

### Step 1: 选择要重新激活的任务

**若 `$ARGUMENTS` 不为空**：在 `.tasks/done/`、`.tasks/canceled/`、`.tasks/deferred/` 中精确匹配任务名，找不到则告知用户。

**若 `$ARGUMENTS` 为空**：扫描上述三个目录，按修改时间逆序取前 10 个：
```bash
find .tasks/done .tasks/canceled .tasks/deferred -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while read d; do echo "$(stat -f '%m' "$d") $d"; done | sort -rn | head -10 | awk '{print $2}'
```
使用 AskUserQuestion 展示列表，让用户选择。

### Step 2: 选择重新开始的阶段

AskUserQuestion：从哪个阶段重新开始？
- **Phase 2（重新设计）** — 保留 prompt.md，重新设计
- **Phase 3（重新规划）** — 保留 design.md，重新规划
- **Phase 4（重新执行）** — 保留 plan.md，重新执行
- **Phase 5（重新测试）** — 保留代码变更，重新验证和验收
- **Phase 6（重新归档）** — 跳过所有执行，直接关闭（已验证完毕）

### Step 3: 移回 open 目录

```bash
git mv .tasks/{done|canceled|deferred}/{task-name} .tasks/open/{task-name}
```

### Step 4: 更新 phases.md

读取 `.tasks/open/{task-name}/phases.md`，将目标 Phase 及之后的所有步骤重置为 `[ ]`，Status 改为 PENDING；保留目标 Phase 之前已完成的 `[x]`。

示例（选择 Phase 4 重新执行）：
- Phase 1 Status: DONE（保留所有 [x]）
- Phase 2 Status: DONE（保留所有 [x]）
- Phase 3 Status: DONE（保留所有 [x]）
- Phase 4 所有步骤重置为 `[ ]`，Status: PENDING
- Phase 5 所有步骤重置为 `[ ]`，Status: PENDING
- Phase 6 所有步骤重置为 `[ ]`，Status: PENDING

更新 `**Updated**: {今日日期 HH:MM}`。

### Step 5: 删除旧的 unattended.json

```bash
rm -f .tasks/open/{task-name}/unattended.json
```

重开后由用户重新决定是否启用无人值守。

### Step 6: 更新 Linear 状态（条件）

读取 `{task-folder}/task-config.json`，检查 `plugins.linear.enabled`。

- 为 true 且 `linear.json` 存在 → 按 `plugins/linear.md` 规范更新状态为 In Progress（`state` 取 `linear.json.statusMap["In Progress"]`，经 get_status_map 解析，无硬编码 UUID）
- 为 false 或 `linear.json` 不存在 → 跳过

失败时跳过（不中止 reopen 流程）。

### Step 6.5: 保留 task-config.json

reopen 后 task-config.json 保留。用户可在 P2 Step 2e 重新配置。

### Step 7: Commit

```bash
git add .tasks/open/{task-name}/
git commit -m "docs: reopen task [{task-name}]"
```

### Step 8: 通知用户

告知用户：
- 任务已重新激活：`.tasks/open/{task-name}/`
- 将从 Phase N 开始
- 请调用 `/task` 继续（不自动执行）

---

## Dependencies

- **Reads**: `{task-folder}/task-config.json`, `{task-folder}/linear.json`（若存在）
- **Writes**: `{task-folder}/phases.md`（重置步骤状态）
- **Deletes**: `{task-folder}/unattended.json`（若存在）
- **Conditionalized**: Linear update（`plugins.linear.enabled`）
