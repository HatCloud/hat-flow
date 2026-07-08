# Code Review Protocol

由 SKILL.md 动态路由加载。针对代码变更进行结构化 review。支持两种模式：Light（单 agent 快速检查）和 Full（按维度深度审查）。

## Two Modes

| Mode | Scenario | Agent Count | Scope |
|------|----------|-------------|-------|
| **Light** | 每个 task 完成后 | 单 agent | 当前 task 的 diff |
| **Full** | 所有 task 完成后 | 每维度 1 个 agent（由 task skill 并行派发） | 完整分支 diff |

Full 模式下，task skill 按 diff 自适应并行派发 **1-4 个** reviewer subagent（由 review.md 的维度自适应 + 下方维度合并 Reviewing 决定数量），每个 agent 覆盖分配给它的维度。每次调用执行所分配维度的 checklist。

---

## Light Mode

### Required Input

| Input | Description |
|-------|-------------|
| git diff | 当前 task 的代码变更 |
| plan.md task section | plan.md 中对应当前 task 的段落 |

<rule>
review 开始前先检查所有必要输入，缺失 diff 或 plan section 即以报错终止。
Reason: 不知道代码该做什么（plan）就做 review，会沦为只看 style 的 review，漏掉功能性缺口。
</rule>

### Checklist

<!-- STAGE-1-START -->
1. **Plan Alignment** — 实现是否匹配 plan 中当前 task 的每个步骤？是否有遗漏的步骤或超出范围的变更？
<!-- STAGE-1-END -->
<!-- STAGE-2-START -->
2. **Obvious Bugs** — 是否有明显的 bug：空指针/undefined 访问、数组越界、资源泄漏（未关闭的 handle/connection）、死循环？
3. **Error Handling** — 外部调用（API、文件 I/O、数据库）是否有错误处理？错误是否被正确传播或处理？
4. **Code Style Consistency** — 代码风格是否与项目现有风格一致？命名约定、缩进、import 顺序。
5. **Debug Leftovers** — 是否有遗留的调试代码？`console.log`、`print`、`debugger`、注释掉的代码块。
6. **Type Safety** — 是否有 `any` 类型、未检查的类型断言（`as`）、隐式类型转换？
<!-- STAGE-2-END -->

---

## Full Mode

### Required Input

| Input | Description |
|-------|-------------|
| git diff | 完整分支的代码变更 |
| plan.md full text | 完整的实施计划 |
| design.md full text | 完整的设计文档 |
| Dimension | PLAN_ALIGNMENT / CODE_QUALITY / ARCHITECTURE / TESTING |

<rule>
review 开始前先检查所有必要输入并校验 dimension 参数，输入缺失或 dimension 非法即以报错终止。
Reason: 每个 dimension 都需要完整上下文才能准确评估 cross-cutting concerns。
</rule>

仅执行指定维度的 checklist，不混合维度。Output 的 Type 字段格式为 `CODE-FULL-{DIMENSION}`，如 `CODE-FULL-PLAN_ALIGNMENT`；Light 模式使用 `CODE-LIGHT`。

### 维度合并 Reviewing（小 diff 档）

当 review.md 按 diff 规模派发 <4 个 reviewer agent 时，单个 agent 须覆盖**多个维度的 checklist**：

| 派发数量 | 合并方式 | 覆盖范围 |
|---------|---------|---------|
| 1 个 agent（极小 diff） | 全量合并 | 逐项覆盖全部 4 个维度 checklist（Dimension 1–4） |
| 2 个 agent | 按 review.md 维度分工 | 每 agent 覆盖分配给它的 2 个维度 checklist |
| 4 个 agent | 各负责 1 个维度 | 默认行为，无合并 |

合并时执行原则：**不省略任何维度的 checklist 条目**——每条都要检查并给出结论，即便某条在当前 diff 中不适用（标注"N/A — 原因"）。

### Dimension 1 — Plan Alignment

审查实现与计划的一致性：

1. **Step Coverage** — plan.md 中每个 task 的步骤是否都在 diff 中有对应实现？逐条对照，列出未实现的步骤。
2. **Scope Creep** — diff 中是否有超出 plan 范围的变更？列出 plan 未提及但被修改的文件或功能。
3. **File Manifest** — 文件创建/修改是否与 plan 中各 task 的 **Files** 列表一致？是否有遗漏或多余？
4. **Goal Traceability** — design.md 的每个 Goal 是否在代码中有体现？从 Goal → plan task → code 的链路是否完整？

### Dimension 2 — Code Quality

审查代码质量和工程实践：

1. **DRY** — 是否有重复代码块（>5 行相同或高度相似的逻辑）？建议提取方式。
2. **Error Handling** — 每个外部调用（API、文件 I/O、数据库、子进程）是否有错误处理？是否有 catch-and-swallow（吞掉错误不处理）？
3. **Type Safety** — 是否有 `any` 类型、未检查的类型断言、隐式类型转换？泛型使用是否恰当？
4. **Edge Cases** — 是否处理了边界情况：空数组、空字符串、undefined/null、极大值、负数？
5. **Naming** — 变量/函数/类名是否描述性且一致？是否有单字母变量（循环计数器除外）或歧义命名？
6. **Leftovers** — 调试代码、注释掉的代码块、未处理的 TODO、临时 hack。

### Dimension 3 — Architecture

审查架构设计和系统层面的问题：

