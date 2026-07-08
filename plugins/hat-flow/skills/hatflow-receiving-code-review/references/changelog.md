# hatflow-receiving-code-review 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-07-07 收编收尾：剥上游语域 + 删重复反奉承节 + 补 Dependencies/README

正文剥离 8 处 "your human partner"（改「用户」）及无接收方的 Circle K 暗号协议；删除「回应方式（正确默认）」「Acknowledging Correct Feedback」两节——与全局 CLAUDE.md「不要奉承用户」准则重复，保留 Handling Unclear Feedback 全阻断规则 / Implementation Order / 外部反馈五问等独有增量；补规范 `## Dependencies` 段（review 插件消费方）；README 补收编背景。

## 2026-07-07 补中文触发词 + 建 references/changelog.md

lint 全仓扫描发现 description 缺中文触发词（FAIL），补 "消化 review 反馈" 等 5 个触发词；同时首次为本技能创建修订日志，回填导入以来的真实改动历史。

## 2026-06-21 全套 skill 转陈述式 + 纯中文范式（9ca3e42）

随 ISSUE 范式转变批量改造：正文改为陈述式中文表达，移除 per-skill LANGUAGE RULE 块（输出语言改由项目 CLAUDE.md 单一固定）。

## 2026-05-25 统一外部 skill README 命名（bb099b4）

统一采纳自 obra/superpowers 的外部技能 README 命名规范，补充 spec-add-modules frontmatter。

## 2026-05-25 补充采纳技能的 README-zh 译文（06ad445）

为导入的 superpowers 技能补充中文 README 译文。

## 2026-05-24 导入 5 个 superpowers atomic skills（8f2a054）

采纳 obra/superpowers 的 5 个原子技能（含本技能），建立技能采纳路线图。
