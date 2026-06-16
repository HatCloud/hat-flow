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

> **No GitHub SSH key?** The `owner/repo` shorthand clones over SSH and fails
> with `Permission denied (publickey)` if you have no SSH key configured. This
> repo is public — use the explicit HTTPS URL instead:
> `/plugin marketplace add https://github.com/HatCloud/hat-flow.git`
> (If that still hits an SSH error, your git has an `insteadOf` rule rewriting
> GitHub HTTPS→SSH; configure an SSH key or remove that rewrite.)

Then run `/task-setup` to configure Linear identity, optional Telegram
notifications, enabled plugins, and output language.

### Self-install prompt (let Claude Code set it up)

Prefer to let your Claude Code do the install + setup? Paste this into a Claude
Code session — most of it automates; it only stops to ask you the few things
that need a human decision:

```text
Install and configure the hat-flow task workflow plugin for me.

1. Install:
   /plugin marketplace add https://github.com/HatCloud/hat-flow.git
   /plugin install hat-flow@hat-flow
   (restart if Claude Code asks you to)
2. Run /task-setup and complete it. You can do these automatically:
   - dependency preflight (jq / python3 / node)
   - write a project CLAUDE.md skeleton if missing
   - pick a default preset (standard) and write a project-local
     task-defaults.json skeleton (and ~/.claude/task-defaults.local.json for
     my cross-project defaults)
   Ask me only about:
   - Linear: do I want it? if so, team / project / API key
   - Telegram unattended notifications: set up or skip
   - the project's lint / test verification commands
   - whether this project should disable worktree isolation (branch.worktree:false)
3. When done, tell me I can start with /task <description>, or run a fully
   unattended task with:  claude -p '/task -q <task or issue-id>'
```

## Quick start

1. `/task-setup` — one-time first-run configuration (dependency preflight,
   Linear, plugins, language).
2. `/task <your task description>` — start a task; the orchestrator drives it
   through all six phases.
3. `/task` (no args) in a later session — resume the in-progress task where it
   left off.
4. `/task-end` — close out a finished task (final report, retrospective,
   archive).

## Configuration layers

Task behavior resolves through three config layers (later wins), plus call-time
flags:

| Layer | File | Scope |
|---|---|---|
| ① default template | `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` | ships with the plugin; read-only baseline + 4 presets |
| ② global user | `~/.claude/task-defaults.local.json` | your cross-project preferences; **not overwritten by plugin updates** |
| ③ project-local | `<project-root>/task-defaults.json` | per-project overrides — **highest config layer** |
| ④ call-time flag | e.g. `/task --worktree off …` | single-run override, highest precedence |

Merge order: `① default < ② global < ③ project-local < ④ flag < runtime`.
Only write the keys you want to override (a sparse `overrides` object); layers
deep-merge. Example: a repo where several tasks share one working tree sets
`{"branch": {"worktree": false}}` in its project-local `task-defaults.json`,
overriding a global `worktree:true` preference.

Key options: `branch.mode` (`keep` default — stay on the current branch, good
for same-directory multi-task collaboration — / `new`), `branch.worktree`
(`true` / `false` / `"ask"`), and the `headless.*` auto-decisions used in
unattended runs.

## Headless / unattended mode

Run a task start-to-finish with no human present:

```
claude -p '/task -q <task description or issue-id>'
```

- **`-q` / `--quiet` / `--headless`** (or the keyword「无人值守」) turns on
  unattended mode. It is established **only** by this explicit signal — there is
  no reliable way to auto-detect `claude -p`, so **you must pass `-q`** (an
  interactive session and a `-p` session look the same to the workflow).
- In unattended mode the workflow never calls an interactive prompt: every Init
  decision resolves from config (`headless.*`, `branch.*`), and `branch.worktree`
  defaults to **true** (each run is isolated in its own git worktree + task
  branch; the main directory's HEAD never moves).
- Reversible stop-points degrade gracefully (`degrade_policy: conservative`):
  e.g. a design/plan review that does not converge records its open findings and
  continues, instead of stalling. Irreversible / high-risk points (verification
  crash, machine-judgeable MUST-fail, branch discard) still hard-stop.
- Optional Telegram notifications report progress and any pauses.

> Front-load your decisions in Design/Plan; once Execute starts the run is
> hands-off. `branch.worktree:false` in project-local config opts a repo out of
> worktree isolation (back to sharing one working tree).

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

## Changelog

See [CHANGELOG.md](./CHANGELOG.md). Upgrade with `/plugin update hat-flow`
(restart required); there is no auto-update.

## License

MIT — see [LICENSE](./LICENSE).
