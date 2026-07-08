# hatflow-verification-before-completion 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-07-07 收编收尾：description 排除条件 + user-invocable:false + 补 Announce/README

description 补 "Do NOT use" 排除条件（区分内建 `verify` 的执行侧职责 vs 本技能的声明纪律侧职责）；补 `user-invocable: false`（被 task-test / hatflow-systematic-debugging 引用的纪律库，用户不主动敲 `/hatflow-verification-before-completion`）；补 Announce at start 行；README 补收编背景。核实 task-test/SKILL.md:60「失败案例库」措辞已过时——本技能现有对应物是 Rationalization Guard（托词表）与 Claim Requirements（证据要求表），未改 task-test 文件，仅报告。

## 2026-07-07 补中文触发词 + 建 references/changelog.md

lint 全仓扫描发现 description 缺中文触发词（FAIL），补 "验证后再声称完成" 等 5 个触发词；同时首次为本技能创建修订日志，回填导入以来的真实改动历史。

## 2026-06-21 全套 skill 转陈述式 + 纯中文范式（9ca3e42）

随 ISSUE 范式转变批量改造：正文改为陈述式中文表达，移除 per-skill LANGUAGE RULE 块（输出语言改由项目 CLAUDE.md 单一固定）。

## 2026-05-25 统一外部 skill README 命名（bb099b4）

统一采纳自 obra/superpowers 的外部技能 README 命名规范，补充 spec-add-modules frontmatter。

## 2026-05-25 补充采纳技能的 README-zh 译文（06ad445）

为导入的 superpowers 技能补充中文 README 译文。

## 2026-05-24 导入 5 个 superpowers atomic skills（8f2a054）

采纳 obra/superpowers 的 5 个原子技能（含本技能），建立技能采纳路线图。
