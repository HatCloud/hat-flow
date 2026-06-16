# Changelog

> 最新在最上。

## 2026-06-17 Step 1.5 债务对账 A3 留痕 (M3)

- Step 1.5 [Unattended] 债务对账按 `degrade_policy`：conservative/headless 额外把自动关闭动作 + 低置信疑似项汇总写 unattended-decisions.md `## Headless Degraded Decisions` + final.md P6 引用；standard/缺省维持原行为。见 UNATTENDED_PROTOCOL §9 A3。

## 2026-06-17 Worktree Teardown 3.4.4 (M2)

- 新增 `3.4.4 Worktree Teardown`（核心，仅 worktree 任务）：检测 linked worktree（`--git-dir != --git-common-dir`）；归档后先 `cp -R` 任务文件夹回主仓库 + 删 stub（防 untracked `.tasks/` 随 worktree 删除而丢记录），`ExitWorktree(keep)` 回主目录，按 `end_decisions.branch` auto_merge（`git merge --no-ff` + `git worktree remove` + `git branch -d`）/ keep（登记 unmerged-branches.md）；PR/Discard 永不自动。回主目录后 3.5 git-plugin 分支处理自然 no-op，不重复。
- `<rule>`：merge 前必先物理拷贝 + ExitWorktree(keep)；未 merge 不强删 worktree（HARD-STOP 类）。

## 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 修正悬空引用：删除 PROCESS_REVIEW_TEMPLATE / Part A 引用（文件不存在），改述为 P6.post-archive 的 hook 驱动 retrospective。
  - 去冗余：「phases.md Phase 6 DONE + P6 phase_end 必须在归档 commit 之前」原三处重述，保留 Step 3.3.4 的权威 `<rule>`，其余两处改单行交叉引用。
