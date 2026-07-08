# Wording Evidence（spec-skill 参考）

> 措辞准则（陈述式优先）7 条各自的证据基（一手来源引用）。spec-skill SKILL.md `## 措辞准则` 指向本文件；正文只列规则，出处集中于此，供审校/存疑时查证。

1. **陈述式默认** — LLM 处理否定式弱于肯定式，且 fine-tune 不泛化。García-Ferrero et al., "This is not a Dataset", EMNLP 2023, arXiv:2310.15941；Truong et al., "Language models are not naysayers", *SEM 2023, arXiv:2306.08189。厂商官方同样建议「说该做什么而非不该做什么」：Anthropic, Claude 4 best practices / Be clear and direct（docs.claude.com）；Google, Gemini 3 prompting guide。保留的否定约束应放提示末尾 + 写客观，否则易被丢弃或致 over-indexing（Google, Gemini 3 prompting guide）。
2. **去强调通胀** — 过度强调致 over-triggering / 工具入参幻觉，一句清楚指令通常就够。Anthropic, Claude 4 best practices（把「CRITICAL: You MUST use this tool」改为「Use this tool when…」）；OpenAI, GPT-4.1 Prompting Guide；Google, Gemini prompting guide。
3. **附 Reason** — 给指令附动机，模型从解释泛化。Anthropic, "Add context to improve performance"（Claude 4 best practices）。
4. **具体非模糊** — 模糊形容词换可测量标准。Anthropic（「Limit to 2-3 sentences」）；Google（「write a summary of 3 sentences or less」）。
5. **规则少而不冲突** — rule-augmented prompting 随规则集膨胀 / 冲突而变不稳。rule-guided reasoning benchmark, ACL 2025；arXiv:2506.16335。
6. **Trailing reminder** — 流程末尾的 trailing reminder 可恢复遵从。"Prospective Memory Failures in Large Language Models", arXiv:2603.23530。
7. **结构承重** — 提示格式显著影响输出（最大约 76 分差）。Sclar et al., "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design", ICLR 2024, arXiv:2310.11324。

**语言策略**（中/英文指令遵从差）：EN/ZH 指令遵从差真实但中等、模型依赖、前沿模型缩小（Anthropic 多语言文档：简中 ≈ 英文 96.9-97.1%）；declarative 改写降低跨语言依赖。XIFBench；Multi-IF, arXiv:2410.15553；Mason, arXiv:2603.25015（单预印本，当假说）。详见 `docs/reports/2026-03-28-bilingual-prompting-research.md` + `plans/3-skill-paradigm-shift.md` §4。
