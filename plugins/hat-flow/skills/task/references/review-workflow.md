# Full-Review Workflow 后端（可选 · 探测回落）

P4.post-execute/full-review 的「多维并行 reviewer 扇出 + 逐 finding 对抗验证」生产段的 Workflow 编排骨架。**仅当 `review.workflow_backend: true` 且运行时探测到 Workflow 工具可用时启用；否则静默回落主 session 派发**（见 `plugins/review.md` 的「执行后端」节）。

## 三守卫（任何改动不得突破）

1. **不写 phases.md** —— Workflow 只产 findings，4b 行由主 session 收口写。
2. **不触发 hook** —— P4.post-execute hook 由主 session 边界调用，Workflow 内不调 `hat-plugin-hook`。
3. **缺失静默回落** —— 探测不到 Workflow 工具 → 主 session 派 code-reviewer（现有 background + JOIN）。

## 输入（主 session 解析后经 `args` 传入）

- `dimensions`: 维度自适应表得出的分配（1/2/4 项，每项 `{key, checklist_excerpt, model}`；`key` 如 PLAN_ALIGNMENT/CODE_QUALITY/ARCHITECTURE/TESTING；架构型 review 的 ARCHITECTURE 项 `model='opus'`，其余 `'sonnet'`）。
- `diff_text`: `git diff <range>` 的实际输出（主 session 先跑、避免 Workflow agent 内 cwd/范围歧义）。
- `acceptance`: design.md `## Acceptance Tests`（如有，注入为「合法实现」判断上下文，不输出 VERDICT、不打分）。

## 脚本骨架

```javascript
export const meta = {
  name: 'full-review',
  description: 'P4 full-review：多维并行 reviewer 扇出 + 逐 finding 对抗验证',
  phases: [{ title: 'Review' }, { title: 'Verify' }],
}

const FINDINGS = {
  type: 'object', additionalProperties: false,
  required: ['dimension', 'findings', 'counts'],
  properties: {
    dimension: { type: 'string' },
    findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      required: ['id', 'severity', 'title', 'file', 'evidence_diff_lines'],
      properties: {
        id: { type: 'string' }, severity: { type: 'string', enum: ['Critical', 'Important', 'Minor'] },
        title: { type: 'string' }, file: { type: 'string' },
        evidence_diff_lines: { type: 'string', description: '引用真实 diff 行作核实证据' },
      },
    } },
    counts: { type: 'object', additionalProperties: false, required: ['critical', 'important', 'minor'],
      properties: { critical: { type: 'number' }, important: { type: 'number' }, minor: { type: 'number' } } },
  },
}
const VERDICT = {
  type: 'object', additionalProperties: false, required: ['id', 'is_real', 'evidence'],
  properties: { id: { type: 'string' }, is_real: { type: 'boolean' }, evidence: { type: 'string' } },
}

phase('Review')
const reviewed = await pipeline(
  args.dimensions,
  // 第一跳：每维度一个 code-reviewer 生产 findings
  d => agent(
    `按 CODE_REVIEW.md 的 ${d.key} 维度 checklist 审查下面的 diff。逐条 finding 必须引用真实 diff 行作证据；implementer 的说辞不算证据。
【checklist】\n${d.checklist_excerpt}\n【diff】\n${args.diff_text}\n${args.acceptance ? '【验收上下文（合法实现判断依据，勿输出 VERDICT）】\n' + args.acceptance : ''}`,
    { label: `review:${d.key}`, phase: 'Review', model: d.model, agentType: 'code-reviewer', schema: FINDINGS }),
  // 第二跳：逐 finding 对抗验证（无 barrier 流水；某维度 review 完即开始 verify）
  (rev, d) => parallel((rev?.findings || []).map(f => () =>
    agent(`对抗验证下面这条 review finding 是否真实（读真实 diff 核实，默认怀疑、可判误报）：\n${JSON.stringify(f)}\n【diff】\n${args.diff_text}`,
      { label: `verify:${f.file}`, phase: 'Verify', model: 'sonnet', schema: VERDICT })
      .then(v => ({ ...f, dimension: rev.dimension, verdict: v })))),
)

const flat = reviewed.flat().filter(Boolean)
const confirmed = flat.filter(f => f.verdict?.is_real)
const counts = flat.reduce((a, f) => {
  if (!f.verdict?.is_real) return a
  const s = f.severity.toLowerCase(); a[s] = (a[s] || 0) + 1; return a
}, { critical: 0, important: 0, minor: 0 })
return { confirmed, counts, dropped_as_false_positive: flat.length - confirmed.length }
```

## 主 session 收口（Workflow run 完成后）

1. 读 `confirmed` findings，**批判性消费**（hatflow-receiving-code-review 纪律：仍可反驳 verifier 误判，verifier 把真 finding 判成误报会漏审）。
2. 判 C/I：`counts.critical==0 && counts.important==0` → 通过；否则就地修复 → 下一轮（重跑改动维度的 Workflow，或回落主 session 收敛循环）。
3. **写 phases.md 4b 行 + 调 P4.post-execute hook + 可能转 Revise** —— 全部主 session 做，Workflow 不碰。

## A/B 对账（首次启用必做）

对同一 task 跑两次：现状（主 session `SendMessage` 复活，基线 avg 3426 token/次）vs Workflow（journal-resume）。对账 output token + 稳定性（漏审率、误报过滤准确度），净收益为正再常开 `review.workflow_backend`。
