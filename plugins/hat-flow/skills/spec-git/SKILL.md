---
name: spec-git
user-invocable: false
description: "Use when committing code, creating branches, writing commit messages, or when the user asks about git conventions. Covers Conventional Commits and branch naming. 触发词: \"提交规范\", \"Git 规范\", \"分支命名\", \"commit 规范\""
---

# Git Specification

通用 Git 提交和分支规范。所有项目默认遵循；项目 CLAUDE.md 中的覆盖规则优先级更高。

**Announce at start:** "Using spec-git for commit/branch conventions."

## Commit Format

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>

[optional body]
```

### Type

| type | 用途 |
|------|---------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（不改变行为） |
| `docs` | 文档 |
| `chore` | 杂务（依赖、配置） |
| `style` | 格式（不改逻辑） |
| `test` | 测试 |
| `build` | 构建 / CI |
| `merge` | 合并提交 |

### Scope

可选，用括号包裹，表示影响范围：`feat(audio): 新增 BGM 支持`

### Description

- 小写开头，结尾无句号
- 用用户配置语言写 commit 描述
- 描述意图而非操作（"修复登录时崩溃" 而非 "修改第 42 行"）

### Issue ID

如果关联了 Linear issue，在末尾追加 issue ID：
```
feat(audio): 新增 BGM 支持 (ISSUE)
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
每个 commit 对应一个逻辑变更；按文件名逐个 stage（不用 `git add -A` / `git add .`）。
Reason: 逻辑单元提交让 cherry-pick、revert 和 code review 都更干净；批量 add 有把无关改动一并纳入的风险。
</rule>

1. **逻辑单元提交** — 见上方 `<rule>`：每个 commit 对应一个逻辑变更、按文件名逐个 stage
2. **不留调试残余** — 提交前清理 `console.log` 和注释掉的代码
3. **消息可独立达意** — 仅凭 message 就能传达变更目的
4. **每个任务目标 3-8 个 commit** — 超过 10 个时考虑 squash
5. **Review 期间确认后再提交** — 用户确认修复有效后才提交

## Task Lifecycle Commit Templates

任务管理提交使用固定格式：

```
docs: add task documents [YYYY-MM-DD-topic] (HAT-XXX)
docs: complete and archive task [YYYY-MM-DD-topic] (HAT-XXX)
docs: cancel and archive task [YYYY-MM-DD-topic]
```

## Version Number Commits

iOS/Android 版本号升级：

```
build(ios): bump X.Y.Z:N
```

## Worktree Testing Flow

某些项目的原生构建/运行命令无法在 worktree 里直接跑（构建产物、本地工具链或 dev server 依赖主目录环境）。典型如 RN：`yarn ios` / `yarn android`（native build artifacts 和 Metro 依赖主目录）；其它技术栈替换为各自对应的构建/运行命令。下面第 3 步的命令仅为 RN 示例，由项目按自己的栈替换。

当 `task` Phase 4 检测到 worktree 且项目存在此类约束时，引导用户：

1. **移除 worktree**：释放任务分支
2. **在主目录切到任务分支**：`git checkout <branch-name>`
3. **测试**：跑项目的原生构建/运行命令（RN 示例：`yarn ios` / `yarn android`；其它栈替换为对应命令）
4. **修复问题**：直接在任务分支上提交修复
5. **完成**：测试通过后调用 `/task-end`

## Patterns

| 场景 | 默认做法 |
|------|---------|
| 描述变更 | 带 scope 且说明意图：`fix(auth): 防止 token 过期时崩溃`（而非 `fix: fix bug`） |
| 多文件变更 | 将逻辑相关的文件一起提交（而非每个文件一个 commit） |
| 修正刚提交的内容 | 同一会话、无中间提交时用 `git commit --amend`（而非新建 `fix: fix previous commit`） |
| 格式化 | 在功能提交前完成（而非单独的 `style: run prettier` 提交） |

## Dependencies

- **Referenced by**: task-end（Step 3.4 Archive and Commit）, task-cancel（Step 3.4）, task（Phase 4 execution）
- **Tools**: hat-git-conventions 脚本（检测项目 git 规范）
- **Related**: spec-common（CLAUDE.md 规范，互补关系）
