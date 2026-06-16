# task-design 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。
visual-companion/ 子目录的变更也并入本日志（无独立 changelog）。

---

## 2026-06-17 Step 7 max_rounds A4 分级续跑 (M3)

- Step 7 max_rounds 退出的 [Unattended] 分支按 `degrade_policy` 分流：standard/缺省=暂停（现状）；conservative/headless=A4 accept-with-findings（剩余 findings 写 design.md `## Unresolved Review Findings` + unattended-decisions.md，续跑；同点至多一次，第二次退回暂停）。见 UNATTENDED_PROTOCOL §9。

## 2026-06-17 Step 2e headless 短路 (M1)

- Step 2e.2 加 `_source == "headless"` 最先判断：无头物化的 config 永不弹偏离面板，复杂度评估仍跑、结果写 2e.3 design.md 策略段。
- Activation Timing 守卫补注：`enabled:true` 含 quiet 入口 1f 物化的 headless 状态，跳过激活询问。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **README.md 核心流程第 2 步对齐 SKILL.md Stop Points**：「提出澄清问题（每次一个）」与 SKILL.md「合并提问（最多 4 个）」不一致，改为「合并提问（最多 4 个）」；「关键规则」中的「每次只问一个问题」一并删除。
