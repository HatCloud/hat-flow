# task-end changelog

## 2026-07-07 — 正文瘦身至 word-budget 2000 + 补 self-evolving 标记

正文从约 2008 词压到预算内（1999 词），只压表述、不改结构性语义（步骤编号 / hook 调用点 / 停止点 / Iron Law / 无人值守分支全部保留）。

**表述压缩（两处冗余去重，均与相邻 rule/HARD-GATE 的 Reason 重复）：**
- Step 3.3.4 归档前定稿 phases.md 的引子：把三项失败症状枚举收敛为一句，完整失败面指回下方 `<rule>`（该 rule 的 Reason 已完整列出，无信息损失）。
- Step 3.6 retrospective 显式门控的引子：删去与下方 HARD-GATE Reason 重复的「hook 长输出下被截断/漏读」说理，正文留薄指针。

**frontmatter：** 补 `self-evolving: inbox`（与兄弟技能 task-init / task-execute 一致；task-end 仅有 `lessons.md` 收件箱、无 `lessons-archive.md`，故用 `inbox` 而非 `true`——后者会因缺冷归档组件触发 lint FAIL）。消除「标记遗漏」WARN。
