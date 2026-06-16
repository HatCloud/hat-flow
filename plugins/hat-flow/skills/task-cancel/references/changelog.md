# Changelog

最新在最上。

## 2026-06-15

- 合规卫生（revise-skill 批量订正）：
  - 新建本 changelog。
  - 族内契约对齐：`Unattended State` 步骤改为从 phases.md 所在路径解析 task-folder（与 task-revise 一致），不再用 `{open[0].path}/unattended.json`，避免多任务取错状态。
  - Dependencies 一致性：README 去掉不存在的 `PROCESS_REVIEW_TEMPLATE.md` 引用（Process Review 由 retrospective 插件 hook 承载）与未实际使用的 `spec-git` 引用（commit 规范由 git 插件提供），与 SKILL Dependencies 取齐。
