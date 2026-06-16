# Changelog

> 最新在最上。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 对齐 hook 化后的实际流程：删除已脱节的「Code Review Light（Medium/High 必做）」「Commit Guidelines 内联」表述，改述为 P4.per-task-post / P4.post-execute hook 驱动。
  - SKILL.md 4a mode fallback `<rule>` 正文改英文（Reason 保留中文），符合双语策略。
