# Skill 优化 Rubric

来自 Anthropic 官方「Agent Skills」文档与「Effective context engineering」工程博客的可信优化准则，逐条经一手来源鉴真（见末尾 Source Ledger）。本表与 spec-skill 正文**互补不重复**：spec-skill 管结构 / 约束分层 / 双语策略，本表专管**压缩、渐进披露、token 经济**——压缩或 review 既有 skill 时额外对照。

## 优化 Rubric

1. **Body Under 500 Lines** — SKILL.md 正文控制在 500 行内（弱模型上限更紧）。逼近时按渐进披露拆到 reference，而非堆进正文。
2. **Three-Level Progressive Disclosure** — 三级加载：启动仅预载所有 skill 的 `name`/`description`；触发时才读 SKILL.md；reference / 脚本按需再读。把互斥或罕用内容下沉到独立文件，降低常驻 token。
3. **References One Level Deep + TOC>100** — 所有 reference 从 SKILL.md **一跳直达**，禁止 reference 再套 reference（嵌套引用会让 Claude 只 `head` 预览、拿到残缺信息）。单个 reference 超 100 行时顶部放一段目录，便于部分读取时看清全貌。
4. **Concise — Don't Explain What Claude Knows** — 默认 Claude 已经很聪明；每段自问「这个解释 Claude 真需要吗、值这些 token 吗」。删掉常识铺垫，只留 Claude 没有的上下文。
5. **Degrees of Freedom by Fragility** — 按任务脆弱度匹配具体度。脆弱 / 唯一正确路径（DB 迁移、严格序列）→ 低自由度、精确脚本、禁改命令；多解 / 依赖上下文（code review）→ 高自由度、给方向让 Claude 自己找路。
6. **Default + Escape Hatch** — 不罗列并列选项（「可以用 A 或 B 或 C…」会制造困惑）。给一个默认 + 一条逃生口：「默认用 X；遇到 Y 改用 Z」。
7. **Consistent Terminology, No Time-Sensitive Info** — 同一概念全程同一个词（别混用 endpoint/URL/route）。不写「某日期之前用旧 API」这类会过期的话；历史信息塞进 "old patterns" 折叠区，不污染正文。
8. **Few Canonical Examples** — 输出质量依赖示例时，给少量**具体** input/output 对，而非抽象描述。示例要 concrete not abstract，胜过纯文字说明。
9. **Scripts: Mark Execute vs Read** — 捆绑脚本必须显式标注用途：「运行」(`Run analyze.py to extract fields`) 还是「当参考读」(`See analyze.py for the algorithm`)。多数工具脚本优先执行——比生成代码更可靠、省 token、保一致。
10. **Subagents Return Summaries** — 把聚焦子任务交给上下文干净的 sub-agent，主 agent 只接收浓缩摘要、不接全过程，避免主上下文被污染。复杂任务上此模式显著优于单 agent。
11. **Just-In-Time Context** — 上下文有限且边际递减；核心是找「能最大化目标达成率的最小高信号 token 集」。信息按需、在需要的时刻注入（大文件留文件系统、用时再 Read），而非预先全量塞入。

## Source Ledger

| rubric 条目 | 来源 | 鉴真状态 |
|---|---|---|
| Body Under 500 Lines | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Token budgets / Progressive disclosure） | ✓ 官方一手，原文 "Keep SKILL.md body under 500 lines" |
| Three-Level Progressive Disclosure | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices + 印证 https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | ✓ 官方一手 + 工程博客印证 |
| References One Level Deep + TOC>100 | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Avoid deeply nested references / Structure longer reference files） | ✓ 官方一手，原文 "Keep references one level deep" / ">100 lines, include a table of contents" |
| Concise — Don't Explain What Claude Knows | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Concise is key / Default assumption） | ✓ 官方一手，原文 "Only add context Claude doesn't already have" |
| Degrees of Freedom by Fragility | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Set appropriate degrees of freedom，narrow-bridge / open-field 类比） | ✓ 官方一手 |
| Default + Escape Hatch | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Avoid offering too many options） | ✓ 官方一手，原文 "Provide a default (with escape hatch)" |
| Consistent Terminology, No Time-Sensitive Info | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Use consistent terminology / Avoid time-sensitive information） | ✓ 官方一手 |
| Few Canonical Examples | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Examples pattern；checklist "Examples are concrete, not abstract"） | ✓ 官方一手 |
| Scripts: Mark Execute vs Read | https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices （Provide utility scripts / Make execution intent clear） | ✓ 官方一手，原文 "Run X (execute) … See X (read as reference)" |
| Subagents Return Summaries | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents （Sub-agent architectures） | ✓ 官方工程博客一手 |
| Just-In-Time Context | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents （JIT knowledge logistics） | ✓ 官方工程博客一手 |
