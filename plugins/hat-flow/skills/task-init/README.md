# task-init

Phase 1（Setup）worker：解析用户输入、确认需求、档位粗选、设置 git 分支 / worktree、处理 Linear 集成，创建任务文件夹与 `phases.md` 等状态文件。由 `/task` 编排器在新任务时派发，也可单独调用。完整步骤、停点与产物清单以 `SKILL.md` 为准。

## 补充信息

- **phases.md 的地位**：init 生成的 `phases.md` 是整个 task 族跨 session 恢复的唯一状态锚——后续每个 phase skill 都靠它定位「从哪一步继续」，因此它必须在 Phase 1 就物化，而不是等设计完成。
- **档位两阶段设计**：1b.3 只做粗选（full/standard/lite/hotfix 自动推荐 + 插件 frontmatter 建议规则裁剪），精调留给 Phase 2 Step 2e——init 时对任务复杂度的信息量不足，一次定死会频繁误判。
- **配置合并**：写入 task-config.json 前经 `bin/hat-task-config-resolve` 三层合并（默认模板 < 全局 local < 项目本地 < 调用 flag）。
