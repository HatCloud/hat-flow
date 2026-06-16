# task-init 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-06-17 1d-wt Worktree 物理隔离创建 (M2)

- 新增 `1d-wt. Worktree Isolation`：读 `branch.worktree`（true/false/"ask"），交互模式 "ask" 追加询问；启用时 `git worktree add -b task/<folder> <path> HEAD`（主目录 HEAD 不动）+ 内置 `EnterWorktree(path=)` 切入；`<rule>` 禁止主目录 `git checkout -b`。
- 1f：worktree 启用时经绝对路径 `$MAIN_ROOT` 写主仓库 stub 指针 `.tasks/open/<folder>/.worktree`（跨 session 恢复用）。NO_GIT 跳过 1d-wt。

## 2026-06-17 三层配置合并 + 无头物化 + 分支默认 keep (M1)

- 1b.3 第 5 步改为调用 `hat-task-config-resolve`（默认模板 ① < 全局 local ② < 项目本地 ③ < 调用 flag ④ 深合并 + `branch.worktree` "ask" 哨兵按 quiet 解析），替代原「读 preset 模板深合并」substep；保留裁剪覆盖与 auto 解析。
- 1d 分支决策：读 effective config `branch.mode`（默认 **keep** = 留当前分支，支持同目录多 task 协作）；Iron Law 加 quiet/unattended 例外（按 config 不询问）；worktree 物理隔离与交互追问拆到 `1d-wt`（M2）。
- 1f：quiet_mode 时物化 `task-config.json` 顶层 `_source:"headless"` + 直接写 `unattended.json`（`enabled:true, activate_after:now, degrade_policy, end_decisions`），使 Init 后全程无人值守。
- Dependencies 增 `hat-task-config-resolve` 脚本、`unattended.json` 写、三层配置读源。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Bilingual Strategy / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **SKILL.md 补 Red Flags 表**：预判 init 阶段越界探索 / 跳过需求确认 / 自动建分支 / 跳过 tier 确认等合理化失败模式（全英文，符合双语策略）。
3. **README.md 去掉「worktree」措辞**：SKILL.md 1d 实为 `git checkout -b`，无 worktree。「设置 git 分支或 worktree」改为「设置 git 分支」。
4. **双语：中文章节标题改英文**——`### 1b.3 档位粗选` → `### 1b.3 Tier Pre-Selection`；`### 1b.4 Debt 关联检查（轻量）` → `### 1b.4 Debt Linkage Check (Lightweight)`，与同文件其余英文标题统一（Resume Support 中文对照行保持不变）。
