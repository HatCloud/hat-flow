---
{
  "name": "tdd",
  "description": "TDD 方法论：Full/Lite TDD 循环指令注入、RED 异常检测",
  "recommend_disable_when": [
    "纯文档/配置/SKILL.md 修改，无代码变更",
    "项目无测试框架（无 test runner 配置文件）",
    "单文件小修改（拼写、格式等）"
  ],
  "recommend_enable_when": [
    "涉及核心业务逻辑变更",
    "修改已有测试覆盖的模块"
  ],
  "hooks": {
    "P4.per-task-pre": {
      "priority": 60,
      "section": "## P4.per-task-pre",
      "on_error": "blocking"
    },
    "P4.per-task-post": {
      "priority": 20,
      "section": "## P4.per-task-post",
      "on_error": "blocking"
    }
  }
}
---

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

### 网页/UI 产物的 TDD（界面交互可测）

**TDD 不再局限于纯逻辑函数。** 对网页类产物，界面与交互行为也可纳入 TDD——用 headless 浏览器（Playwright，见 `webapp-testing` skill）把"行为/结构"写成可自动断言的测试，作为 RED/GREEN 的验证命令（Full）或验收命令（Lite）。

- **可程序断言、适合 headless TDD 的**：DOM 结构与分块、点击/hover/拖拽等交互、元素可见性与折叠展开、视图/偏好的 localStorage 持久化（reload 后仍保持）、导航后的 URL/状态、组件渲染出的节点数/属性（如 SVG 图谱节点、opacity）。
  - 典型 RED→GREEN：先写"卡片视图默认渲染为分块 / 点击 `<details>` 展开 / hover 浮窗文本无字面 `[^1]`"的 headless 断言，运行失败（RED）；实现到通过（GREEN）。
- **仍不适用 TDD、留人工复核的**：像素级视觉、配色/留白等主观美观、导出图"好不好看"。
- **与 per-task 自检结合**：Execute 阶段每完成一个较大的 UI 任务后，跑该任务对应的 headless 行为断言作为 per-task 自检（不必等到 Phase 5 才统一验证），尽早暴露交互回归。
- 前提：项目能起本地 preview（如 `astro build && astro preview` 或 dev server）供 Playwright 驱动。

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
  - **on_error: blocking** — 停止推进该 task（所有模式统一，P4 零阻塞交互，约定 9）：在 session 内可见地停下并输出异常报告——哪个 task、验证命令、RED 意外通过的初判（验收标准本就被满足 / 测试无区分度 / 实现已存在），不弹 AskUserQuestion。
  - **[Unattended]** 叠加 Telegram 通知 `[task-name] TDD RED 步骤异常：验证在实现前通过`（best-effort）。
  - 处置在 `/task` 恢复时决定：修正验收标准重跑 RED / 确认实现已存在则跳过该 task / 继续执行。
