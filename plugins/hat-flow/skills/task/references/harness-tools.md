# Harness Tools Mapping

task 套件的中性动作词表到 Claude Code / Codex 两侧落点的唯一权威映射。中性化批次替换工具直呼时，动作短语按本表左列原样使用。

| 动作 | Claude 落点 | Codex 落点 | 退化语义备注 |
|---|---|---|---|
| 路径 token 解析规则 | `${CLAUDE_SKILL_DIR}` 与 `${CLAUDE_PLUGIN_ROOT}` 均为原生 env token。 | 按 A8 spike 实测快路径解析：`${CLAUDE_SKILL_DIR}` = 被激活 `SKILL.md` 所在目录，路径由 harness 随技能内容一并暴露；`${CLAUDE_PLUGIN_ROOT}` = 从该目录逐级上溯至含 `.codex-plugin/` 的目录，仅插件形态成立。 | 该定位算法来自 `.tasks/open/2026-07-08-hatflow-codex-port/spike-results.md` 实测：本地 marketplace 安装实测复制进 `~/.codex/plugins/cache/` 且插件结构完整保留（GitHub marketplace 形态同理属官方文档一致的推断，发布后 MUST 实测确认），满足 R1；路径来自被激活技能自身、非 glob 搜索，多版本并存不影响，满足 R2；不依赖未经 spike 实测的路径约定，满足 R3。散装直放 `~/.agents/skills` 无 `.codex-plugin/` 祖先，或自动定位规则不适用 / 运行时失败时，退 EH #9：向用户询问插件根路径，询问所得先以会话内记忆持有，`task-config.json` 落盘后（Phase 1f）回填其 `capabilities` 段持久化；跨 session 若未持久化则每 session 至多再问一次。 |
| 向用户提问（结构化选项优先） | AskUserQuestion 工具（必须使用）。 | 纯文本列选项等待回复。 | Codex 无结构化提问工具时，选项、推荐项和停点语义用可见文本承载，并真正等待用户回复。 |
| 维护进度清单 | TaskCreate/TaskUpdate/TaskList。 | 不支持，`todo_sync` 视为 off、仅用 `phases.md`。 | Codex 不维护宿主 todo；进度权威退到任务文件。 |
| 定向续接某代理 | SendMessage(to: agentId)。 | 未实测，暂用「新开代理并注入前轮上下文」降级。 | `spike-results.md` 未记录具体 Codex 线程续接原语；不得编造 API 或命令名。 |
| 派发子代理（只读 reviewer / 写实现者 / 后台） | Agent 工具 + subagent_type + model 档；通用分析型角色（无对应 native 定义者，如 Requirements Analyst / Devil's Advocate）类型取 `general-purpose`。 | `spawn_agent` + `developer_instructions` 注入协议全文，`sandbox_mode=read-only` 对应只读；无 multi_agent 能力时主线程顺序自执行并如实标注。 | 子代理不可用时保持协议工作内容不跳过，只降级执行位置与并发能力。 |
| 进入/退出隔离工作树 | EnterWorktree/ExitWorktree。 | `git worktree add` + cd（沿用 superpowers codex-tools 的环境检测惯例）。 | 退出时回到原工作目录并按任务协议处理 worktree 生命周期。 |
| 新会话交接 | 输出可复制命令块：`cd {项目根绝对路径} && claude -n "{task-folder-name}" "/task 继续任务「{任务名}」：任务目录 {task-folder}，Plan 已完成、从 Execute 开始。先读该目录下 phases.md 与 task-config.json 恢复进度，按 Resume 流程继续。任务目标：{一句话摘要}"`（占位符取值见 orchestrator 交接步说明）。 | 继续当前会话（无对应机制，跳过交接建议）。 | Codex MVP 不提供同等新会话交接机制。 |
| 运行套件脚本 | 裸命令（bin 目录已入 PATH）。 | `<插件根>/bin/<脚本>` 全路径直接执行，shebang 决定解释器，若丢失可执行位则按 shebang 加 `bash`/`python3` 前缀。 | 插件根按本表首条路径 token 解析规则取得；解析失败退 EH #9。 |
| 调用 Linear MCP 的 <op> | `mcp__linear__<op>`（双下划线）。 | 按 `spike-results.md` 实测暴露名 `mcp__linear.<op>`（单点，server 名与操作名用点连接）。 | 操作名由 MCP server 定义，跨宿主同名；只映射宿主暴露名前缀 / 连接形式。 |
| 会话标识 | `$CLAUDE_CODE_SESSION_ID`；session.json 写入模板：`[ -n "${CLAUDE_CODE_SESSION_ID:-}" ] && printf '{"sessions": ["%s"]}\n' "$CLAUDE_CODE_SESSION_ID" > "{task-folder}/session.json"`；跨 session 追加/合并模板（去重 + create-if-missing + 损坏 JSON 重置兜底 + 失败静默，已实测三例）：`python3 -c 'import json,sys,os; sj,sid=sys.argv[1],sys.argv[2]; g={"json":json,"os":os,"sj":sj}; exec("try:\n d=json.load(open(sj)) if os.path.exists(sj) else {\"sessions\":[]}\nexcept Exception:\n d={\"sessions\":[]}",g); d=g["d"]; d=d if isinstance(d,dict) and isinstance(d.get("sessions"),list) else {"sessions":[]}; (d["sessions"].append(sid), __import__("pathlib").Path(sj).write_text(json.dumps(d))) if sid and sid not in d["sessions"] else None' "{task-folder}/session.json" "$CLAUDE_CODE_SESSION_ID" 2>/dev/null || true`。 | 无对应，`session.json` 写入跳过（graceful degradation）。 | 依赖会话 id 的持久化能力在 Codex MVP 中不启用。 |
| 模型档位（常规/加强） | sonnet/opus。 | 会话默认模型（MVP 不映射）。 | Codex 侧不承诺按动作切换模型档位。 |
| `!` 注入行 | Skill 激活时自动展开。 | 未展开（Read 路由 / Codex 原生加载）时，当场执行该命令或 Read 该文件再继续。 | 对 `!cat` 注入行，Codex 侧按文件读取处理；对命令注入行，按当前安全策略执行可执行命令。 |
| 无人值守模式 | UNATTENDED_PROTOCOL 全量支持。 | MVP 不支持，一律交互降级。 | 无人值守分支在 Codex MVP 中不得静默假装支持；遇停点按交互模式可见处理。 |
| 斜杠命令触发 | `/<技能名>`（如 `/task`）。 | `$<技能名>` mention 或 `/skills` 菜单（如 `$task`）。 | 技能名跨 harness 一致，仅触发语法不同。 |
| 无头驱动（外部驱动器 resume 循环） | 首轮 `claude -p --permission-mode bypassPermissions "/task -q <任务>"`；续轮 `claude -p -c "<按判定算法的应答>"`（无人值守续跑一般为 `"/task -q"`）；过程观测 `claude -p --output-format stream-json --verbose`；「已停止」唯一权威 = 进程退出。 | 不支持（无人值守整体交互降级，见「无人值守模式」行）。 | 判定算法与 state.json 契约见 `headless-driving.md`；本行集中保存 Claude 侧命令配方（该文档正文经本行引用）。 |
| 斜杠位置参数注入 | `${CLAUDE_POSITIONAL_ARGS}`（斜杠激活时展开；**subagent 模式下恒为空字符串**，2026-03-28 dogfooding 实证——故 subagent 调用一律走「路径 B」直接注入协议内容）。 | 无对应（技能激活无位置参数机制）。 | 依赖该变量的动态路由在两侧均不可靠：Claude subagent 模式为空、Codex 无此机制；协议加载以「调用方指明类型 + 直接 Read/注入」为准。 |
