# Headless Driving — task 工作流外部驱动契约

本文件是**外部驱动契约的唯一权威**：外部驱动方（E2E 回归脚本、cron、调度器）如何不解析输出文本、纯机械地驱动 task 工作流。写入端语义见 `bin/hat-task-state`（脚本 docstring）与 task/SKILL.md 的停点状态 `<rule>`。

## state.json Schema（v1）

位置：`{task-folder}/state.json`。由 `bin/hat-task-state` 写入（原子写）。

```json
{
  "v": 1,
  "state": "waiting_input",
  "phase": 2,
  "stop_point": "design-approval",
  "resume_hint": "approve",
  "expected_input": "回复「继续」批准 design，或给出修改意见",
  "outcome": null,
  "updated_at": "2026-07-07T12:00:00Z",
  "stopped_at": null,
  "session_id": "<uuid>"
}
```

| 字段 | 语义 |
|---|---|
| `state` | 三态：`running`（推进中）/ `waiting_input`（停点等人工）/ `terminal`（终态） |
| `resume_hint` | **机械消费枚举**：`approve`=回「继续」即可推进；`choice`=需从选项中选；`free_text`=需实质输入 |
| `expected_input` | **纯人读展示文本**——禁止解析为结构化指令、禁止原样回填为下一轮输入（内容可能间接混入用户原始输入，属未消毒面） |
| `stop_point` | 语义 slug，诊断辅助；词表开放（见下），驱动方**不得 switch on 它** |
| `outcome` | 仅 terminal 非空：`done / canceled / deferred` |
| `updated_at` | 流程侧写入时间（UTC ISO） |
| `stopped_at` | Stop hook（`hat-task-state stamp`）盖的回合结束戳；**必要不充分**证据（见下），可恒 null |
| `session_id` | 写入方会话 id；stamp 按它匹配、杜绝多 open task 张冠李戴 |

**机械消费边界**：驱动决策只依赖 `state` + `resume_hint`（+ `outcome`）。

## 驱动判定算法

前提：**「已停止」的唯一权威是进程退出事实**（无头驱动进程退出 / 超时被杀；命令配方集中于 harness-tools.md「无头驱动」行）。确认进程退出后按序判定：

| # | 条件 | 动作 |
|---|---|---|
| 0 | 无 state.json / JSON 损坏 | 回退启发式（见下节） |
| 1 | `stopped_at` 与 `updated_at` 均非空，且 `stopped_at - updated_at > 30s` | 语义陈旧（流程漏写）→ 回退启发式 |
| 2 | `state == terminal` | 按 `outcome` 收尾，停止 resume |
| 3 | `state == waiting_input` | 按 `resume_hint` 应答后以「无头驱动」行续轮命令 resume |
| 4 | `state == running`（进程却已退出） | 异常中止（quota / crash / 外层超时误杀）→ 直接 resume 安全（幂等恢复由 phases.md 承担） |
| 5 | open 路径整体消失 | 查 `.tasks/done|canceled|deferred/`（含 `archive/` 下同名）判终态（归档移动窗口期兜底） |

参考实现（可执行镜像，覆盖分支 0-4）：`bin/test_hat_task_state.py` 的 `driver_decision()`——分支 5 是文件系统层探测（open 路径存在性 + 归档目录扫描），由驱动方自行实现，不在该函数范围内。

**`stopped_at` 为何必要不充分**：Stop hook 数组里其它 hook（如 hat-friction-remind）可能返回 `{"decision":"block"}` 让会话再续一轮——此时 stamp 已落盘但回合并未真正终止。故 `stopped_at` 只用于新鲜度比较（第 1 行），绝不单独当「已停止」用。**同 session 多 open task**：一个 session 先后碰过的多个 open task，其 state.json 的 session_id 相同，stamp 会全部盖戳（设计接受行为——多盖只给非活跃任务的新鲜度比较添一次噪音，不损坏数据；驱动方判定仍以各自的 state/updated_at 为主）。实证（2026-07-07）：Stop hook 在**交互与 `-p` 无头模式下均实时触发**（无需重启 session）；但 hat-flow 下游用户可能未注册该 hook → `stopped_at` 恒 null → 第 1 行自然跳过、主路径不受影响。

## 无 state.json 回退（旧任务 / 语义陈旧）

phases.md 启发式：

- Phase 6 Status = DONE **且** 任务夹已在归档路径（`done/` 等）→ 终态
- 否则 → resume（「无头驱动」行续轮命令，应答 `"/task -q"`），依赖 phases.md 的 `[x]` 恢复语义
- 连续 N 轮（建议 3）resume 后 phases.md 无任何变化 → 判 stuck，人工介入

## 消费方驱动契约

- **超时**：每轮预算建议 900s（无头单轮实测可跑完约 4 个 phase 中的大段）。**坑（E2E 首跑实证）**：调用方工具链常有更短的同步调用硬上限（如 Claude Code Bash 工具 600s）——务必**异步启动 + 让内部 `gtimeout 900` 做超时权威**，不要同步等待。
- **resume 循环**：按 harness-tools.md「无头驱动」行的首轮/续轮命令执行（无人值守续跑一般就是 `"/task -q"`）。设上限轮次（无人值守建议 8）+ 每轮做 quota 检测（输出命中 `hit your.*limit` → 立即中止报 QUOTA_BLOCKED，不空烧）。
- **观测**：需要过程可见性时用「无头驱动」行的观测命令（stream-json 逐事件读）；只判结果时读 state.json 即可，不解析文本。
- **副作用屏蔽（测试床）**：项目本地 `task-defaults.json` 显式 `"telegram_chat_id": null` = 显式禁用通知（短路探测链，见 UNATTENDED_PROTOCOL.md §3）。

## stop_point 词表（开放登记，非封闭枚举）

初始收录（来源：各 skill Mandatory Stop Points 表；新增停点直接沿用其语义 slug，不构成 breaking change）。`期望 resume_hint` 列是写入方的映射权威——编排器在停点按此填，不必每次重新推断：

| slug | 停点 | 期望 resume_hint |
|---|---|---|
| `requirement-confirm` | 1b.1 需求确认 | approve |
| `tier-select` | 1b.3 档位 | choice |
| `branch-decision` | 1d | choice |
| `worktree-ask` | 1d-wt | choice |
| `dirty-files` | P1 hook | choice |
| `git-conventions` | 1c | choice |
| `linear-create` | 1e/1f | choice |
| `unattended-activation` | 2A.1 | choice |
| `web-research-gate` | P2 1.5 | choice |
| `clarify` | P2 Step 2 | free_text |
| `approach-select` | P2 Step 3 | choice |
| `section-confirm` | P2 Step 4 | approve |
| `review-strategy` | P2 6.5 | choice |
| `design-approval` | P2 Step 8 | approve |
| `plan-confirm` | P3 3b | approve |
| `acceptance-checklist` | P5 5c | free_text |
| `test-hard-stop` | P5 完成硬停 | approve（回 `/task-end`） |
| `end-branch-menu` | P6 分支处置 | choice |
| `stuck-report` | P4 卡壳升级末端可见停下 | free_text |
| `paused` | 无人值守 §8 暂停 | free_text |
