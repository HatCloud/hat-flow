# task-end

## 目的

任务完成后的生命周期关闭流程。确保每个任务都有完整的收尾记录，包括完成报告、变更日志、Linear 同步和文件归档。

## 触发条件

用户确认任务已完成且测试通过时使用。常见触发词：结束任务、任务完成、关闭任务、归档任务。

## 核心流程

1. **机械验证** — 运行项目配置的验证命令，不依赖口头确认。通过 `.last-verified` 文件和 commit hash 比对避免重复验证
2. **识别任务** — 通过脚本或 Glob 检测 `.tasks/open/` 中的活跃任务
3. **技术债务检查** — 回顾任务期间是否产生了变通方案或已知未修复问题
4. **编写 final.md** — 包含完成内容、遇到的问题、偏差分析、验证结果、变更日志条目
5. **流程回顾** — 由 retrospective plugin 的 `P6.post-archive` hook 驱动（hook 输出的 retrospective 段执行流程审查）
6. **关闭活动** — Linear 状态同步、changelog 更新、CLAUDE.md 更新、pre-commit 安全检查、归档提交、分支处理

## 关键规则

- 验证命令必须实际运行，不能仅凭用户口头确认跳过
- 关闭提交中只包含文档变更，代码变更必须单独处理
- final.md 是唯一的完成记录，必须详尽
- Linear 子 issue 需要逐个确认状态

## 强制停止点

共 9 个用户决策点（验证命令配置、验证失败、多任务选择、技术债务、流程改进、子 issue 处理、CLAUDE.md 更新、意外代码变更、分支合并）。每个停止点必须使用 AskUserQuestion 等待用户确认。

## 依赖

- 引用：task-config.json
- Hook：P6.pre-archive/post-archive（P6 phase_start/phase_end 已下沉为 core timing 内联、非 hook——ISSUE）
- 脚本：hat-task-detect、hat-task-archive、hat-plugin-hook、hat-conversation-export
