上次整合: 2026-07-06

task-execute（实现期）经验库。两段式自进化「提议」端收件箱：运行段沉淀候选（带「建议出口」标记），固化由 skill-revise 双盲测试后执行。硬上限 ≤15 条。

| 经验 | 重要度 | 建议出口 | 来源 | 上次命中 |
|---|---|---|---|---|
| 并行派发独立组件 task 前先对跨批次共享地基做冒烟（如测试框架能否渲染目标组件）——单 task 局部绕开会掩盖地基级阻塞 | 7 | 正文（并行派发前加共享地基冒烟检查点） | 795a5c23：jest-expo winter runtime 双重不兼容，T7 绕开掩盖 components 项目整体已坏，主 agent 前置 spike 才暴露 | 2026-06-24 |
| 仓库 baseline 本就非全绿时，「验收全绿」解读为「无新增失败 + 新测试通过」，先做 baseline 预检 | 5 | 正文（验证步骤加 baseline 预检一句） | 570deec3：2026-06-21 test_release_notes_parser 2 个既存失败与任务无关 | 2026-06-21 |
| Phase 4 内已完成配置的决策（per_task_review=each）被当成开放问题重新征求许可，task 边界被误当确认点——SKILL.md 需加显式规则：「连续执行 plan tasks，不在 task 边界停下征求继续许可；仅在撞卡点/连续失败 3 次/发现 plan 外系统性问题/Phase 边界时停」 | 7 | 正文 | 8d567cf4 friction：2026-07-07 CatGotcha M9(ISSUE)，preset=full，用户反馈"执行阶段其实不用老是停下来问我" | 2026-07-07 |
