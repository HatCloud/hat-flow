# task-cancel

## 目的

任务取消或推迟时的生命周期关闭流程。记录原因、处理代码清理、同步 Linear 状态、归档任务文件夹。

## 触发条件

用户决定放弃或推迟进行中的任务时使用。常见触发词：取消任务、放弃任务、推迟任务。

## 核心流程

1. **识别任务** — 检测活跃任务，确认取消/推迟意图，收集原因
2. **确定处置方式** — 永久取消（归档到 `canceled/`）或推迟（归档到 `deferred/`），两者在代码处理和 Linear 状态上有本质区别
3. **评估已完成工作** — 检查实现进展，用户决定代码去留（保留/丢弃/部分保留）
4. **执行清理**：
   - Linear 同步（状态更新 + 评论 + 子 issue 处理）
   - 代码变更处理（含 worktree 清理）
   - 切换到 main 分支编写文档
   - 编写 final.md（取消报告或推迟报告）
   - 流程回顾讨论
   - 归档提交
   - 处理 feature 分支

## 关键区别：取消 vs 推迟

| 维度 | 取消 | 推迟 |
|------|------|------|
| 归档目录 | `canceled/` | `deferred/` |
| Linear 状态 | Canceled | Backlog |
| 子 issue | 需要逐个处理 | 保留不动 |
| 代码默认 | 用户选择 | 默认保留 |
| final.md 模板 | Cancellation Report | Deferral Report（含 Resume Notes） |

## 强制停止点

共 7 个用户决策点（多任务选择、取消原因、处置方式、代码处理、子 issue、流程改进、分支处理）。每个停止点必须使用 AskUserQuestion 等待用户确认。

## 依赖

- 引用：PROCESS_REVIEW_TEMPLATE.md、plugins/linear.md（通过 task-config.json 条件化）
- 引用：spec-git（commit 规范）
- 脚本：hat-task-detect、hat-task-archive
