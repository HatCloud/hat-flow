# Git Specification

通用 Git 提交和分支命名规范，所有项目默认遵循。

## 触发方式

提交代码、创建分支、写 commit message 时自动加载。用户问"提交规范"、"Git 规范"等也会触发。

## 核心内容

### Commit 格式
采用 Conventional Commits：`<type>(<scope>): <description>`
- type：feat / fix / refactor / docs / chore / style / test / build
- scope：可选，表示影响范围
- description：中文，小写开头，描述意图而非操作
- 关联 Linear issue 时在末尾追加 issue ID

### 分支命名
- `feature/<issue-id>-<description>` — 功能分支
- `fix/<issue-id>-<description>` — 修复分支
- `hotfix/<description>` — 热修复

### Commit Discipline
- 每次提交对应一个逻辑变更
- 提交前清理调试代码
- 目标每个任务 3-8 个 commit
- 不单独提交格式化
- Review 期间确认后才提交

### 任务生命周期模板
固定格式的 docs 类型提交，用于任务创建、完成、取消。

### Worktree 测试流程
Worktree 无法直接运行 native build，需回到主目录测试。
