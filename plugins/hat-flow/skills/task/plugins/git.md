# Git Plugin

> **关于交互（spec-task-skill 约定 9 Interaction Front-Loading）**：本插件仅 **P4.per-task-post 为零阻塞交互**（commit 自动、不弹确认）。P1.phase-start 的 dirty 处理与 P6.post-archive 的分支菜单**保留 AskUserQuestion**——它们分属 Init / End 决策点，受约定 9 豁免（Init 集中收集决策、P5-P6 自然决策点）。修改时勿误把 P1/P6 的交互当作违反 P4 零交互。

## P1.phase-start

### Git 规范 + Dirty File 检查

1. 运行 `git status --porcelain` 检查工作目录状态
2. 如有未提交的变更：
   - **[Interactive]** AskUserQuestion：stash / commit / 继续（可能混入无关变更）
   - **[Unattended]** 忽略继续（不 stash、不 commit）——与 `UNATTENDED_PROTOCOL.md §6` 一致；安全靠后续 commit-checkpoint「仅 add 指定文件范围」承接
3. 确认当前分支名和 git 规范（Conventional Commits 等）
4. **记录 base_ref（供 End 阶段 squash 用）**：把任务开始时的 HEAD 写入 `{task-folder}/.git-base-ref`，作为「本任务在 main 上连续提交段」的起点（仅在本任务尚未产生提交时记录；文件已存在则不覆盖）。NO_GIT 跳过。
   ```bash
   [ -f "{task-folder}/.git-base-ref" ] || git rev-parse HEAD > "{task-folder}/.git-base-ref"
   ```

## P3.phase-end

### 提交任务文档

将 Phase 1-3 生成的任务文档提交到 git：

1. `git add` 以下文件（存在时）：
   - `{task-folder}/prompt.md`
   - `{task-folder}/design.md`
   - `{task-folder}/plan.md`
   - `{task-folder}/linear.json`（linear 启用时）
   - `{task-folder}/phases.md`
   - `{task-folder}/task-config.json`
2. Commit message: `docs(task): add task documents for {task-name} [{issue-id}]`
3. 不提交 `.tasks/` 以外的文件

## P4.per-task-post/formatter

### Formatter 清理

如果 formatter 不由 git hook 管理（检查 `.husky/` 或 `.git/hooks/pre-commit`），在 `git add` 前运行格式化命令。

决策树：
```
hookManaged: true   → 不做任何事
hookManaged: false  → formatter 存在？ → 是：运行 formatCommand
                                       → 否：跳过
```

不创建独立的 `style: format` commit。

## P4.per-task-post/commit-checkpoint

### Commit Checkpoint 处理

检查 plan.md 当前 task 的 `### Verification` 之后是否紧跟 `### ✔ Commit Checkpoint M`：

- **有 Checkpoint**：
  1. 解析 commit message（在该小节首行 backticks 中）
  2. `git status --porcelain` 收集本 Checkpoint 覆盖的 task 范围对应的源码改动
  3. **不含** `.tasks/` 下的变更（任务文件夹的提交统一由 P3 init commit 和 P6 closure commit 处理）
  4. **所有模式（含 Interactive）直接 commit**：按 plan checkpoint 的 message + 上述限定的文件范围自动 `git add <specific-files> && git commit`，**不弹确认**。安全职责由「仅 add 指定文件范围 + 排除 `.tasks/` 外无关变更」承接（不再依赖此前 P1 阶段的暂存支柱——Unattended dirty 已统一为忽略继续），非裸 `git add -A`。

     > **残留风险（ISSUE）**：删暂存支柱后，「仅 add 指定文件范围」是唯一兜底——Unattended 下工作区可能留无关变更。故 **plan task 必须列具体文件**（非目录/glob），否则同一文件内混入的无关 hunk 仍会被 `git add <file>` 整体带入。
  5. 提交节奏 / 是否需用户确认提交，**前置到 Design/Plan 一次性决定**（spec-task-skill 约定 9 Interaction Front-Loading：Execute 零阻塞交互）。
- **无 Checkpoint**：跳过，继续下一 task

### 8 条 Commit 规则

1. **Follow project conventions** — Conventional Commits、Angular style 等
2. **Commit by logical unit, not by file** — 相关变更归为一个 commit
3. **No fix commits within the same session** — amend 原始 commit，除非中间有其他 commit
4. **Reference issue ID** — 如 `feat(audio): add BGM support (ISSUE)`
5. **Write meaningful messages** — 描述"为什么"和"做了什么"
6. **Target 3-8 commits per task** — Phase 4 典型 3-5 个 commit
7. **Confirm before committing during test phase** — 分析→修复→用户测试→确认→commit
8. **Format before commit (conditional)** — 见上方 Formatter 清理

### Common Anti-Patterns

| Anti-pattern | Problem |
|---|---|
| One commit per file | Breaks logical units |
| Leaving debug/console.log | Pollutes history |
| Committing during review without confirmation | Unverified fixes |
| Messages like "fix" or "update" | Cannot understand intent |
| Separate formatting commits | Should format before feature commit |

## P6.pre-archive

### Pre-commit 安全检查

