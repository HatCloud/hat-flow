# brainstorm — 轻量苏格拉底式需求头脑风暴

## 用途

把模糊或初级的想法，通过逐问苏格拉底式对话扩充为合理、详尽、可执行的需求。定位是"轻封装"——不像 Superpowers brainstorming 那样多阶段 + 模板 + 对抗 review，只保留"逐问追问直到满意"的核心。

## 三入口

- **独立触发**：用户说"头脑风暴 / brainstorm / 帮我想想 / 完善需求"即唤起（`user-invocable: true`，菜单可见）。输出扩充后的结构化需求文本，不写文件。
- **被 task-init 调用**：task-init 1b.2 Prompt 健康度评估为"低分"（2+ ❌ 或 ❌/⚠️≥3）或用户主动时，经 Read 协议 inline 调用；产物回流内存态，由 task-init 1f 落盘 prompt.md。
- **被 skill-create 调用**：Phase 1 对新技能想法无条件做需求扩充，经 Read 调用；产物回流内存态，由 skill-create 收入其需求上下文。

流程与规则见 SKILL.md 正文，此处不复述。

## 自进化

`self-evolving: true`。运行段沉淀经验进 `references/lessons.md`，固化经 `skill-revise` 双盲测试。
