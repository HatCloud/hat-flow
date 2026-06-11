# hat-flow

**English** · [中文](./README.zh-CN.md)

Spec-driven task workflow for Claude Code — a disciplined 6-phase lifecycle
(**Init → Design → Plan → Execute → Test → End**) with a plugin hook system,
independent code/design/plan review, optional Linear and Telegram integration,
and TDD discipline. It turns an ad-hoc coding request into a repeatable,
resumable, reviewable engineering process.

## Features

- **6-phase lifecycle** — every task flows through Init → Design → Plan →
  Execute → Test → End, with cross-session state persisted in `phases.md`.
- **Plugin hook system** — review, Linear, git, TDD and retrospective
  capabilities attach at phase boundaries and toggle per task via presets
  (`full` / `standard` / `lite` / `hotfix`).
- **Independent review** — dedicated code / design / plan reviewers run as
  read-only subagents, separate from the agent doing the work.
- **TDD discipline** — optional red-green-refactor enforcement with timing
  instrumentation.
- **Resumable across sessions** — the orchestrator reads `phases.md` to know
  exactly where to pick a task back up.

## Requirements

These tools must be on your `PATH` before installing:

- **`jq`** — required. The plugin hook engine parses manifests/config with it;
  without `jq` all task-workflow plugins (review/linear/git/timing) silently
  fail to fire. Install: `brew install jq` / `apt-get install jq`.
- **`python3`** (3.8+) — required. Several workflow helpers and bin scripts run
  on it.
- **`node`** (with `npx`) — only needed for the optional Linear integration
  (`@hatcloud/linear-mcp` is launched via `npx`).

Running `/task-setup` performs a preflight check and reports anything missing.

## Install

```
/plugin marketplace add HatCloud/hat-flow
/plugin install hat-flow@hat-flow
```

Then run `/task-setup` to configure Linear identity, optional Telegram
notifications, enabled plugins, and output language.

## Quick start

1. `/task-setup` — one-time first-run configuration (dependency preflight,
   Linear, plugins, language).
2. `/task <your task description>` — start a task; the orchestrator drives it
   through all six phases.
3. `/task` (no args) in a later session — resume the in-progress task where it
   left off.
4. `/task-end` — close out a finished task (final report, retrospective,
   archive).

## Plugins

| Plugin | What it does | Default |
|---|---|---|
| `review` | Independent code/design/plan review at phase boundaries | on |
| `linear` | Sync the task to a Linear issue (status + design/plan/archive comments) | auto (on when configured) |
| `git` | Conventional commits, branch naming, dirty-tree checks | on |
| `tdd` | Red-green-refactor enforcement per execute task | preset-dependent |
| `retrospective` | Post-archive process review | preset-dependent |

Presets pick sensible defaults; `/task-setup` and per-task tuning let you
override any of them.

## Optional integrations

- **Linear** — set the `linear_api_key` user config; the `@hatcloud/linear-mcp`
  server is launched via `npx`. Without a key, the Linear plugin disables itself.
- **Telegram** (unattended-mode notifications) — install the companion
  `telegram@claude-plugins-official` plugin and run `/telegram:configure`.

## Attribution

Bundles four adapted skills from [obra/superpowers](https://github.com/obra/superpowers)
(MIT) under a `hatflow-` prefix (`hatflow-systematic-debugging`,
`hatflow-verification-before-completion`, `hatflow-dispatching-parallel-agents`,
`hatflow-receiving-code-review`). To use the auto-triggering upstream versions,
install obra/superpowers directly — the `hatflow-` prefix keeps both side by side.

## License

MIT — see [LICENSE](./LICENSE).
