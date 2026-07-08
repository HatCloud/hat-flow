上次整合: 2026-06-22

spec-skill 经验库（transient inbox）。spec 类技能仅作运行段候选收件箱：写入带「建议出口」标记的候选，固化由 `skill-revise` 双盲/对比测试后执行并清空。不做常驻 library / 冷归档 / 整合，不自注入（读者是 skill-revise）。

| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| 涉及外部 CLI flag 语义（尤其安全/权限相关）的设计假设，落 `<rule>`/Iron Law 前必须先 `--help` 核对值域 + 实跑验证，不能凭印象写。无效值（写了不存在的 flag 值）+ 未验证的强制力假设会被当权威约束注入下游 | 8 | 正文（测试中性×1·待重设计） | ISSUE：design 把「只读 worker = permission_mode dontAsk + allowedTools 白名单」写进 headless-scheduler Iron Law，但 dontAsk 非有效 permission-mode 值、且 claude -p 下权限 flag 实测不强制只读（Bash 绕过 / 嵌套继承父权限）；Phase 5 实跑才发现 | 2026-06-22 |
