# Linear Plugin

## P1.phase-end

### Linear Issue 创建/关联

根据用户输入决定 Linear 操作：

### Path 1: Linear Prompt (XML Format)

用户粘贴 `<issue identifier="PROJ-123">...</issue>` XML：
- 解析 XML 提取 `issueId`、`issueUrl`
- `mcp__linear__get_issue({ id: "PROJ-123" })` 获取 `issueUuid`
- 写入 `{task-folder}/linear.json`

### Path 2: Issue ID Direct Input

用户提供标识符如 `PROJ-123`：
- `mcp__linear__get_issue({ id: "PROJ-123" })` 获取完整信息
- 写入 `{task-folder}/linear.json`

### Path 3: No Linear Context

- **[Interactive]** AskUserQuestion：创建新 issue / 跳过 Linear
- **[Unattended]** 创建新 issue

创建 issue（team/project 标识来自项目 `CLAUDE.md ## Linear 配置`）：
```
mcp__linear__create_issue({
  teamId: "<CLAUDE.md ## Linear 配置 的 Team id>",
  title: "任务标题",
  description: "描述",
  projectId: "<CLAUDE.md ## Linear 配置 的 Project id>"
})
```

### 状态解析（get_status_map，无硬编码 UUID）

各状态的 UUID 随 workspace 而异，**不内嵌任何固定值**——运行时按 name 动态解析并缓存：

1. 确定 team 后（来自 `CLAUDE.md ## Linear 配置`），调用 `mcp__linear__get_status_map({ teamId: "<team id>" })`（或按 team key），返回该 team 的 status `name → UUID` 映射。
2. 将映射缓存到 `{task-folder}/linear.json` 的 `statusMap` 字段（首次创建/关联 issue 时写入），后续各 phase 按 **name** 索引（大小写不敏感容错）。
3. 所有状态更新引用 `statusMap` 中对应 name 的 UUID，不出现裸 UUID。

### 状态更新

创建/关联后设为 In Progress（`state` 取 `linear.json.statusMap["In Progress"]`）：
```
mcp__linear__update_issue({ id: "<issueUuid>", state: "<statusMap['In Progress']>" })
```

### linear.json 格式

```json
{
  "issueId": "PROJ-123",
  "issueUuid": "uuid-string",
  "issueUrl": "https://linear.app/<workspace>/issue/PROJ-123/...",
  "statusMap": { "In Progress": "<uuid>", "In Review": "<uuid>", "Done": "<uuid>", "...": "..." }
}
```

> `statusMap` 由 get_status_map 在 P1 一次性填充；缺失时各 phase 按需重新调用 get_status_map 回填（幂等）。

### Missing Project / Team Config Handling

若项目 `CLAUDE.md` 缺少 `## Linear 配置`（无 Team / Project id）：
1. **[Interactive]** AskUserQuestion：调 `mcp__linear__list_teams` / `list_projects` 列出可选项，用户选择后写入项目 `CLAUDE.md ## Linear 配置`
2. **[Unattended]** 或用户跳过 → linear plugin **优雅关闭**（不报错，不中止主流程），本任务后续 Linear 同步整体 no-op

### 错误处理

MCP 出错 → 记录错误（操作名 + 错误信息），继续执行，**不中止主流程**。在 final.md 中汇总所有 Linear 失败操作。

## P3.phase-end

> B1：原 P2.phase-end 的「更新 Issue 描述」已并入此处——P3 一次 subagent 完成「描述更新 + 发评论」两步。

### 1. 更新 Issue 描述（不受 upload_docs gate）

1. `mcp__linear__get_issue({ id: "<issueUuid>" })` 取当前 description 长度。
2. 仅当 description **少于 30 字符**时更新：用**派发 prompt 中已注入的 Overview 文本**（事实来源由主线程从 design.md 提取后注入，subagent **不 Read design.md**）：
   `mcp__linear__update_issue({ id: "<issueUuid>", description: "<注入的 Overview 文本>" })`
3. description ≥30 字符 → 整步 no-op（幂等）。

### 2. 上传文档到 Linear（评论，指针式）

当 `task-config.json` 的 `plugins.linear.upload_docs` 为 true 时，创建**指针式**评论——事实取**派发 prompt 注入的 Overview 1-2 行**，指向分支文档，**不 inline design/plan 全文**；前缀 `## 设计+计划摘要`：
```
mcp__linear__create_comment({
  issueId: "<issueUuid>",
  body: "## 设计+计划摘要\n\n{注入的 Overview 1-2 行}\n\n设计+计划已提交，详见分支 `{branch}`：design.md / plan.md"
})
```

## P5.post-acceptance

### 状态更新为 In Review

验收完成后（`state` 取 `linear.json.statusMap["In Review"]`）：
```
mcp__linear__update_issue({ id: "<issueUuid>", state: "<statusMap['In Review']>" })
```

### 验收评论（指针式）

状态置 In Review 后，创建**指针式**验收评论（前缀 `## 验收`，不 inline acceptance-checklist 全文）：
```
mcp__linear__create_comment({
  issueId: "<issueUuid>",
  body: "## 验收\n\n验收通过，状态已置 In Review。详见分支 `{branch}` / PR（acceptance-checklist.md）"
})
```
查重见下方幂等规则（前缀 `## 验收`）。

## P6.pre-archive

### 归档前 Linear 操作

1. 状态设为 Done（`state` 取 `linear.json.statusMap["Done"]`）：
```
mcp__linear__update_issue({ id: "<issueUuid>", state: "<statusMap['Done']>" })
```

