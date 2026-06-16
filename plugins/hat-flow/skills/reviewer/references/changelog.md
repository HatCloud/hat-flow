# reviewer 修订日志

记录对本 skill 的每次修改，便于回溯。不注入上下文，最新在最上。

本 skill 是 subagent-only review 工具，reviewer 自身不反复处理同类经验沉淀（经验沉淀归调用方 task 流程），**不开 lessons.md**，只维护本 changelog。

---

## 2026-06-16 声明审查范围排除外部导入技能（忽略表）

「调用方式」后补「范围」说明：外部导入 / 第三方技能不在审查范围，统一登记在忽略表 `~/.claude/skill-maintenance-ignore`（gitignore 风格 glob，如 lark-*、surge）；调用方派发前按表过滤，不靠"是不是软链"。避免对第三方上游技能做无意义的合规审查。

---

## 2026-06-16 设 user-invocable: false（隐藏出 / 斜杠菜单）

subagent-only，被派发调用，从不被用户直接调用，无需暴露在 / 斜杠菜单。隐藏后仍可被派发激活。

## 2026-06-15 可移植性修正 + Dependencies 调用方对齐

用 `revise-skill`（以 spec-skill 为标尺）订正，范围限定可移植性 + 一致性两项偏差。

1. **可移植性（spec 540-562 行）**：SKILL.md 多处用 `${CLAUDE_PLUGIN_ROOT}/skills/reviewer/XXX_REVIEW.md` 绝对路径引用本 skill 自有文件 → 全改 `${CLAUDE_SKILL_DIR}/XXX_REVIEW.md`。
   - L82 PLAN 类型例外段：`${CLAUDE_PLUGIN_ROOT}/skills/reviewer/PLAN_REVIEW.md` → `${CLAUDE_SKILL_DIR}/PLAN_REVIEW.md`。
   - Dependencies 预注入项：`${CLAUDE_POSITIONAL_ARGS}_REVIEW.md` → `${CLAUDE_SKILL_DIR}/${CLAUDE_POSITIONAL_ARGS}_REVIEW.md`。
   - （Dynamic Routing 的 `!`cat`` 行此前已是 `${CLAUDE_SKILL_DIR}/...`，无需改。）
2. **一致性**：SKILL.md Dependencies 调用方仅列 `task skill`，与 README 不符（README 含 distill/research/card-refine 调 DOCUMENT review）→ 以实际调用方为准，SKILL Dependencies 补 `distill / research / card-refine（DOCUMENT review）` 及 `Knowledge_Base Guide 文件` 引用，两处取齐。

> 范围外（待后续）：`*_REVIEW.md` 协议文件仍平铺在 skill 根目录，未迁入 `references/`。本轮不做结构迁移整改，留作后续。
