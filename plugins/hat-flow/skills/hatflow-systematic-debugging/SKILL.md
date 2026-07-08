---
name: hatflow-systematic-debugging
description: "[hat-flow bundled dep — invoked explicitly by the task workflow, not auto-triggered] Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. 触发词: \"系统性调试\", \"排查 bug\", \"根因分析\", \"测试失败排查\", \"别瞎猜先查根因"
disable-model-invocation: true
---

# Systematic Debugging

**Announce at start:** "Using hatflow-systematic-debugging to investigate the root cause."

## Overview

随机试错既浪费时间又会引入新 bug；快速打补丁只会掩盖底层问题。本 skill 的核心是：先定位根因，再动手修复——修补症状等同于没修。

**核心原则：** 任何修复之前先完成根因调查。流程的每一步都服务于这一目标。

## The Iron Law

<rule>
No Fixes Without Root Cause Investigation First — 未完成 Phase 1 的调查就提出修复，会把症状当根因处理、引入新 bug 并掩盖真问题。Phase 1 是后续所有 phase 的前置。
</rule>

## When to Use

适用于任何技术问题：测试失败、生产 bug、非预期行为、性能问题、构建失败、集成问题。

以下情形尤其需要本流程（此时跳步的诱惑最大、代价也最大）：

- 时间紧迫的紧急情况——系统化排查比反复试错更快，而非更慢。
- 看似"一个快速修复就行"——第一个修复会定下后续的处理范式，一开始就做对最划算。
- 已经试过多个修复、或上一个修复没生效。
- 问题看似简单——简单 bug 同样有根因，流程对简单 bug 也很快。
- 自己尚未完全理解问题。

## The Four Phases

每个 phase 完成后才进入下一个。

### Phase 1: Root Cause Investigation

任何修复动作之前：

1. **仔细读错误信息**
   - 不略过任何 error 或 warning，它们常常直接包含答案。
   - 完整读 stack trace，记下行号、文件路径、错误码。

2. **稳定复现**
   - 能否可靠触发？确切步骤是什么？是否每次都发生？
   - 无法复现时先收集更多数据，不靠猜测。

3. **检查近期改动**
   - 什么改动可能导致此问题？查 git diff、近期 commit。
   - 新依赖、配置变更、环境差异都在排查范围内。

4. **多组件系统中收集证据**

   当系统含多个组件时（CI → build → signing，API → service → database），在提出修复前先加诊断埋点：

   ```
   对每个组件边界：
     - 记录进入组件的数据
     - 记录离开组件的数据
     - 验证环境/配置是否正确传递
     - 检查每一层的状态

   先跑一次收集证据，看清在哪里断裂
   再分析证据定位失败的组件
   再深入调查那个具体组件
   ```

   多层系统示例：

   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   这样能看出哪一层失败（secrets → workflow ✓，workflow → build ✗）。

5. **追踪数据流**

   当错误深藏在调用栈中时，向上回溯：坏值从哪里产生？谁用坏值调用了这里？一路追到源头，在源头修复而非症状处。完整的回溯技术见 `references/root-cause-tracing.md`。

### Phase 2: Pattern Analysis

修复前先找出模式：

1. **找可用的范例**
   - 在同一代码库里定位类似的、能正常工作的代码。

2. **对照参考实现**
   - 若在套用某个模式，完整读参考实现的每一行，不略读，理解透了再套用。

3. **找出差异**
   - 可用代码与坏代码之间有什么不同？列出每一处差异，再小也列上，不预设"这个不可能有影响"。

4. **理解依赖**
   - 这段代码还需要哪些组件、配置、环境？它做了哪些假设？

### Phase 3: Hypothesis and Testing

用科学方法：

1. **提出单一假设**
   - 明确写下："我认为根因是 X，因为 Y"。具体，不含糊。

2. **最小化测试**
   - 用尽可能小的改动验证假设，一次只动一个变量，不同时修多处。

3. **先验证再继续**
   - 生效 → 进入 Phase 4；未生效 → 提出新假设，不在原修复上叠加更多修复。

4. **不懂就说不懂**
   - 直接说"我不理解 X"，不假装懂；可以求助或继续研究。

### Phase 4: Implementation

修根因，不修症状：

1. **写一个会失败的测试**
   - 最简复现；有框架就写自动化测试，没有就写一次性测试脚本。
   - 修复前必须先有这个失败测试。写规范的失败测试用 `test-driven-development` skill。

2. **实施单一修复**
   - 针对已识别的根因，一次只改一处；不顺手做"反正都来了"的改进或捆绑重构。

3. **验证修复**
   - 测试现在通过了吗？有没有弄坏其他测试？原始问题真的解决了吗？

4. **修复未生效时**
   - 停下，数一下已经试过几次修复。
   - 少于 3 次：回到 Phase 1，带着新信息重新分析。
   - 达到 3 次及以上：停下来质疑架构（见下一步），不要在没有架构层讨论的情况下尝试第 4 次修复。

5. **3 次以上修复失败：质疑架构**

   出现以下迹象说明是架构问题，而非失败的假设：

   - 每个修复都在不同位置暴露出新的共享状态/耦合/问题。
   - 修复都需要"大规模重构"才能落地。
   - 每个修复都在别处制造新症状。

   <rule>
   3+ 修复连续失败时，先停下与人类伙伴讨论根本设计，再尝试更多修复——这是架构错误的信号而非假设错误，继续打补丁只会在别处制造新症状。需要判断：这个模式本身是否站得住脚？是否只是出于惯性在硬撑？应当重构架构还是继续修症状？
   </rule>

## Quick Reference

| Phase | 关键活动 | 完成标准 |
|-------|---------|---------|
| **1. Root Cause** | 读错误、复现、查改动、收集证据 | 理解发生了什么、为什么 |
| **2. Pattern** | 找可用范例、对照 | 识别出差异 |
| **3. Hypothesis** | 提假设、最小化测试 | 假设被确认或换新假设 |
| **4. Implementation** | 写测试、修复、验证 | bug 解决、测试通过 |

## 人类伙伴发出的"方向不对"信号

收到以下重定向时，回到 Phase 1：

- "这个有发生吗？"——你没验证就假设了。
- "它能让我们看到……吗？"——你本该先加证据收集。
- "别猜了"——你在没理解的情况下提修复。
- "重新想想根本设计"——该质疑根本设计，而非只看症状。
- "我们卡住了？"（带挫败感）——当前方法行不通。

## 当流程显示"没有根因"

若系统化调查后确认问题确实是环境性、时序相关或外部因素：

1. 流程已走完。
2. 记录调查过的内容。
3. 实施恰当的处理（重试、超时、错误提示）。
4. 加监控/日志以备后续调查。

多数"没有根因"的判断其实是调查不彻底，确认前先回看 Phase 1 是否真正走完。

## Supporting Techniques

以下技术属于系统化调试的一部分，文件在 `references/`：

- **`root-cause-tracing.md`** — 沿调用栈向后回溯，找到最初触发点。
- **`defense-in-depth.md`** — 定位根因后在多层加校验。
- **`condition-based-waiting.md`** — 用条件轮询取代任意超时。

## Dependencies

- 引用: test-driven-development（Phase 4 步骤 1 写失败测试）
- 引用: hatflow-verification-before-completion（宣称成功前先验证修复确实生效）
- 无预注入依赖
- 无 skill 调用依赖
