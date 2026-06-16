# Task Init Skill

## 目的

Phase 1（Setup）阶段 skill。处理新任务的初始化工作：git 分支设置、任务文件夹创建、Linear 集成、需求确认。

## 触发条件

- 通过 `/task` 编排器自动调用（新任务时）
- 直接调用 `/task-init`（手动初始化）

## 核心职责

1. 检查是否有现有任务
2. 解析用户输入（Linear prompt / Issue ID / 自由描述）
3. 确认需求理解（结构化复述 + 澄清问题）
4. 设置 git 分支
5. 处理 Linear 上下文
6. 创建任务文件夹 + prompt.md + **phases.md**

## phases.md

任务文件夹中的状态文件。记录所有阶段的颗粒度 todo 列表，支持跨 session 恢复：
- 每步完成后标记 `[x]`
- Phase 1 完成后 `**Status**: DONE`
- `/task` 编排器读取此文件决定从哪个阶段继续

## 关键规则

- 分支创建必须经用户 AskUserQuestion 确认
- 所有文件写入在分支设置完成后才执行
- NO_GIT 模式下自动跳过所有 git 操作

## 产物

- `.tasks/open/YYYY-MM-DD-topic/phases.md`
- `.tasks/open/YYYY-MM-DD-topic/prompt.md`
- `.tasks/open/YYYY-MM-DD-topic/linear.json`（如果有 Linear 集成）
