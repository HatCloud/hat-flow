# task-plan 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

---

## 2026-06-17 3b max_rounds A4 分级续跑 (M3)

- 3b max_rounds 退出的 [Unattended] 分支按 `degrade_policy` 分流：standard/缺省=暂停（现状）；conservative/headless=A4 accept-with-findings（剩余 Issues 写 plan.md `## Unresolved Review Findings` + unattended-decisions.md，续跑；同点至多一次，第二次退回暂停）。见 UNATTENDED_PROTOCOL §9。

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

由 task orchestrator 路由派发、不单独跑，无需暴露在 / 斜杠菜单。隐藏后仍可被编排器/派发激活。

## 2026-06-15 合规订正（revise-skill 批量）

按 spec-skill File Organization / Naming / Bilingual Strategy / Checklist 订正本流程类 worker（经验归属在 task orchestrator，本 skill 不设独立 lessons.md）：

1. **新增 `references/changelog.md`**（本文件）。spec 规定每个被修改的 skill 必须维护修订日志。
2. **README.md 核心流程重写对齐 SKILL.md SC2 二元契约**：原描述「Reviewer subagent review（Low 0 轮，Medium 1+条件第2轮，High 2轮）」与「确认执行模式 + TDD 策略」均与 SKILL.md 不符——前者属过时的分层轮次矩阵（SC2 实为单个 plan-reviewer、single-pass、Verdict 二元、不算轮次矩阵），后者属 Phase 2 职责（plan 阶段无此停点）。两者均删除/重写。
3. **双语：中文章节标题改英文**——`### 3b. Plan 忠实度评估` → `### 3b. Plan Fidelity Review`；`### 3c + 3d: P3.phase-end（...）` → `### 3c + 3d: P3.phase-end (Timestamp + Commit + Linear Sync)`（Resume Support 中文对照行保持不变）。
