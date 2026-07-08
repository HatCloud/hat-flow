# Task Skill 规范 (spec-task-skill)

Task workflow 系列 skill 的专用编写规范，继承 `spec-skill` 的所有通用规则。

## 适用范围

- `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md`（编排器）
- `${CLAUDE_PLUGIN_ROOT}/skills/task-init/SKILL.md` ~ `${CLAUDE_PLUGIN_ROOT}/skills/task-end/SKILL.md`（6 个阶段 skill）
- `${CLAUDE_PLUGIN_ROOT}/skills/task-cancel/SKILL.md`、`${CLAUDE_PLUGIN_ROOT}/skills/task-revise/SKILL.md`、`${CLAUDE_PLUGIN_ROOT}/skills/task-reopen/SKILL.md`（生命周期辅助 skill）

## 核心约定

### Core / Plugin Separation
Task 流程分 core（phase skill + 编排器 + 门控脚本）和 plugin（plugins/*.md + manifest）两层，只通过 hook 边界连接。插件逻辑绝不写进 core——目标是任一插件翻 `enabled:false` 即可干净拔除，无需改动 core 文件。需要跨阶段产物（一个阶段产出、另一个阶段消费）的能力难以做成干净插件，其生命周期逻辑容易溢出到 phase skill。

### Phase Transition Protocol
阶段 skill 完成后必须返回编排器 Step 3，不得自行发出过渡指示（如"请调用 /task-end"）。唯一例外是 Test→End 的硬停。

### Phase 语义命名
过渡描述使用 Init/Design/Plan/Execute/Test/End 语义名，避免硬编码序号（phase_merge 会改变序号）。

### Hook Artifact Verification
hook 委托后必须验证预期产物，缺失时执行 fallback 而非跳过。

### Revise Confirmation
Revise 流程的 RN-design 和 RN-plan 必须包含确认循环。

### Interactive / Unattended Duality
改 task skill 的任何步骤都要同时设计正常（Interactive）和无人值守（Unattended）两条路径。每个停顿点（AskUserQuestion / 纯文本确认 / 等待用户测试 / 硬阻断）必须有 `[Unattended]` 分支，保证无人值守不被阻塞——自动按默认决定、或通知后 auto-cancel。

### 剥离 / 删除类任务的验收 grep 范围
以 residual-grep 作验收门控的删除/剥离类任务，其 grep 范围与模式必须排除两类合法命中：刻意保留的产物（后续 block 消费侧、历史记录、changelog）与宽松关键词命中合法标识符的子串误报；否则「零残留」验收会与 Out-of-Scope 自相矛盾、永远 FAIL。

### Hook Manifest Closure
插件 frontmatter 声明的 hook `section` 与 plugin `.md` body 的 `## ` 标题必须双向集合包含（正向：每个 `section` 在 body 有对应标题；反向：每个 hook-handler 标题被某 `section` 引用），判据是 section 字符串的集合包含而非「hook 点名 == section 名」，否则会出现声明缺段或写了却永不 emit 的静默失效。

### Interaction Front-Loading
用户交互前置到 Init/Design 一次性收集；Plan 交互最小化；Execute(P4) 在所有模式（含 Interactive）零阻塞交互，卡死终态是在 session 内可见停下 + 输出报告（Telegram 为 best-effort 叠加）；对外不可逆动作（发布/push/删除）的就绪后确认建模为 P6 End 决策，P5/P6 与独立 on-demand skill 豁免。

### 任务文档路径引用约束
任务文档自引用当前任务的其他文件时用 `任务文档/<relative_path>` 占位符，绝对路径 out of scope；`docs/` 目录下文档沿用原有路径写法为例外。

## 使用方式

创建或修改 task 系列 skill 时加载此 spec：`/spec-task-skill`。它会自动预注入 spec-skill 内容。
