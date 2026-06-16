# Changelog — spec-git

最新在最上。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

spec 类不面向用户直接调用，靠触发词/被引用激活；隐藏后仍可自动触发。

## 2026-06-15

- **补 Red Flags 表**：新增 `## Red Flags`（5 条），覆盖 `git add -A`、vague message、单独 style commit、按文件提交、review 中过早 commit 等合理化跳步。
- **可移植性泛化（Worktree Testing Flow）**：原文把 `yarn ios` / `yarn android` 当作硬规则写进全局 git spec，钉死了 RN 栈。改为占位表述「项目的原生构建/运行命令」，保留 RN 示例但明确标注为示例、由各项目按自己的栈替换，避免全局规范绑定单一技术栈。
- 新建本 changelog（spec 类只设 changelog，不设 lessons.md）。
