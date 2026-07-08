---
name: task-reopen
description: "Use when the user wants to reactivate a completed, canceled, or deferred task. Do NOT use for tasks still open. 触发词: \"重新激活\", \"reopen\", \"task reopen\", \"重开任务\", \"恢复任务\""
---

# Task Reopen

将已完成/取消/推迟的任务重新移回进行中，供用户继续开发或修改。

工具落点按 `${CLAUDE_PLUGIN_ROOT}/skills/task/references/harness-tools.md` 映射。

**Announce at start:** "Using task-reopen to reactivate a task."

## Runtime Context

- Tasks: !`hat-task-detect .tasks 2>/dev/null || echo '{"open":[]}'`
- Branch: !`git branch --show-current 2>/dev/null || echo 'NO_GIT'`
- User input: $ARGUMENTS

---

## TODO Sync

按 `config.todo_sync` 档（`off | overview | full`），依 `task/references/todo-sync.md` 的触发点表 + 4 命名模板执行（该文件为唯一权威，本 section 不重述契约）。

本 skill 触发点：**overview 复活**——`full`/`overview` 将 overview 由 `completed` 改回 `in_progress` + 符号回退到重开的 phase；`full` 重建该 phase step；`off` no-op。

---

## Process

### Unattended State（每次执行时加载）

1. **读取状态**：执行 task-reopen 时任务可能尚未处于 open 状态，因此跳过 unattended.json 读取
2. **文件不存在或 enabled != true**：走正常交互流程（task-reopen 的预期路径）
3. **执行模式**：task-reopen 是人工操作，全自动执行不可用；重开后由用户通过 `/task` 决定是否启用无人值守

> 无人值守的激活入口与契约（quiet / 交互主入口 / 后备入口、activate_after 与 declined 语义）见 UNATTENDED_PROTOCOL.md §5。各阶段 skill 只读取已有状态。

---

### Step 1: 选择要重新激活的任务

**若 `$ARGUMENTS` 不为空**：在 `.tasks/done/`、`.tasks/canceled/`、`.tasks/deferred/` 中精确匹配任务名，找不到则告知用户。

**若 `$ARGUMENTS` 为空**：扫描上述三个目录，按修改时间逆序取前 10 个：
```bash
find .tasks/done .tasks/canceled .tasks/deferred -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while read d; do echo "$(stat -f '%m' "$d") $d"; done | sort -rn | head -10 | awk '{print $2}'
```
使用 向用户提问（结构化选项优先） 展示列表，让用户选择。

### Step 2: 选择重新开始的阶段

向用户提问（结构化选项优先）：从哪个阶段重新开始？
- **Phase 2（重新设计）** — 保留 prompt.md，重新设计
- **Phase 3（重新规划）** — 保留 design.md，重新规划
- **Phase 4（重新执行）** — 保留 plan.md，重新执行
- **Phase 5（重新测试）** — 保留代码变更，重新验证和验收
- **Phase 6（重新归档）** — 跳过所有执行，直接关闭（已验证完毕）

### Step 3: 移回 open 目录

```bash
git mv .tasks/{done|canceled|deferred}/{task-name} .tasks/open/{task-name}
```

此处用 `git mv` 而非 `mv`，使源目录的删除与 `open/` 的新增原子暂存到同一变更。

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

- 为 true 且 `linear.json` 存在 → 按 `plugins/linear.md` 规范更新状态为 In Progress（`state` 取 `linear.json.statusMap["In Progress"]`，经 get_status_map 解析；UUID 不硬编码）
- 为 false 或 `linear.json` 不存在 → 跳过

Linear 更新失败时跳过该步，reopen 流程继续。

### Step 7: 保留 task-config.json

reopen 后 task-config.json 保留。用户可在 P2 Step 2e 重新配置。

### Step 8: Commit

```bash
git add .tasks/open/{task-name}/
git commit -m "docs: reopen task [{task-name}]"
```

### Step 9: 通知用户

告知用户：
- 任务已重新激活：`.tasks/open/{task-name}/`
- 将从 Phase N 开始
- 调用 `/task` 继续；reopen 后不自动进入执行

---

## Dependencies

- **Reads**: `{task-folder}/task-config.json`, `{task-folder}/linear.json`（若存在）
- **Writes**: `{task-folder}/phases.md`（重置步骤状态）
- **Deletes**: `{task-folder}/unattended.json`（若存在）
- **Conditionalized**: Linear update（`plugins.linear.enabled`）
