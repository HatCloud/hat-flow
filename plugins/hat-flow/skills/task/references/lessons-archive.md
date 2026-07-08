# Lessons Archive — task (orchestrator)

冷归档：被挤出经验库（`lessons.md`）的条目沉这里，**永不注入、永不作为路径给 model 主动读**。不删，仅供人工回溯 / skill-revise 复活。

## 2026-07-06 归档（skill-revise 对比实验中性×2）

| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| 编排路由：已有 1 个 open task 但用户 prompt 描述的是不相关新任务（新 Linear ID / 新需求）时，Step 1「1 open task→Resume」会误续旧任务；宜加「prompt 含明确新任务信号→询问续旧 or 开新」分支 | 7 | 正文（测试中性×2·已归档 2026-07-06） | ISSUE 审计 F1：open=headless-scheduler 而 prompt=审计+ISSUE 新任务，靠 AskUserQuestion 人工分流 | 2026-06-22 |

> 归档依据：两轮独立设计的对比实验均中性——2026-07-06 轮为实景路由题（open=headless-scheduler 审计 vs prompt=ISSUE statusline 新需求），基线/改前/改后三臂 9/9 全 pass，改前文本在 fresh-context 下不构成误导；ISSUE 的误续发生在长上下文注意力稀释场景，测题无法复现该条件。真实事故证据保留（用户可依协议例外手动强制固化）。
