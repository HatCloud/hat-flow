# Changelog

> 最新在最上。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15

- 合规卫生（revise-skill）：
  - 新建本 changelog。
  - README.md 准确性修正：删除 worktree 残留与 `5e` 引用，对齐 SKILL 的 5a/5b/5c/5d。
  - 去冗余：「Test 为硬停、不自动推进 Phase 6」原约 4-5 处重述，保留一处权威 `<rule>`（Test 完成 → 过渡）+ 末尾 trailing reminder，其余改为单行交叉引用。
  - Dependencies 补注 `P5.post-acceptance` 的 `subagent:linear-sync` 异步派发交接契约。
