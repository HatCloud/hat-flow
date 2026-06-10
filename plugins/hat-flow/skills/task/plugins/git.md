# Git Plugin

> **关于交互（spec-task-skill 约定 9 Interaction Front-Loading）**：本插件仅 **P4.per-task-post 为零阻塞交互**（commit 自动、不弹确认）。P1.phase-start 的 dirty 处理与 P6.post-archive 的分支菜单**保留 AskUserQuestion**——它们分属 Init / End 决策点，受约定 9 豁免（Init 集中收集决策、P5-P6 自然决策点）。修改时勿误把 P1/P6 的交互当作违反 P4 零交互。

## P1.phase-start

### Git 规范 + Dirty File 检查

1. 运行 `git status --porcelain` 检查工作目录状态
2. 如有未提交的变更：
   - **[Interactive]** AskUserQuestion：stash / commit / 继续（可能混入无关变更）
   - **[Unattended]** 忽略继续（不 stash、不 commit）——与 `UNATTENDED_PROTOCOL.md §6` 一致；安全靠后续 commit-checkpoint「仅 add 指定文件范围」承接
3. 确认当前分支名和 git 规范（Conventional Commits 等）

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

     > **残留风险（HAT-437）**：删暂存支柱后，「仅 add 指定文件范围」是唯一兜底——Unattended 下工作区可能留无关变更。故 **plan task 必须列具体文件**（非目录/glob），否则同一文件内混入的无关 hunk 仍会被 `git add <file>` 整体带入。
  5. 提交节奏 / 是否需用户确认提交，**前置到 Design/Plan 一次性决定**（spec-task-skill 约定 9 Interaction Front-Loading：Execute 零阻塞交互）。
- **无 Checkpoint**：跳过，继续下一 task

### 8 条 Commit 规则

1. **Follow project conventions** — Conventional Commits、Angular style 等
2. **Commit by logical unit, not by file** — 相关变更归为一个 commit
3. **No fix commits within the same session** — amend 原始 commit，除非中间有其他 commit
4. **Reference issue ID** — 如 `feat(audio): add BGM support (HAT-106)`
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

> **仅在非 main 分支时触发分支菜单**；已在 main（或 NO_GIT）时跳过分支处理，直接做 tag / 归档清理。前置：归档前验证已通过（task-end Step 0）。

1. **分支处理（4 选项菜单，参考 finishing-a-development-branch 范式，不导入该 skill）**：
   - **[Interactive]** AskUserQuestion，4 选项：
     - **Merge locally** — `git checkout main && git merge --no-ff {branch} && git branch -d {branch}`
     - **Push + Create PR** — `git push -u origin {branch}` + `gh pr create`，**保留分支**（供 PR 反馈迭代）
     - **Keep as-is** — 保留分支不动。**提示「该分支尚未并入 main」** + 追加一行到 `docs/unmerged-branches.md`（列：分支名 / task / 日期 / 备注；文件不存在则先建表头再追加），供日后对账合并（HAT-439）
     - **Discard** — 需用户 **typed 确认**（输入分支名）后 `git checkout main && git branch -D {branch}`（force 删，丢弃未合并工作）
   - **[Unattended]** 按 `unattended.json` 的 `end_decisions.branch` 映射：`auto_merge` → Merge locally；`keep` → Keep as-is（**仅追加 `docs/unmerged-branches.md` 登记、不提示**）；**`PR` / `Discard` 永不自动触发**（无人值守下跳过——不 push、不 force 删）；字段缺失或非法值 → 默认 **Keep as-is**（安全保守，同样登记）
2. 清理 revise tag（如 `revise-r1-start` 等临时 tag）
3. 旧任务归档目录中的 `.tasks/archive/done/` 清理（保留最近 10 个）
