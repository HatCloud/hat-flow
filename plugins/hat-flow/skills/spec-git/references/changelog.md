# Changelog — spec-git

最新在最上。

## 2026-06-21 落地遗留内容 bug：示例中文化 + 模板对齐脚本 + 去重 + 补 merge 类型

清扫上条遗留的内容 bug。① 通用 commit 示例 description 改中文（Scope/Issue ID/Patterns 三处英文示例），与 L43「中文写 description」规则一致，type/scope/issue-id 仍英文；② Task Lifecycle Commit Templates 原用用户配置语言动词、与脚本实际产出（如 `docs: complete and archive task [...]`）相悖，对齐为真实英文格式；③ 去重——格式化约束删 Commit Discipline #5（保留 Patterns 表对照行），git-add 单元提交把 Commit Discipline #1 精简为仅交叉引用 `<rule>`；④ Type 表补 `merge` 行；⑤ 修正本 changelog 上条把 `Patterns` 误写成 `Common Mistakes` 的笔误。

## 2026-06-20 描述范式：删 Red Flags 表 + git-add 规则陈述化

ISSUE 描述范式转变 spillover。① 删顶部 Red Flags 表——5 条已被 Commit Discipline + Patterns 覆盖，无信息损失；② Commit Discipline 的 `<rule>` 从「Never use git add -A」改为陈述式「stage specific files by name」。遗留内容 bug（commit 描述语言中英矛盾 L60 / Task Lifecycle 模板过时 / 缺 merge:·task: 类型）属轨 2 合规扫除，未在此 pass 处理。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

spec 类不面向用户直接调用，靠触发词/被引用激活；隐藏后仍可自动触发。

## 2026-06-15

- **补 Red Flags 表**：新增 `## Red Flags`（5 条），覆盖 `git add -A`、vague message、单独 style commit、按文件提交、review 中过早 commit 等合理化跳步。
- **可移植性泛化（Worktree Testing Flow）**：原文把 `yarn ios` / `yarn android` 当作硬规则写进全局 git spec，钉死了 RN 栈。改为占位表述「项目的原生构建/运行命令」，保留 RN 示例但明确标注为示例、由各项目按自己的栈替换，避免全局规范绑定单一技术栈。
- 新建本 changelog（spec 类只设 changelog，不设 lessons.md）。
