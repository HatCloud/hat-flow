# Document Review Protocol

通用文档审核协议。通过动态注入 Guide 文件实现类型特有检查。

**调用方式**：调用方（distill/dive/card-refine）派发只读 review 子代理（派发方式见 harness-tools.md「派发子代理」行），将本协议内容 + 对应 Guide 文件内容 + 待审文档内容全部以文本形式注入 prompt（路径 B）。不依赖斜杠位置参数动态路由（见 harness-tools.md「斜杠位置参数注入」行）。

## Required Input

调用方必须注入以下内容，缺少任何一项则终止并报错：

| Input | Description |
|-------|-------------|
| 待审文档全文 | 完整的文档内容（卡片/Wiki/报告/博文） |
| Guide 文件全文 | 对应类型的 Guide（如 CARDS_GUIDE.md）以及适用的 AUTHORSHIP_GUIDE / WRITING_VOICE_GUIDE / CONTENT_ROUTING_GUIDE |
| 文档类型 | Cards / Wiki / Report / Blog |

<rule>
review 开始前先检查所有必要输入，缺失任一输入即以报错终止，并列出缺失项。
Reason: 在残缺上下文上做 review 会产生 false negative，比不做 review 更糟。
</rule>

## Guide 映射

| 文档类型 | Guide 文件 | 路径 |
|---------|-----------|------|
| Cards 卡片 | CARDS_GUIDE.md | ~/Knowledge_Base/docs/CARDS_GUIDE.md |
| Wiki 页面 | WIKI_GUIDE.md | ~/Knowledge_Base/docs/WIKI_GUIDE.md |
| 研究报告 | REPORT_GUIDE.md | ~/Knowledge_Base/docs/REPORT_GUIDE.md |
| Blog 博文 | BLOG_POST_GUIDE.md | ~/Knowledge_Base/docs/BLOG_POST_GUIDE.md |

所有 AI 生成或 AI 显著改写内容，还必须读取 `~/Knowledge_Base/docs/AUTHORSHIP_GUIDE.md`；所有 Post / Blog 内容还必须读取 `~/Knowledge_Base/docs/WRITING_VOICE_GUIDE.md` 和 `~/Knowledge_Base/docs/CONTENT_ROUTING_GUIDE.md`。

## 检查维度

### 1. Fact Check（分级策略）

将文档中的事实性声明分为三类，按不同标准检查：

| 事实类型 | 识别方式 | 检查要求 | 缺失时严重度 |
|---------|---------|---------|------------|
| **硬事实** | API 返回值、版本号、命令参数、报错信息、数据指标 | 必须有可核查源（URL、文档链接、代码路径）；如果是 URL 则验证可达性 | **Critical** |
| **软事实** | 设计哲学、原理、方法论、历史叙述 | 应有主流参考（书籍、论文、官方文档），不强制每条都有 URL | **Important** |
| **观点/解读** | Blog's Note、启示、比喻、类比、个人理解 | 不需要外部源，但必须明确标记为主观解读（不可伪装成客观事实） | **Suggestion** |

**检查流程**：
1. 逐段扫描文档，标记每段的事实类型
2. 对硬事实：检查是否有可核查源；如有 URL，验证可达性
3. 对软事实：检查是否有参考来源
4. 对观点/解读：检查是否明确标记为主观

### 2. Format Compliance（Guide 驱动）

从注入的 Guide 文件中提取 `## 审核检查项` 段落，逐条检查：

1. 读取 Guide 文件中的 `## 审核检查项` 段落
2. 将每个 `- [ ]` 项转化为检查条件
3. 对待审文档逐条验证
4. 未通过的项目按严重度分级：
   - Frontmatter 缺失必填字段 → Critical
   - 结构不符合规范 → Important
   - 风格建议 → Suggestion

**如果 Guide 文件中没有 `## 审核检查项` 段落**：跳过此维度，输出 Warning："Guide 文件缺少审核检查项段落，Format Compliance 检查已跳过。"

### 3. Content Quality（通用基础检查）

以下检查项适用于所有文档类型：

- [ ] **独立性**：文档能否独立阅读理解（不依赖特定对话上下文）
- [ ] **深度**：是否有实质性内容（非空洞总结或纯列表）
- [ ] **可读性**：结构清晰、段落有序、表述准确
- [ ] **无占位符**：无 TBD、TODO、"待补充"等未完成内容

## Output Format

对每个发现的问题输出：

```
### [序号] [问题标题]

- **Severity**: Critical / Important / Suggestion
- **Confidence**: 0-100
- **Location**: 文档中的具体位置（段落/行号/字段名）
- **Issue**: 问题描述
- **Fix**: 修复建议
```

## Confidence Guidance

| Confidence | 适用场景 |
|------------|---------|
| 95+ | 可证伪的矛盾或缺失（如必填字段缺失） |
| 85-94 | 确认的格式/内容问题 |
| 75-84 | 潜在问题（需推理发现） |
| 60-74 | 风格或表述建议 |
| <60 | 纯推测 |

## Summary

审核结束后输出汇总：

```
## 汇总

| Severity | 数量 |
|----------|------|
| Critical | N |
| Important | N |
| Suggestion | N |
```
