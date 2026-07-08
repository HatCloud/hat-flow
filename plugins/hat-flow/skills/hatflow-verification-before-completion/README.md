# hatflow-verification-before-completion

完成前验证。在声称工作已完成、已修复或测试通过之前，必须运行验证命令并确认输出。先有证据，再下结论。

## 触发词

- "验证完成"
- "确认修复"

## 核心原则

- 永远先运行验证命令，再声称成功
- 不基于代码阅读推断通过——必须实际执行
- 把验证输出作为证据展示给用户

## 收编背景

2026-05-24 采纳自 obra/superpowers 的 5 个原子技能之一，2026-06-21 随 ISSUE 范式转变完成陈述式中文化。`user-invocable: false`——用户不会主动敲 `/hatflow-verification-before-completion`，它是被 `task-test`、`hatflow-systematic-debugging` 引用的纪律库，靠触发词激活。与内建 `verify` 技能职责不同：`verify` 驱动被改流程做端到端观察（限有 runtime surface 的代码变更），本技能是覆盖全类声明（测试/lint/构建/bug 修复/agent 委派/需求核对）的证据纪律。经 hat-task-package 以 `hatflow-verification-before-completion` 名义打包进 hat-flow 公开分发。
