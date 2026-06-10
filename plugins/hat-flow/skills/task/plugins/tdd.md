# TDD Plugin

## P4.per-task-pre

### TDD 循环指令注入

根据 `task-config.json` 的 `plugins.tdd.mode` 决定注入的 TDD 指令：

### Full TDD

在 subagent prompt 中注入：
```
遵循 plan.md 中的 RED/GREEN/REFACTOR 步骤：
1. RED: 先写测试，运行验证失败（测试必须失败）
2. GREEN: 实现功能，运行验证通过
3. REFACTOR: 重构代码（保持测试通过）

重要：如果 RED 步骤意外通过（验证命令在实现前就成功），立即停止并报告异常。
```

### Lite TDD

在 subagent prompt 中注入：
```
遵循 Lite TDD 流程：
1. 运行验收命令，确认当前不满足条件
2. 实现功能
3. 运行验收命令，确认满足条件
4. 重构（保持验收命令通过）
```

### None

不注入任何 TDD 指令。

### TDD Spec 注入（条件性）

若当前 task 包含 RED 步骤（Full TDD），检查项目 CLAUDE.md `## 测试配置` 是否声明了 `测试规范文件`：

```bash
grep '测试规范文件' CLAUDE.md | sed 's/.*`\(.*\)`.*/\1/'
```

若路径存在，读取该文件内容并附加到 subagent prompt：
```
The following is this project's test-writing specification. Follow it when writing or modifying test files.
```

## P4.per-task-post

### RED 异常检测

检查 task 执行结果：
- 如果 TDD mode 为 Full 且 RED 步骤意外通过（验证命令在实现前成功）：
  - **on_error: blocking** — 阻断流程
  - **[Interactive]** AskUserQuestion：验收标准是否正确？
  - **[Unattended]** 发送 Telegram 通知 `[task-name] TDD RED 步骤异常：验证在实现前通过`，暂停等待

### TDD 验证状态记录

将 TDD 执行结果记录到 timing.jsonl，经 core helper（自带顶层 `observability.enabled` 门控，关闭档 → no-op，无需 tdd 自判 observability 开关）：
```bash
hat-timing-stamp {task-folder} tdd_cycle P4 task="Task {N}" mode=full|lite red_pass=false green_pass=true
```
保留 `tdd_cycle` 事件名与 `red_pass`/`green_pass`/`mode` 字段（领域数据，非纯计时）。`red_pass`/`green_pass` 按本次实际 cycle 结果填（常态：RED 未意外通过 → `red_pass=false`，GREEN 通过 → `green_pass=true`）。该 `tdd_cycle` 与 obs 的 `task_end` 是 P4.per-task-post 上两个不同事件，各写一行、不撞名。
