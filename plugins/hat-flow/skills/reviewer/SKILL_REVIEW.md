# Skill Review Protocol

审核 skill 文件（SKILL.md + README.md）的质量。基于 spec-skill 规范。

**调用方式**：调用方派发 Agent subagent，将本协议内容 + spec-skill 规范内容 + 待审 SKILL.md + README.md 全部以文本形式注入 prompt（路径 B）。不依赖 `${CLAUDE_POSITIONAL_ARGS}` 动态路由。

## Required Input

调用方必须注入以下内容，缺少任何一项则终止并报错：

| Input | Description |
|-------|-------------|
| SKILL.md 全文 | 待审核的 SKILL.md |
| README.md 全文 | 待审核的 README.md |
| spec-skill 规范 | spec-skill SKILL.md 的内容（`${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md`） |

<rule>
Check all required inputs before starting review. If any input is missing, output error listing missing items and terminate immediately.
Reason: reviewing with partial context produces false negatives that are worse than no review.
</rule>

## 检查维度

### 1. 结构合规

对照 spec-skill 规范，检查 SKILL.md 的必要段落：

- [ ] **Frontmatter** 完整（name、description 字段）
- [ ] **LANGUAGE RULE** 段落存在且明确（中文主体 + 英文技术术语）
- [ ] **Red Flags 表格** 存在，列出常见错误思维模式
- [ ] **Mandatory Stop Points 表格** 存在，每个 Gate 有明确的 AskUserQuestion 说明
- [ ] **流程步骤** 存在且编号连续
- [ ] **触发方式** 在 SKILL.md 或 README.md 中有明确列出

对照 spec-skill 规范，检查 README.md 的结构：

- [ ] 包含触发方式/关键词
- [ ] 包含核心流程概览（步骤列表）
- [ ] 包含输出路径（如适用）
- [ ] 包含依赖声明（引用其他 skill 或外部文件）

### 2. 流程完整性

- [ ] 每个 Mandatory Stop Point 都有对应的流程步骤说明
- [ ] 流程步骤之间的依赖关系清晰（后续步骤不引用尚未创建的产物）
- [ ] Iron Laws（如有）有明确的违反后果说明
- [ ] Error Handling 覆盖关键失败场景（至少：用户拒绝 Gate、外部文件不存在、subagent 调用失败）

### 3. 兼容性

**CC 特有语法黑名单**（以下语法不得出现在需要兼容 an alternate runtime 的 skill 中）：

- `${CLAUDE_POSITIONAL_ARGS}`
- `${CLAUDE_SKILL_DIR}`
- `${CLAUDE_USER_ARGS}`
- `` !`command` `` 注入语法

检查项：
- [ ] SKILL.md 中不包含上述黑名单语法
- [ ] README.md 中不包含上述黑名单语法
- [ ] 工具调用使用通用名称（如 "AskUserQuestion"、"Agent"），不使用平台特有 API

**注意**：`<rule>` 标签是合法的——它是强调规则的格式，非 CC 特有语法。

### 4. 内容质量

- [ ] **指令清晰度**：无歧义表述（如"适当处理"、"酌情判断"——必须具体化）
- [ ] **占位符扫描**：无 TBD、TODO、"to be determined"、"待补充"
- [ ] **流程一致性**：SKILL.md 中的步骤数与 README.md 概览一致
- [ ] **路径准确性**：所有文件路径是精确的（无"相关目录"等模糊描述）
- [ ] **Red Flags 覆盖度**：Red Flags 表格是否覆盖了该 skill 特有的常见错误（非仅复制通用模板）

## Output Format

对每个发现的问题输出：

```
### [序号] [问题标题]

- **Severity**: Critical / Important / Suggestion
- **Confidence**: 0-100
- **Location**: SKILL.md 或 README.md 中的具体位置
- **Issue**: 问题描述
- **Fix**: 修复建议
```

## Confidence Guidance

| Confidence | 适用场景 |
|------------|---------|
| 95+ | 可证伪的矛盾或必填项缺失 |
| 85-94 | 确认的结构性缺失或格式问题 |
| 75-84 | 潜在的流程间隙或隐含假设 |
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
