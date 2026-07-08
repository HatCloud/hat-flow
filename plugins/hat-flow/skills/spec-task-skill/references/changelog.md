# Changelog — spec-task-skill

> 最新在最上。每条记录一次改动及缘由。

## 2026-07-08 约定 1/2 机制名：compact → 新会话交接

编排器 Plan 完成后的软停机制由 compact 建议改为新会话交接建议（skill-revise 定向修订，动因与全量改动见 task 套件 changelog 2026-07-08 条），本规范约定 1（Phase Transition Protocol 的排除项与 rule）、约定 2（语义命名示例）中的机制名同步换词。约定本身的语义（过渡逻辑归编排器、语义命名判据）不变。

## 2026-07-07 word-budget 档位声明回填

frontmatter 补 `word-budget: 2000`，依据 2026-07-07 Length Budget 三档声明制回填（权威规范类，被 skill-create/skill-revise 全文预注入消费）。

## 2026-07-05 Dependencies 补「消费方」说明（元技能改造，机制 D）

诊断发现：`skill-create`/`skill-revise` 处理 task 系列目标技能时，正文里全无判断分支去加载本文件——是否套用本文件的 10 条增量约定完全靠人工记性。补一句「消费方」说明本文件被谁、何时条件消费（`skill-create` Phase 1/2 之间、`skill-revise` Phase 0，目标名匹配 `task*` 或 Dependencies 声明 `Invokes: task-*` 时）。本文件侧只做说明，不感知消费方数量；实际路由分支在两个消费方各自的 SKILL.md 里加。

## 2026-06-21 README 核心约定补齐后 4 条（约定 7~10）

README「核心约定」节原只提炼前 6 条，缺约定 7（删除/剥离类验收 grep 范围排除合法命中）、8（Hook Manifest Closure 双向集合包含）、9（Interaction Front-Loading）、10（任务文档路径引用约束）。按 SKILL.md 实际标题/内容各补一句 `###` 子条，使 README 与 SKILL.md 的 10 条约定一一对应、不再漏提 spec 后半段约束。

## 2026-06-20 描述范式：删 Red Flags 表（降级为作者侧工具）

ISSUE 描述范式转变 spillover。删顶部 Red Flags 表——其 4 条（transition 返回 Step 3 / hook 多段验证 / 语义命名 / Revise 确认）已分别由约定 1/3/2/4 的正文 + `<rule>` 覆盖，无信息损失；Red Flags 按新范式降级为作者侧失败模式头脑风暴工具、不注入。`<HARD-GATE>` / `<rule>` 为正当硬规则，保留。

## 2026-06-20 约定 9 补「对外不可逆动作的就绪后确认」边界

ISSUE dogfooding 发现：发布确认（带阻塞 AskUserQuestion）落在 P4 Execute 内，表面撞约定 9「P4 零阻塞」。根因是约定 9 原假设一切交互可前置到 Design，但「发布/push/删除」的就绪后确认必须等产物全绿才有意义、无法前置。修法不削弱 P4 硬规则，而是新增边界澄清 + Rationalization 行 + review checklist 子句：这类动作建模为 **P6 End 决策**（P6 本就豁免本约定），不塞进 P4。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

spec 类不面向用户直接调用，靠触发词/被引用激活；隐藏后仍可自动触发。

## 2026-06-15

- **可移植性修复**：SKILL.md 第 31 行 `!`cat`` 由硬编码绝对路径 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md` 改为 `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md`。缘由：硬编码本地绝对路径违反 spec-skill 可移植性 rule（skill 移动/复用即失效），改用 `${CLAUDE_SKILL_DIR}` 后随目录自动解析。
- **README 适用范围补全**：README.md「适用范围」原只列 task-cancel / task-revise，补上 task-reopen（SKILL.md 正文实含 task-reopen，README 漏列），与 SKILL.md 保持一致。
- **新建本 changelog**：spec 类被修改后需维护 changelog（spec-skill File Organization rule）。
