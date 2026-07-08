# hatflow-dispatching-parallel-agents 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-07-08 Codex 中性化批②——派发工具名中性化

将正文中的「Agent 工具」直呼改为「并发派发子代理」，与 task 套件的 `harness-tools.md` 子代理派发动作词保持一致，避免绑定 Claude Code 工具名。

## 2026-07-07 正式收编瘦身（D6a）

description 补 Do NOT use 排除条件；删除与消费方/harness 重叠的 Real Example、Key Benefits、Task() 伪代码段（536→307 词），Verification 四步并入「4. Review and Integrate」去重；README 去镜像，只留摘要 + 收编背景。

## 2026-07-07 补 references/changelog.md（回填历史）

首次为本技能创建修订日志，回填导入以来的真实改动历史（此前未维护 changelog，属漏项补齐）。

## 2026-06-21 全套 skill 转陈述式 + 纯中文范式（9ca3e42）

随 ISSUE 范式转变批量改造：正文改为陈述式中文表达，移除 per-skill LANGUAGE RULE 块（输出语言改由项目 CLAUDE.md 单一固定）。

## 2026-05-25 统一外部 skill README 命名（bb099b4）

统一采纳自 obra/superpowers 的外部技能 README 命名规范，补充 spec-add-modules frontmatter。

## 2026-05-25 补充采纳技能的 README-zh 译文（06ad445）

为导入的 superpowers 技能补充中文 README 译文。

## 2026-05-24 导入 5 个 superpowers atomic skills（8f2a054）

采纳 obra/superpowers 的 5 个原子技能（含本技能），建立技能采纳路线图。