归档前确认：
1. 所有变更已提交（`git status --porcelain` 为空或仅有 `.tasks/` 变更）
2. 当前分支与预期分支一致
3. 无未解决的 merge conflict

## P6.post-archive

### 分支处理 + Tag 清理

> **非 main 分支 → 触发分支菜单（含 squash 合并）**；**已在 main（或 NO_GIT）→ 跳过分支菜单**，但仍按 `end_decisions.squash` 尝试压缩本任务在 main 上的连续提交段（见第 1.5 步）。前置：归档前验证已通过（task-end Step 0）。worktree 隔离任务的分支处理已由 task-end **Step 3.4.4**（core teardown）完成、此时已回到 main，故本菜单对其自然 no-op。

**读取 `end_decisions.squash`**（来自 `unattended.json` 的 `end_decisions.squash`，或交互模式取 effective config `end_decisions.squash`；缺省 `true`）。

1. **分支处理（4 选项菜单，参考 finishing-a-development-branch 范式，不导入该 skill）**：
   - **[Interactive]** AskUserQuestion，4 选项：
     - **Merge locally** — `git checkout main` 后按 squash 开关合并：
       - `squash == true`（缺省）→ `git merge --squash {branch} && git commit -m "{conventional msg} [{task}]"`（把分支全部改动压成单 commit）+ `git branch -D {branch}`（squash 后 git 不视为已合并，用 `-D`）
       - `squash == false` → `git merge --no-ff {branch} && git branch -d {branch}`
     - **Push + Create PR** — `git push -u origin {branch}` + `gh pr create`，**保留分支**（供 PR 反馈迭代；PR 场景不本地 squash，留给 PR squash-merge）
     - **Keep as-is** — 保留分支不动。**提示「该分支尚未并入 main」** + 追加一行到 `docs/unmerged-branches.md`（列：分支名 / task / 日期 / 备注；文件不存在则先建表头再追加），供日后对账合并（ISSUE）
     - **Discard** — 需用户 **typed 确认**（输入分支名）后 `git checkout main && git branch -D {branch}`（force 删，丢弃未合并工作）
   - **[Unattended]** 按 `unattended.json` 的 `end_decisions.branch` 映射：`auto_merge` → Merge locally（同样按 squash 开关选 `--squash`/`--no-ff`）；`keep` → Keep as-is（**仅追加 `docs/unmerged-branches.md` 登记、不提示**）；**`PR` / `Discard` 永不自动触发**（无人值守下跳过——不 push、不 force 删）；字段缺失或非法值 → 默认 **Keep as-is**（安全保守，同样登记）
1.5. **main 连续提交段 squash（已在 main、无任务分支/worktree 时）**：当 `squash == true` 且本任务直接在 main 上工作时，把本任务从 `base_ref` 到 HEAD 的连续提交压缩为一个。读 `base=$(cat {task-folder}/.git-base-ref 2>/dev/null)`。**仅当下列守卫全部通过才执行**，任一不过则**保守跳过**（不改写历史）并在 final.md `## Verification` 记一行原因：
   - `base` 非空、且是 HEAD 的祖先（`git merge-base --is-ancestor $base HEAD`）；
   - 提交数 `N = git rev-list --count $base..HEAD` ≥ 2（N≤1 无需压缩）；
   - 区间无 merge commit（`git rev-list --merges $base..HEAD` 为空）；
   - 区间提交**全部未推送**（`git rev-list $base..HEAD --remotes | wc -l` 为 0）——已推送绝不改写；
   - **未被打断**：`.tasks/open/` 下只有本任务（无并发的其它 open task），作为「无其它需求插入提交」的保守代理。
   - 通过 → `git reset --soft $base && git commit -m "{conventional msg 概括本任务} [{task}]"`（保留全部文件改动，仅压历史）。
   ```bash
   base=$(cat "{task-folder}/.git-base-ref" 2>/dev/null)
   if [ -n "$base" ] && git merge-base --is-ancestor "$base" HEAD 2>/dev/null \
      && [ "$(git rev-list --count "$base"..HEAD)" -ge 2 ] \
      && [ -z "$(git rev-list --merges "$base"..HEAD)" ] \
      && [ "$(git rev-list "$base"..HEAD --remotes | wc -l | tr -d ' ')" = 0 ] \
      && [ "$(find .tasks/open -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" -le 1 ]; then
       git reset --soft "$base" && git commit -m "<msg> [{task}]"
   fi
   ```
2. 清理 revise tag（如 `revise-r1-start` 等临时 tag）
3. 旧任务归档目录中的 `.tasks/archive/done/` 清理（保留最近 10 个）

<rule>
The on-main squash (step 1.5) MUST skip — never rewrite history — whenever any guard is uncertain: no recorded base_ref, base not an ancestor of HEAD, a merge commit in range, any commit already pushed to a remote, or more than one open task. When skipping, record the reason in final.md; do NOT `git reset` on doubt.
Reason: squashing rewrites main's commit history. Rewriting a pushed commit corrupts shared history; folding a concurrent task's commit into this one mislabels someone else's work. The "其他需求插入的提交打断则不压缩" intent demands erring toward NOT squashing — a missed squash is harmless, a wrong rewrite is not. The guards (unpushed + single open task + no merges) make the range provably this task's local work before any reset.
</rule>
