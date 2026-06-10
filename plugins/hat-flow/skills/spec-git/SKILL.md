---
name: spec-git
description: "Use when committing code, creating branches, writing commit messages, or when the user asks about git conventions. Covers Conventional Commits and branch naming. 触发词: \"提交规范\", \"Git 规范\", \"分支命名\", \"commit 规范\""
---

# Git Specification

通用 Git 提交和分支规范。所有项目默认遵循；项目 CLAUDE.md 中的覆盖规则优先级更高。

**Announce at start:** "Using spec-git for commit/branch conventions."

**LANGUAGE RULE — strictly enforced, no exceptions:**
Every message you show to the user MUST be written in Chinese (中文).
This includes status updates, analysis results, questions, error reports, and summaries.
Technical terms and code identifiers stay in English.
Do NOT write English sentences like "Let me check..." or "Based on my analysis...".
Write "让我检查..." or "分析结果如下..." instead.

## Commit Format

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>

[optional body]
```

### Type

| type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Refactor (no behavior change) |
| `docs` | Documentation |
| `chore` | Maintenance (dependencies, config) |
| `style` | Formatting (no logic change) |
| `test` | Tests |
| `build` | Build/CI |

### Scope

可选，用括号包裹，表示影响范围：`feat(audio): add BGM support`

### Description

- 小写开头，结尾无句号
- 用用户配置语言写 commit 描述
- 描述意图而非操作（"修复登录时崩溃" 而非 "修改第 42 行"）

### Issue ID

如果关联了 Linear issue，在末尾追加 issue ID：
```
feat(audio): add BGM support (ISSUE)
```

## Branch Naming

```
main                              ← 主分支
feature/<issue-id>-<description>  ← 功能分支 (feature/ISSUE-add-login)
fix/<issue-id>-<description>      ← 修复分支
hotfix/<description>              ← 热修复
```

## Commit Discipline

<rule>
Each commit must correspond to one logical change. Never use `git add -A` or `git add .` — add specific files by name.
Reason: logical unit commits enable clean cherry-picks, reverts, and code review. Bulk adds risk including unrelated changes.
</rule>

1. **Logical unit commits** — 每次提交对应一个逻辑变更，而非按文件提交
2. **No debug leftovers** — 提交前清理 `console.log` 和注释掉的代码
3. **Meaningful messages** — 仅凭 message 就能传达变更目的
4. **Target 3-8 commits/task** — 超过 10 个考虑 squash
5. **Don't commit formatting separately** — 在功能提交前格式化，不要单独创建 `style: format` 提交
6. **Confirm before committing during review** — 用户确认修复有效后才提交

## Task Lifecycle Commit Templates

任务管理提交使用固定格式：

```
docs: 添加任务文档 [YYYY-MM-DD-topic] (HAT-XXX)
docs: 完成并归档任务 [YYYY-MM-DD-topic] (HAT-XXX)
docs: 取消并归档任务 [YYYY-MM-DD-topic]
```

## Version Number Commits

iOS/Android 版本号升级：

```
build(ios): bump X.Y.Z:N
```

## Worktree Testing Flow

Worktree 无法直接运行 `yarn ios` / `yarn android`（native build artifacts 和 Metro 依赖主目录环境）。

当 `task` Phase 4 检测到 worktree 时，引导用户：

1. **Remove worktree**：释放任务分支
2. **Switch to task branch in main directory**：`git checkout <branch-name>`
3. **Test**：`yarn ios` / `yarn android`
4. **Fix issues**：直接在任务分支上提交修复
5. **Complete**：测试通过后调用 `/task-end`

## Common Mistakes

| Mistake | Correct Approach |
|---------|-----------------|
| `fix: fix bug` | `fix(auth): prevent crash when token expires` |
| 每个文件一个 commit | 将逻辑相关的文件一起提交 |
| 发现问题后创建 `fix: fix previous commit` | `git commit --amend`（同一会话，无中间提交） |
| 独立的 `style: run prettier` 提交 | 在功能提交前格式化 |

## Dependencies

- **Referenced by**: task-end（Step 3.4 Archive and Commit）, task-cancel（Step 3.4）, task（Phase 4 execution）
- **Tools**: hat-git-conventions 脚本（检测项目 git 规范）
- **Related**: spec-common（CLAUDE.md 规范，互补关系）
