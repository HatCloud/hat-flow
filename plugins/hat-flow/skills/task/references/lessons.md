上次整合: 2026-07-06

仅收**编排决策类**经验（路由 / 分支 / 无人值守 / 跨 worker 协调）。执行细节归对应 worker（task-init/-design/-plan/-execute/-test/-end 各自的 lessons）；已固化为 `<rule>`/HARD-GATE 的属硬规则，留正文，不搬此处。硬上限 ≤15 条。

| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| codex-first 经 agent 间接派发不保证真调 codex：派发 prompt 须硬性要求「引擎执行证据（thread/agent id），失败输出 FALLBACK 而非 native 代审」——P2 两轮静默降级 native、P3 加硬性要求后 codex 真跑成功 | 7 | 正文（review.md 派发段） | ISSUE：fallback-log.jsonl P2 R1/R2 两条 + P3 成功对照 | 2026-07-07 |
| 给 reviewer 注入「项目专有约定」时逐条核对出处（grep 到规范原文），不凭印象自创——自创约定会诱导 reviewer 产生系统性误判 | 6 | 正文（review.md 派发段） | ISSUE：P3 派发 prompt 自创「验证命令须来自顶部」，codex 据此产出 2 条误判 Important，靠 pushback 纠正 | 2026-07-07 |
