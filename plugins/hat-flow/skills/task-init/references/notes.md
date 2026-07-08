# Task Init — 背景说明（按需 Read）

SKILL.md 正文只留操作性规则；以下为不影响执行步骤的背景性论述与 schema 细节，按需查阅。

## 档位建议：大体量只读分析 / 元任务拆独立 session

1b.3 档位选择时，若任务含**大体量只读分析 / 复盘**（dogfooding、deep-research、审计、reading-triage 等），分析阶段宜**独立 session 运行**。原因：大段只读分析会显著推高单 phase token（dogfooding 实证 P2 曾达 38%）、污染主上下文。此为轻量 guidance，不强制、不引入自动检测——识别到此类任务时提示用户分析阶段另开 session 即可。

## P1 hook 时序：为何全部推迟到 1f 之后

本阶段全部文件系统写（task-config.json / phases.md / prompt.md）与 P1 hook（`P1.phase-start` → `P1.phase-end`）统一在 1f 任务文件夹创建之后运行。因为 `hat-plugin-hook {task-folder} ...` 必须有已存在的 `{task-folder}` 才能解析，故 1b.3 与 1c/1d 阶段不调用任何 P1 hook。git dirty check 由 `P1.phase-start` 承载，在此运行仍早于任何 task commit，正确性不受影响。

## session.json schema（跨 session 追加）

形态：`{"sessions": ["<id1>", "<id2>", ...]}`。task-init 1f 写入首个；编排器 Step 2B 在跨 session 恢复时把新 session-id 追加进数组（见 task/SKILL.md）。消费者：`hat-conversation-export` wrapper、`/dogfooding`、task-end 导出。用于精确定位本任务的会话导出，修复「抓最新 jsonl」导致的串任务。会话标识（Claude 落点见 harness-tools.md「会话标识」行）缺失时 1f 跳过写入（graceful），导出回退到名匹配并标注「会话来源未经确认」。

## Codex capability 预检（1b.3 首次门控细节）

触发条件：effective config `plugins.review.reviewer` ∈ {`codex`,`auto`} 或 `execution.engine` ∈ {`codex`,`auto`}。运行 `codex-check`：

- `FALLBACK:` / 不可用 → 1b.3 第 4 步 向用户提问（结构化选项优先） 的 reviewer/engine 选项**不提供 codex**、`auto` 此刻锁定为 claude（不报错）。
- `READY` → 保留 codex/auto。
- 检测结果存内存，随 1f 写入 `task-config.json` 的 `capabilities.codex`（`{checked_at,status,reason,quota_state,cwd_control:"unknown"}`；`cwd_control` 由 P4 首个 codex execute 的 spike 回填）。**capabilities 由 phase skill 写入，非 `hat-task-config-resolve`。**
- 派发点二次检测（`checked_at` 过期 / 跨 phase 刷新）由各 phase（P2/P3/P4 dispatch）承担（design Component C）；1b.3 仅做首次门控。reviewer/engine 均不含 codex/auto 时跳过本预检。
