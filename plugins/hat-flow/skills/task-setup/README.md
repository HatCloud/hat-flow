# task-setup

hat-flow 任务工作流的首次配置向导（first-run setup）：依赖预检、Linear 身份、可选 Telegram 通知、插件档位、输出语言，一次把任务流在项目里配置就位。全程可跳过，任一步跳过即用缺省。完整步骤与规则以 `SKILL.md` 为准。

## 补充信息

- **在 task 族中的位置**：编排族的「配置入口」worker——与生命周期内各 phase worker 不同，只在项目首次接入时跑一次；之后改配置直接编辑项目的 task-defaults.json，不重跑向导。
- **分发安全立场**：配置只写项目本地（`CLAUDE.md` / `task-defaults.json`），绝不落作者私人值或硬编码状态 UUID——本 skill 随 hat-flow 公开分发，任何个人值都是分发事故。
- **python3 硬门的由来**（ISSUE 教训）：hook 引擎曾隐含未声明的 jq 硬依赖、干净环境全挂，此后核心改纯 Python 并把依赖预检提为 setup 首步——python3 缺失时所有插件 hook 静默失效、流程照跑但产物全缺，故设为不继续的硬门；node 仅 Linear 集成需要。