1. **Pattern Consistency** — 新代码是否遵循项目现有的架构模式（MVC、模块化、组件化等）？是否引入了不一致的模式？
2. **Separation of Concerns** — 是否有业务逻辑泄漏到 UI/表现层，或反之？各层的职责是否清晰？
3. **Performance** — 是否有 N+1 查询、不必要的循环嵌套、大数据结构的不必要复制、阻塞主线程的操作？
4. **Security** — 是否有敏感数据暴露（硬编码密钥、日志中的 PII）、未授权操作、用户输入未验证（XSS、注入）？
5. **Module Boundaries** — 新代码是否尊重现有的模块边界和抽象层？是否有跨层直接调用或循环依赖？

### Dimension 4 — Testing

审查测试覆盖和测试质量：

1. **Test Coverage** — 每个新功能或行为修改是否有对应测试？列出缺少测试的功能。
2. **Assertion Quality** — 测试是否只检查"不报错"（弱断言）还是检查具体预期值（强断言）？`expect(result).toBeDefined()` vs `expect(result).toEqual(expectedValue)`。
3. **Edge Case Coverage** — 测试是否包含边界输入：空值、极值、非法输入、异常路径？
4. **Test Isolation** — 测试之间是否有共享状态（全局变量、数据库状态）导致的潜在干扰？测试顺序是否影响结果？
5. **Mock Reasonability** — mock 是否过度（掩盖真实行为、mock 了不应该 mock 的东西）或不足（测试依赖外部服务、网络）？

---

## Severity Classification

每条 issue 按**实际严重度**归类（三级）。不再使用数值置信度评分——severity 与置信度双轴并存会造成"高置信度的 Important 被当作可跳过"的误判。

| Severity | 含义 | 例子 |
|----------|------|------|
| **Critical (Must Fix)** | bug、安全问题、数据丢失风险、功能损坏、核心逻辑无测试 | "函数在 `arr.length === 0` 时访问 `arr[0]`"；"核心解析逻辑零 happy-path 测试" |
| **Important (Should Fix)** | 架构问题、缺失功能、错误处理缺失、明确的 plan 偏离、测试缺口 | "plan 要求创建 X 文件但 diff 中未出现"；"外部调用无错误处理" |
| **Minor (Nice to Have)** | 代码风格、优化机会、文档润色、命名建议、纯推测性顾虑 | "函数名 `process` 不够描述性" |

校准判据：能导致运行期错误 / 数据损坏 / 安全漏洞 / 核心功能不可用的才是 Critical；"应该改进但不改也能正常工作"是 Important；"锦上添花"是 Minor。滥用 Critical 会让真正的 Critical 失去信号。原先低置信度桶（纯推测、风格偏好）并入 Minor。

结构化的升级规则（pattern → effect）见同目录 `severity-escalation.yaml`；判定犹豫时对照其 `rules` 与 `coverage_thresholds`。

**每条 issue 必须给出：**
1. `file:line` 引用（不可含糊）
2. 错在哪（具体现象）
3. 为何重要（影响）
4. 怎么修（若不显然）

**结尾结论（必给）：**

```
Ready to merge? [Yes | No | With fixes]
Reasoning: [1-2 句技术判断]
```

<rule>
每条论断都逐行对照 diff 核实；「它能工作」只有在读过让它工作的代码之后才成立。这对每次 review 都适用，Light 和 Full 皆然。
Reason: review 存在的意义是抓出 implementer 漏掉或自我合理化掉的问题。reviewer 的价值在于独立核实，而非附和 implementer 的叙述。
</rule>

<HARD-GATE>
真正的 Critical issue 阻断 merge。Critical 始终保持 Critical——不为了让自动化流程放行而降级成 Important。在 Critical 与 Important 之间拿不准时，凡是可能导致 runtime failure、data loss，或让 core logic 处于未测试状态的，一律默认归为 Critical。
Reason: bin-unit-tests 事件——一个严重问题被判为 Important，auto-flow 把 Important 当作可跳过，结果有缺陷的成果被发布。severity 驱动门控，所以一次静默的错误分级就会把 bug 放行出去。
</HARD-GATE>

## Coverage Assessment

先检测项目测试框架（`package.json` scripts、pytest、`go test`、Makefile 等）：

- **无测试框架** → 不强制要求覆盖率（可记 Minor 建议引入，不升级）。
- **有测试框架** → 按代码类型定"低覆盖"的 severity：

| 代码类型 | "低覆盖"判据 | Severity |
|---------|------------|----------|
| 纯逻辑（解析 / 算法 / 状态机 / 数据转换） | 核心路径或 happy-path 无测试 | **Critical** |
| 边界 / 错误处理逻辑 | 异常路径无测试 | Important |
| 界面代码（UI 组件 / 视图） | 关键交互（提交 / 删除 / 支付等）无测试（渲染快照不算） | Important |
| 样板 / 配置 / 类型定义 | — | 不要求 |

界面代码用独立（更低）阈值，因为 UI 自动化测试成本高、单位收益低于逻辑代码；但关键交互仍需测试。

<rule>
core path 没有测试覆盖的纯逻辑新代码归为 Critical，而非 Important。
Reason: 未测试的 core logic 正是静默崩坏的藏身处。UI 代码适用另一条更低的标准，因为 UI 测试每单位保障的成本更高——core logic 没有这种借口。
</rule>

---

## Acceptance Context（验收项作上下文，不打分）

当任务文件夹的 `design.md` 含 `## Acceptance Tests` 时，code review 把这些验收项（含 `[MUST|SHOULD|MAY]` 标签与变体 / 反模式纯文字注记）当作判断"合法实现"的上下文：

- **变体注记**告知哪些替代实现是被允许的——不要把 design 已认可的另一种合法实现误报为问题。
- **反模式注记**告知哪些实现方式应被排除——命中反模式的代码可作为 finding 报告。

reviewer **不输出 VERDICT、不打分**，仍按上方维度 checklist + 三级 severity（Critical/Important/Minor）+ Coverage Assessment 输出。
