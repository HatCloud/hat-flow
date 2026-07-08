# task-init changelog

## 2026-07-08 — transition rule 机制名换词

编排器 Plan→Execute 的 compact 软停改为新会话交接（skill-revise 定向修订，详见 task 套件 changelog 2026-07-08 条），本 skill transition rule Reason 中「compact」随之换为「新会话交接」。纯换词，无语义变更。

## 2026-07-07 — 正文瘦身至 word-budget 2000

正文从 ~2381 词压到预算内，只压表述、不改结构性语义（步骤编号 / hook 调用点 / 停止点 / 评分规则 / 与编排器·brainstorm·插件系统的契约全部保留，外部引用锚点 1a–1f / 1b.2b / 1d-wt / post-1f 原样）。

**下沉到 `references/notes.md`（纯背景论述，正文留薄指针）：**
- 「档位建议：大体量只读分析拆独立 session」blockquote（1b.3 尾，轻量 guidance）
- 「P1 hook 时序：为何推迟到 1f 之后」的 rationale（正文保留一行操作规则）
- session.json schema 说明 + 消费者清单 + graceful 回退（正文保留 write 命令）
- Codex capability 预检的分支细节（正文 1b.3 第 5 步保留触发条件 + 薄指针）

**正文内表述压缩：** 1b.1 / 1b.2b / 1d / 1d-wt / 1f 的重复说理合并、长句精简，无语义变更。
