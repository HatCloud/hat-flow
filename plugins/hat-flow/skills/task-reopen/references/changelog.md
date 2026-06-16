# Changelog

最新在最上。

## 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 删除 `README-zh.md`（双 README 违反单一性/ASCII 约定），保留单一 `README.md`。
  - `README.md` 与 SKILL.md 对齐：Linear 状态更新改述为经 `statusMap` + `get_status_map` 解析、无硬编码 UUID；依赖段去掉硬编码 `mcp__linear__update_issue`，改引用 `plugins/linear.md` 规范。
  - 补 SKILL.md 的 Red Flags 表。
