# hatflow-systematic-debugging 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-07-07 收编收尾：辅助文件迁 references/ + 补 Announce/Dependencies

5 个辅助文件（root-cause-tracing.md、defense-in-depth.md、condition-based-waiting.md、condition-based-waiting-example.ts、find-polluter.sh）从根目录迁入 `references/`，同步正文相对引用；补 Announce at start 行；「相关 skill」列表改为规范 `## Dependencies` 段；删「人类伙伴发出的信号」段中 superpowers 遗留的 "Ultrathink" 上游个人化用语，改为陈述式中文措辞。正文方法论未动。外部引用点（task-execute 卡壳阶梯、task-revise、UNATTENDED_PROTOCOL、hat-task-package）均只指向 SKILL.md 或整目录，不受影响。

## 2026-07-07 补中文触发词 + 建 references/changelog.md

lint 全仓扫描发现 description 缺中文触发词（FAIL），补 "系统性调试" 等 5 个触发词；同时首次为本技能创建修订日志，回填导入以来的真实改动历史。

## 2026-06-21 全套 skill 转陈述式 + 纯中文范式（9ca3e42）

随 ISSUE 范式转变批量改造：正文改为陈述式中文表达，移除 per-skill LANGUAGE RULE 块（输出语言改由项目 CLAUDE.md 单一固定）。

## 2026-05-25 统一外部 skill README 命名（bb099b4）

统一采纳自 obra/superpowers 的外部技能 README 命名规范，补充 spec-add-modules frontmatter。

## 2026-05-25 补充采纳技能的 README-zh 译文（06ad445）

为导入的 superpowers 技能补充中文 README 译文。

## 2026-05-24 导入 5 个 superpowers atomic skills（8f2a054）

采纳 obra/superpowers 的 5 个原子技能（含本技能），建立技能采纳路线图。
