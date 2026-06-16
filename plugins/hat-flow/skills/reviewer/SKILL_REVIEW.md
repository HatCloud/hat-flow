# Skill Review Protocol

审核 skill 文件（SKILL.md + README.md）的质量。基于 spec-skill 规范。

**调用方式**：调用方派发 Agent subagent，将本协议内容 + spec-skill 规范内容 + 待审 SKILL.md + README.md 全部以文本形式注入 prompt（路径 B）。不依赖 `${CLAUDE_POSITIONAL_ARGS}` 动态路由。

**范围**：只审**我们自有**的技能。**外部导入 / 第三方技能不在审查范围**——它们统一登记在忽略表 `~/.claude/skill-maintenance-ignore`（gitignore 风格 glob，按技能名匹配，如 `lark-*`、`surge`）。调用方派发前先读这份表、把命中的技能过滤掉，不要派审（**以忽略表为准，不靠"是不是软链"**）。

## Required Input

调用方必须注入以下内容，缺少任何一项则终止并报错：

| Input | Description |
|-------|-------------|
| SKILL.md 全文 | 待审核的 SKILL.md |
| README.md 全文 | 待审核的 README.md |
| spec-skill 规范 | spec-skill SKILL.md 的内容（`${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/SKILL.md`） |

> 注：维度 5「自进化合规」以注入的 spec-skill「Self-Evolution Capability」**当前定义**为准——每次审查都用最新版，无需被审技能自带版本戳。

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

**ASCII 命名**（对照 spec-skill「File Organization → Naming: ASCII Only」）：
- [ ] skill 目录下文件名 / 文件夹名全为 ASCII 英文（无中文 / 空格 / 点）。发现中文名 → `Important`，Fix 写出对应英文 kebab-case 译名 + 提示同步更新所有引用

**注意**：`<rule>` 标签是合法的——它是强调规则的格式，非 CC 特有语法。

### 4. 内容质量

- [ ] **指令清晰度**：无歧义表述（如"适当处理"、"酌情判断"——必须具体化）
- [ ] **占位符扫描**：无 TBD、TODO、"to be determined"、"待补充"
- [ ] **流程一致性**：SKILL.md 中的步骤数与 README.md 概览一致
- [ ] **路径准确性**：所有文件路径是精确的（无"相关目录"等模糊描述）
- [ ] **Red Flags 覆盖度**：Red Flags 表格是否覆盖了该 skill 特有的常见错误（非仅复制通用模板）

### 5. 自进化合规（条件触发）

**触发条件**：读待审 SKILL.md 的 frontmatter `self-evolving`。缺省或 `false` → **跳过本维度，不报任何问题**。`true` → 执行下列校验。

**校验基准**：对照注入的 spec-skill「Self-Evolution Capability」章节（Required Input 已含 spec-skill 全文，**天然是最新版**——本维度以该当前定义为准，无需技能自带版本号）。过程准则采**全局母本直接注入**模型：技能不各存副本，启动时直引母本绝对路径。逐项查：

- [ ] **经验库** `references/lessons.md` 存在，且在 SKILL.md 启动时 `!`cat``（an alternate runtime 兼容技能用 `Read`）注入
- [ ] **修订日志** `references/changelog.md` 存在
- [ ] **末尾总结 / 收尾 Dogfooding** step 存在于流程
- [ ] **过程准则全局母本注入**：SKILL.md 启动注入区有一行**直接注入母本绝对路径** `${CLAUDE_PLUGIN_ROOT}/skills/spec-skill/references/self-evolution-canonical.md`（`$HOME`/`~` 前缀，非 `${CLAUDE_SKILL_DIR}` 本地副本）。裁决漏斗 / 写入闸 / 整合 / changelog 纪律 / 先验后做全靠它进上下文

判级规则：
- 某组件**完全缺失** → `Critical`，Fix 写「应新增（对应 spec 组件）」
- 经验库 / 母本注入是复合判据：**文件或母本路径在但未实际注入**（漏了 `!`cat``/`Read` 行）按 `Critical` 处理——运行时进不了上下文，等同缺失。
- **母本注入指向本地副本**（仍写 `${CLAUDE_SKILL_DIR}/references/self-evolution.md` 旧路径）→ `Important`，Fix 写「应改为直接注入全局母本绝对路径」
- **技能目录下残留 `references/self-evolution.md` 本地副本**（旧模型遗留）→ `Important`，Fix 写「应删除本地副本，过程准则统一注入全局母本」

**反向检查（标记缺省时也做）**：若 frontmatter **无** `self-evolving`，但该技能是重复使用型工作流且组件**实际齐备**（经验库 / 母本注入 / changelog / 收尾 Dogfooding 都在，实做了却没声明）→ `Suggestion`，Fix 写「应在 frontmatter 补 `self-evolving: true`，让 review 能据此校验」。这是触发门控之外唯一在标记缺省时仍输出的情形。

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
