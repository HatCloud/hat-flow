# Changelog — spec-task-skill

> 最新在最上。每条记录一次改动及缘由。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

spec 类不面向用户直接调用，靠触发词/被引用激活；隐藏后仍可自动触发。

## 2026-06-15

- **可移植性修复**：SKILL.md 第 31 行 `!`cat`` 由硬编码绝对路径 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md` 改为 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md`。缘由：硬编码本地绝对路径违反 spec-skill 可移植性 rule（skill 移动/复用即失效），改用 `${CLAUDE_SKILL_DIR}` 后随目录自动解析。
- **README 适用范围补全**：README.md「适用范围」原只列 task-cancel / task-revise，补上 task-reopen（SKILL.md 正文实含 task-reopen，README 漏列），与 SKILL.md 保持一致。
- **新建本 changelog**：spec 类被修改后需维护 changelog（spec-skill File Organization rule）。
