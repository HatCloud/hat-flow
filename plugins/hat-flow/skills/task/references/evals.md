# task 族回归用例（evals）

> 机制 E1：验证通过的 experiment 沉淀于此，供修订后回归复测（skill-revise Phase 2.5 消费）。硬上限 ≤8 条，满后淘汰最旧/区分度最低者（淘汰记 changelog）。task 族的用例是**端到端流程回归**（跑真实迷你任务查产物），非单臂文本压测——修改编排器/phase skill/插件正文后按此复跑。
>
> **执行时机（用户 2026-07-05 拍板）**：两条 E2E 在**全部技能改造批次完成后的最后阶段**统跑，不随中间批次逐次跑；两条都必须**全自动化**（Interactive 停点用 mock 响应驱动，不依赖真人应答）。
>
> **回归脚本硬性要求**（首跑教训）：每轮输出须检测 quota/session-limit 响应（如 "hit your session limit"）→ 立即中止报 QUOTA_BLOCKED，不空烧 resume 轮；跑前先做一次最小探针确认额度可用。

## E2E-1：Interactive 全流程（mock 响应驱动）

- **task**：在一个迷你 git 项目（`calc.py` 含 `add()` + `test_calc.py` 含 1 条用例 + CLAUDE.md 含验证命令）上执行 `/task 为 calc.py 增加 subtract(a, b) 函数并补一条 pytest 用例`，走完 P1→P6。**停点应答自动化**：各交互停点（需求/设计/plan 确认、验收、End 决策）由预置的 mock 响应表驱动（逐停点给定缺省应答，如「确认/继续/验收通过/Merge locally」），参照 task-execute 既有的 `TASK_RESUME_CHOICE` 环境变量 / menu input fixture 测试接缝模式实现，不依赖真人在场。
- **criteria**（对任务文件夹与仓库跑 assert）：
  - must：`phases.md` 存在且 P1-P6 全部步骤 `[x]`；`prompt.md`/`design.md`/`plan.md`/`acceptance-checklist.md`/`final.md`/`conversation.md` 齐全（`hat-task-artifact-check` 各 phase PASS）；`python3 -m pytest -q` 全绿且 `subtract` 用例存在；任务文件夹已归档至 `.tasks/archive/done/` 或 `.tasks/done/`。
  - must_not：P4 execute 过程中出现阻塞性 AskUserQuestion（约定 9；检查 conversation.md 的 P4 段）；plan/design 阶段因协议正文缺失而凭空发挥（design.md 应体现 DESIGN_PROTOCOL 的结构——批次 0 A1 修复的回归锚点）。
- **观察项**（非判定，记 friction）：每个停点等待是否合理、有无多余确认、有无卡顿点。

## E2E-2：Unattended 全流程

- **task**：同上迷你项目，`claude -p --permission-mode bypassPermissions "/task -q <同一任务>"` 无头执行 + `claude -p -c` resume 循环（单次约 4 phase，上限 8 轮、每轮 gtimeout 900s），全程无人应答。
- **criteria**：
  - must：同 E2E-1 的产物齐全项；另加 `unattended.json` 存在且 `enabled:true`、`unattended-decisions.md` 存在（自动决策留痕）；resume 循环在上限内收敛（非无限卡住——批次 0 A4 派发超时契约的回归锚点）。
  - must_not：transcript 中出现等待用户输入的死等；`git log` 出现越权改写（squash 守卫误压——A3 回归锚点：测试仓无 remote，守卫不得因 `--remotes` 误报而错误跳过或误压）。
- **verdict 记录**：

| 日期 | 用例 | verdict | 备注 |
|---|---|---|---|
| 2026-07-07 | E2E-1 | PASS | 9 轮收敛（≤25）；6/6 断言过；3 次 mock 表未覆盖停点（Git 规范选择 / 分支决策 / `/task` 泛化应答未被识别为 `/task-end`）——下轮跑前按此修 mock 表 |
| 2026-07-07 | E2E-2 | PASS | 2 轮收敛（≤8）；7/9 断言明确 PASS，2 项未充分触发非缺陷（unattended-decisions.md 需任务含歧义点才生成；squash 守卫被 branch=keep 短路未走 merge 路径）——下轮测试任务预埋轻度歧义点 + 显式 `end_decisions.branch=merge` 补全覆盖；P4 review 观察到异步 JOIN 派发 3 subagent、无死等无复活。完整记录：`plans/e2e-run-1/`（journal×2 + report.md） |
