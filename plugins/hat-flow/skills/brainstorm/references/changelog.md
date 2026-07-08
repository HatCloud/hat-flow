# brainstorm changelog

> 仅在 skill 定义（SKILL.md / reference / 经验库结构）被修改时写一条，记「改了什么 + 为何」，最新在最上。

## 2026-07-07 F3 契约联动订正（技能舰队审计，经 skill-revise）

- **补登 skill-create 第三调用方**：Dependencies / README / description 此前只写独立 + task-init 双入口，skill-create Phase 1 已无条件调用本技能（skill-create/SKILL.md:57-71）；Iron Law 4、Step 1、Step 5 的「被 task-init 调用」分支泛化为「被编排方调用」（落盘由调用方各自负责：task-init 1f / skill-create Phase 1）。
- **独立触发 + 无人值守的决策落点**：Step 2 [Unattended] 原写死 `{task-folder}/unattended-decisions.md`，独立触发场景无 task-folder——改为有 task-folder 记文件、独立场景并入最终输出文本。
- **补调用载体说明**：被编排方经 Read 加载时 `!`cat`` 注入行不展开，正文加防护提示（先手动 Read lessons 与母本）。
- **README 去镜像**：删「核心流程」「关键规则」复述段，双入口改三入口。

## 2026-06-21 — 新增 brainstorm skill（ISSUE）

- 新建轻量苏格拉底式需求头脑风暴 skill：`user-invocable: true` + `self-evolving: true`。
- 核心：逐问为主（one-question-at-a-time，实证最佳实践）、联网许可门（复用 web-research 契约、只采信 verified）、收敛双触发（用户喊停 + 质量达标主动确认）、无人值守两门默认开启 + 确定性退出 cap、内存态原子回流。
- 双入口：独立 `/brainstorm` + task-init 1b.2b 低分路径调用。
- 为何：task-init 此前对模糊/初级需求无主动扩充机制，模糊需求带病进入 Design。
