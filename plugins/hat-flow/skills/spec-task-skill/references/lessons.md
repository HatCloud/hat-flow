# spec-task-skill 暂存 inbox（transient）

> spec 类技能的暂存 inbox：两段式运行段把候选经验沉这里（带「建议出口」标记），由 skill-revise 双盲测试后固化进正文 / reference、并**清空**本表。空是常态，不做冷归档 / 整合、不自注入（读者是 skill-revise）。

| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| 📸 改 plugin `.md` 正文后 `golden_corpus` 测试必失败（字节级锁定），需重生 golden；验证流程缺「改 plugin 正文须同步重生 golden」提示，且无 `--regen` 命令、靠手写 inline 重生 | 7 | reference | 本会话 dogfood; bin/test_plugin_hook.py:442 | 2026-06-21 |
