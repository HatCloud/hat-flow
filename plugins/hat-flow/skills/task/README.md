# task

任务生命周期编排器，6 Phase 体系 + 插件架构的入口：读取任务文件夹中的 `phases.md` 决定当前阶段，加载对应阶段 skill 执行，支持跨 session 恢复。本 skill 不执行任何阶段逻辑——只负责路由与 phase 过渡。完整路由规则、无人值守语义与 Trivial 豁免以 `SKILL.md` 为准。

## 补充信息

- **体系定位**：task 族 = 本编排器 + 6 个 phase worker（init/design/plan/execute/test/end）+ 生命周期命令（cancel/reopen/setup）+ revise 子循环；review/linear/git/tdd/retrospective 5 个插件经 `bin/hat-plugin-hook` 在各 hook 点按需注入。
- **关键文件指路**：`task-defaults.json`（配置默认模板，v2 schema 含 4 档位预设）、`UNATTENDED_PROTOCOL.md`（无人值守分级降级协议）、`plugins/`（插件 manifest + 指令文件）、`DESIGN_PROTOCOL.md` / `PLAN_PROMPT.md`（被 task-design / task-plan 运行时嵌入的协议文件）。
- **设计立场**：`phases.md` 是唯一状态源——所有恢复、路由、进度判断都读它，不靠对话记忆；编排器保持薄，阶段逻辑全部下沉到各 phase skill。
- **分发**：本目录是个人版单一来源，对外经 `bin/hat-task-package` 导出为 hat-flow 公开插件（路径与语言中性化，从不写回源码）。
