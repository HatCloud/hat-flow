# spec-skill

Claude Code 全局 skill 编写与维护的唯一权威规范——定义 skill 该有什么结构、frontmatter 怎么写、约束怎么分级、语言策略、自进化组件，以及创建/修改前必过的 Checklist。不是操作手册，完整规则以 `SKILL.md` 为准，本文件不复述。

创建新 skill、修改既有 skill、review skill 质量前都要先读本 skill；被 `skill-create`（新建，Phase 2 Read 作权威）、`skill-revise`（修订，启动即 `!cat` 全文预注入）当规范源头消费。

## 补充信息

- **三分流入口**：从零建新技能走 `skill-create`；改既有技能的正文/流程走 `skill-revise`（带对比实验测试门，是唯一入口）；改本规范自身直接改这里。
- **spec 类 vs 流程类**：本 skill 自己是 spec 类——只维护 `lessons.md` 暂存 inbox + `changelog.md`，不设完整经验库/冷归档，这是"重复使用型流程类技能才配完整自进化机制"这条判据下的自然结果。
- **正文体量**：`SKILL.md` 是高频加载文件（被 `skill-revise`/`spec-task-skill` 每次全文预注入），受体量预算约束；详细论证、自进化组件完整定义、措辞证据基已下沉到 `references/` 下的多个子文件，`SKILL.md` 正文只留骨架规则和 Checklist。
- **历史沿革**：本文件曾承担"英文技能正文的中文对照译文"职责——那个定位已废弃，正文早已统一为陈述式中文；README 现在只做摘要 + 补充信息，不再逐条镜像 `SKILL.md` 的规则（详见 `references/self-evolution-spec.md` 末尾的历史说明）。
