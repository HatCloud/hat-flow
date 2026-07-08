# task-setup Changelog

## 2026-07-07 — 正文瘦身至 500 词预算内

- 正文从约 622 词压到 444 词（默认档 500，lint 无超预算 WARN）。
- 仅下沉 / 压缩表述，未改任何流程语义、步骤编号（Step 0–5 + 完成 + Dependencies）、AskUserQuestion 停止点、Step 0 python3 `<rule>` 铁律、Step 5「两字段就位」验收门。
- Step 5（234 词，最大块）：把两向/单向拿 token、chat_id 解析、双字段验证的 bash 操作细节下沉到新建 `references/telegram-notify-setup.md`（条件分支 + 体积大 → 按需 Read，符合 Pre-injection Strategy）。SKILL.md 保留步骤结构、字段落点表（load-bearing）、AskUserQuestion 停止点与验收门，改为指回该 reference。
- Step 0/1/2/3 及 intro：删冗余修饰与重复表述（如「任务流照常运行」类补白），保留全部操作性指令与路径。
- Dependencies 增列新 reference 及 Step 5 的 `.env` / `task-defaults.local.json` 两处 Writes。