2. 归档 comment——**摘要 + 指向**（不再 inline final.md 全文）：

   用**派发 prompt 注入的 final.md 摘要**（最终状态 + 3-5 行摘要 + 关键 changelog——主线程从 final.md 提取后注入，subagent **不 Read final.md**），并指向 final.md 全文所在位置（git 分支 + 归档目录），构建 comment body（Markdown、用户配置语言）：
   ```
   mcp__linear__create_comment({
     issueId: "<issueUuid>",
     body: "## 任务归档：{task-name}\n\n**最终状态**：{Done / Canceled / ...}\n\n{3-5 行摘要}\n\n完整报告见 final.md：分支 `{branch}` / 归档目录 `.tasks/done/{task-name}/final.md`"
   })
   ```

   **为何摘要+指向而非全文 inline**：final.md 全文 inline 会在 P6 重复写一遍大段文本（dogfooding 实测 End 阶段 token 大头之一）；final.md 已落盘在 git（分支 + 归档目录），Linear comment 只需做指针。摘要恒短，无超长问题，故无需 create_document 兜底。

   若 `create_comment` 失败（网络/权限），记录错误并在 final.md 中汇总（遵循 P1 错误处理原则，不中止主流程）。

3. 子 issue 同步（如 `sync_sub_issues` 启用）：关闭关联的子 issue

### Comment Guidelines

1. 使用用户配置的语言
2. Markdown 格式
3. 各 phase 评论统一**指针式**：事实（注入的 Overview/状态/摘要）+ 指向（分支 / PR / 归档目录的 design.md/plan.md/final.md/acceptance-checklist.md），**不 inline 大文档全文**（P3 设计+计划 / P5 验收 / P6 归档同此原则）

## Subagent Context

> 本 section 由编排器在派发 `linear-sync` 一次性后台 subagent 时注入（manifest `subagents.linear-sync.context_section` 指向此处）。编排器读到 `hat-plugin-hook` 输出的 `<!-- DISPATCH ... hook:{point} ... -->` 指令后，`Agent(run_in_background=true)` 派发该 subagent。subagent 按本 section 执行对应 hook 的 Linear 同步，结束即自终结。`--no-filter`（强制 inline）时主线程读上方各 `## P{N}.*` section 直接执行，不走本 section。

### 角色

你是被派发的一次性 `linear-sync` subagent，负责某个 Linear hook（P3/P5/P6 之一）的异步执行。派发 prompt 已**注入**本次 `## {hook_point}` section 与本 `## Subagent Context` 的正文——**直接按注入的正文执行，不要 Read `linear.md` / design.md / plan.md / final.md**（仅 Read `{task-folder}/linear.json` 取 issueUuid；P3 描述/评论的事实取派发 prompt 注入的 Overview 文本）。成功即结束，失败按下方重试；终态失败在你的 result 文本里写明（你**没有** SendMessage，无法主动回报——主线程靠 completion notification 被动感知，按 graceful 吸收）。

### MCP 依赖前提

你从 user/project settings 继承 Linear MCP（`mcp__linear__*`），与主 session 一致——manifest 的 `subagent_type: general-purpose` 不携带 mcpServers，工具靠继承获得。若 `mcp__linear__*` 不可用，在 result 文本写明"MCP 不可用、同步跳过"后结束（无法降级自救）。

### MCP 工具调用模式

| 操作 | 调用 |
|---|---|
| 读 issue | `mcp__linear__get_issue({ id: "<issueUuid 或 PROJ-123>" })` |
| 更新状态/描述 | `mcp__linear__update_issue({ id: "<issueUuid>", state: "<状态 UUID>", description: "..." })` |
| 创建评论 | `mcp__linear__create_comment({ issueId: "<issueUuid>", body: "<用户配置语言的 Markdown>" })` |

`issueUuid` 从 `{task-folder}/linear.json` 的 `issueUuid` 字段读取。

### 状态 UUID 来源

状态 `state` 的 UUID 从 `{task-folder}/linear.json` 的 `statusMap` 字段按 name 读取（如 `statusMap["In Review"]`），由主线程在 P1 经 `mcp__linear__get_status_map` 填充——**subagent 不内嵌任何固定状态 UUID**。若 `statusMap` 缺失对应 name，subagent 自行调 `mcp__linear__get_status_map({ teamId })`（team id 来自派发 prompt 注入或 `linear.json`）解析后再用。

### 幂等规则（重复派发 / 重试不得产生重复副作用）

- **create_comment 前查重**：先 `mcp__linear__list_comments({ issueId })`，**按前缀全量过滤所有评论**（遍历全部评论、不限于近期窗口——B1 合并 + 收敛轮重跑下旧评论易被挤出近期窗口致重复，故全量过滤根治），若已存在同 hook 语义的 comment（按标题前缀 `## 设计+计划摘要`、`## 验收`、`## 任务归档` 三者之一判断）则跳过，不重复发。
- **create_issue 前查 linear.json**：若 `linear.json` 已有 `issueUuid` 则复用，绝不重复创建 issue。
- **update_issue 幂等天然安全**：状态/描述更新可重复执行，以最后一次为准。

### 重试策略

MCP 调用失败 → 指数退避重试：100ms → 200ms → 400ms，最多 3 次。仍失败则在 result 文本写明失败（操作 + 错误 + 建议），结束本轮，不阻塞主流程。

### 终态失败的 result 格式

```
[linear-sync] {hook_point} {操作} 失败，已重试 3 次。
错误: {error}
建议: 跳过或手动处理（Linear 操作幂等，下个 phase / P6 会兜底覆盖）。
```

主线程收到 completion notification 后按 `on_error: graceful` 处理——记入 timing.jsonl 继续，不重试、不阻断。
