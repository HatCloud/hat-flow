# 任务文档路径占位符规范

## 占位符定义

**`任务文档`** 是当前任务文件夹根目录的占位符。

消解原因：任务文件夹在任务生命周期中处于三态（`open/`、`done/`、归档），worktree 隔离时还有额外路径层级，绝对路径在归档或清理 worktree 后即失效。

## 语法

```
任务文档/<relative_path>
```

示例：
- `任务文档/design.md`
- `任务文档/plan.md`
- `任务文档/doc/reports/research-report.md`

## 适用场景

任务文档内引用**当前任务**的其他文件（例：final.md 引用 design.md、doc/reports/ 下的报告等）。

## 不适用场景

- **工具路径**：SKILL.md 中引用工具脚本的路径（如 `bin/hat-task-archive`），由 `hat-task-package` 按自己的路径规则处理，不使用此占位符
- **跨任务引用**：引用其他任务的文档应改用任务名 slug 或摘要描述（如"见 2026-06-17-todo-sync-research 的 final.md"），而非占位符
- **`docs/` 目录下的文档**：已有相对路径约定，遵循原有写法（相对路径或直接文件名），不受占位符约束

## 正确写法

任务内引用一律走占位符，不写绝对路径——绝对路径在归档或清理 worktree 后即失效。

```
# 绝对路径（即使当下有效，归档后失效）
~/.claude/.claude/worktrees/2026-06-17-task-doc-placeholder-review/.tasks/open/2026-06-17-task-doc-placeholder-review/design.md
/Users/hat_cloud/.claude/.claude/.tasks/done/2026-06-17-task/plan.md

# 占位符（推荐）
任务文档/design.md
任务文档/plan.md
```

