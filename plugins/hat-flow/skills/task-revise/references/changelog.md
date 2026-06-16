# Changelog

最新在最上。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 重写 `README.md` 使其与 SKILL.md 的新模型一致：删除旧的「mini design→plan→execute 子流程 / Mini 三段式」表述，改为「自适应单循环、无 Full/Partial/Lite 档位、design/plan 按需」。
