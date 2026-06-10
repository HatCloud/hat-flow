# task-reopen

将已完成、取消或推迟的任务重新移回 `.tasks/open/`，重置 phases.md 到指定阶段，并同步 Linear 状态。

## 触发词

`reopen`、`重新激活`、`重开任务`、`恢复任务`

## 行为

1. 定位任务文件夹（done / canceled / deferred）
2. 移回 `.tasks/open/`
3. 重置 phases.md 到指定阶段
4. 更新 Linear issue 状态（如有关联）
