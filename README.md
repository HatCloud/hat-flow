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

## Upgrade

The plugin has **no auto-update** — you must trigger it manually and restart
Claude Code for the new version to load.

### Manual upgrade

In a terminal:

```text
/plugin update hat-flow
```

Then restart Claude Code (the plugin is loaded at startup; the new version
won't take effect until then).

**Verify the new version is active** after restart:

- `/plugin` → check the `hat-flow` row's version
- Or: `cat ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json | grep version`

**If `/plugin update` fails** (network / cache issue), reinstall the
marketplace entry:

```text
/plugin marketplace remove hat-flow
/plugin marketplace add https://github.com/HatCloud/hat-flow.git
/plugin install hat-flow@hat-flow
```

### AI-assisted upgrade (let Claude Code do it)

Paste this into a Claude Code session:

```text
Upgrade the hat-flow plugin for me.

1. Run `/plugin update hat-flow`. If it fails with a network or cache error:
   - `/plugin marketplace remove hat-flow`
   - `/plugin marketplace add https://github.com/HatCloud/hat-flow.git`
   - `/plugin install hat-flow@hat-flow`
2. Tell me to restart Claude Code (the new version only loads on restart).
3. After restart, verify the new version is active:
   - run `/plugin` and check the hat-flow row
   - or: `cat ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json | grep version`
   If the version hasn't changed, stop and tell me — something is wrong.
4. If I have local task-defaults.json files
   (`~/.claude/task-defaults.local.json` or `<project>/task-defaults.json`),
   diff them against the new schema in
   `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json`. Flag any keys that
   no longer exist or have changed meaning — but DO NOT modify my files
   without confirming first.
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

## Task parameters

Task behavior is configured by **command-line flags + three config layers +
mode semantics**. This section is the authoritative reference for every
parameter and its default in each mode.

### Command-line flags

The `/task` orchestrator parses `$ARGUMENTS` in Step 0 before any phase runs.
Flag overrides become sparse JSON merged as layer ④ via
`hat-task-config-resolve --flags`.

| Flag | Maps to | Effect |
|------|---------|--------|
| `-q` / `--quiet` | (mode flag) | Enable Quiet mode + `degrade_policy → conservative` |
| `--headless` | (mode flag) | Enable Headless mode + `degrade_policy → headless` (M1 currently behaves as conservative) |
| `--worktree on\|off\|ask` | `branch.worktree` | Force worktree isolation behavior |
| `--no-worktree` | `branch.worktree = false` | Shorthand for `--worktree off` |
| `--branch keep\|new` | `branch.mode` | Force branch strategy |
| `--preset <name>` | top-level `preset` | Override default preset (`full` / `standard` / `lite` / `hotfix`) |
| First positional arg matching a preset name | top-level `preset` | Tier shortcut |

### Configuration reference (`task-defaults.json`)

> **Legend:** `"ask"` is a sentinel value resolved at config time — quiet /
> headless resolves it to `true`, interactive keeps it as `"ask"` (1d prompts
> the user). `"auto"` plugin values are resolved at task-init time against the
> local environment (Linear / git detection).

#### `preset` (top-level)

| Default | Values | Function |
|---------|--------|----------|
| `standard` | `full` / `standard` / `lite` / `hotfix` | Selects a preset block from `presets.*` to deep-merge onto the baseline. |

#### `branch.*` — task branch & worktree isolation

| Key | Type | Interactive | Quiet | Headless | Function |
|---|---|---|---|---|---|
| `branch.mode` | enum | 1d prompts (default `keep`) | config (default `keep`) | config | `keep` stays on current branch; `new` creates a task branch. |
| `branch.worktree` | tri-state | `"ask"` prompts (default `false`) | `"ask"` → `true` | `"ask"` → `true` | Explicit `true` / `false` overrides in every mode. |
| `branch.name` | string\|null | `null` (auto from folder) | same | same | Explicit branch-name override. |

#### `headless.*` — only effective when `unattended.json enabled == true`

| Key | Type | Default | Function |
|---|---|---|---|
| `headless.existing_task` | enum | `continue` | Continue the existing task vs. start a new one. |
| `headless.git_conventions` | enum | `default` | Fallback when no git-convention spec is found (`default` / `implicit` / `skip`). |
| `headless.dirty_policy` | enum | `ignore` | How to handle a dirty tree (`ignore` / `stash`). |
| `headless.degrade_policy` | enum | `conservative` | Crash / stop-point handling tier (`standard` / `conservative` / `headless`); interactive mode is always `standard`. |
| `headless.linear_on_fail` | enum | `skip` | Linear API failure behavior (`skip` / `retry`). |

#### `end_decisions.*` — Phase 6 auto-decision defaults

| Key | Type | Default | Function |
|---|---|---|---|
| `end_decisions.branch` | enum | `keep` | `auto_merge` merges back to main; `keep` keeps the branch. `PR` / `Discard` are never auto-triggered. |
| `end_decisions.claude_md` | enum | `auto_update` | Whether to auto-update project `CLAUDE.md`. |
| `end_decisions.squash` | bool | `true` | Squash task commits into one at End (`merge --squash` for branch merge; `reset --soft` for direct-on-main). Set `false` to disable. |

#### `execution.*` — Phase 4 dispatch

| Key | Type | Default | Function |
|---|---|---|---|
| `execution.mode` | enum | `auto` | `auto` decides per batch (independent 2+ with no interdep → `parallel-agents`; coupled / single → `inline`); `inline` runs sequentially in the main agent; `parallel-agents` dispatches every isolatable task to `task-executor`. Legacy `subagent` is migrated to `auto`. |
| `execution.engine` | enum | `auto` | Only affects dispatched subagents: `auto` picks Sonnet / Opus from (difficulty, TDD, complexity); explicit `sonnet` / `opus` overrides. Inline tasks always run on the main agent's current model. |

#### `plugins.review.*` — independent review

| Key | Type | Default | Function |
|---|---|---|---|
| `plugins.review.enabled` | bool | `true` | Master switch. |
| `plugins.review.design_rounds` | mixed | `auto` | `auto` decides from complexity (Low:0, Medium:1, High:1–2); number = fixed rounds. |
| `plugins.review.code_review` | enum | `medium` | Depth: `skip` / `light` / `medium` / `full`. |
| `plugins.review.per_task_review` | enum | `each` | `each` = review after every plan task (finest); `checkpoint` = only at the P4.post-execute full review. |
| `plugins.review.reviewer` | enum | `claude` | Reviewer type (currently only `claude`). |
| `plugins.review.max_rounds` | int (1–5) | `3` | Max reviewer rounds before forced converge. |

#### `plugins.linear.*` — Linear integration

| Key | Type | Default | Function |
|---|---|---|---|
| `plugins.linear.enabled` | tri-state | `auto` | `auto` decides from project `CLAUDE.md ## Linear` / `linear.json` / MCP availability; resolves to `true` / `false` in `task-config.json`. |
| `plugins.linear.update_description` | bool | `true` | Update issue description. |
| `plugins.linear.upload_docs` | bool | `true` | Upload design / plan docs. |
| `plugins.linear.sync_sub_issues` | bool | `true` | Sync sub-issues. |

#### `plugins.git.*` — git conventions

| Key | Type | Default | Function |
|---|---|---|---|
| `plugins.git.enabled` | tri-state | `auto` | `auto` = detect git repo (NO_GIT forces `false`). |

#### `plugins.tdd.*` — TDD enforcement

| Key | Type | Default | Function |
|---|---|---|---|
| `plugins.tdd.enabled` | bool | `false` | Overridden by presets (`full` / `standard` → `true`; `lite` / `hotfix` → `false`). |
| `plugins.tdd.mode` | enum | `none` | `none` / `lite` / `full`; `mode != none` auto-sets `enabled = true`. |

#### `plugins.retrospective.*` — post-archive self-review

| Key | Type | Default | Function |
|---|---|---|---|
| `plugins.retrospective.enabled` | bool | `false` in this distribution | Disabled by the export override (`apply_export_overrides`). |

#### Top-level non-plugin keys

| Key | Type | Default | Function |
|---|---|---|---|
| `observability.enabled` | bool | `false` in this distribution | Gates `hat-timing-stamp` writes; disabled by the export override. |
| `todo_sync` | bool | `true` | Sync `phases.md` to `TaskCreate` / `TaskUpdate` UI. |
| `phase_merge` | array | `[]` | E.g. `[[3,4]]` skips the P3→P4 pause. **P5→P6 can never be merged.** |

### Presets

| Preset | `execution.mode` | `tdd.mode` | `code_review` | `per_task_review` | `retrospective` | `observability` | `todo_sync` | Typical use |
|--------|------------------|------------|----------------|--------------------|------------------|-----------------|--------------|------------|
| `full` | `auto` | `full` | `full` | `each` | `true` | `true` | `true` | Large refactors, contract-sensitive work |
| `standard` (default) | `auto` | `lite` | `medium` | `each` | `true` | `true` | `true` | General-purpose |
| `lite` | `inline` | `none` | `light` | `each` | `false` | `true` | `true` | Small changes, docs |
| `hotfix` | `inline` | `none` | `skip` | (skipped) | `false` | **`false`** | **`false`** | Emergency fixes (minimum overhead) |

> Override any field via layer ② (`~/.claude/task-defaults.local.json`),
> layer ③ (`<project>/task-defaults.json`), or call-time flag (highest).

### Mode comparison

| Aspect | Normal (interactive) | Quiet (`-q` / `--quiet` / 「无人值守」) | Headless (`--headless`) |
|--------|----------------------|---------------------------------------|--------------------------|
| `quiet_mode` | `false` | `true` | `true` |
| `degrade_policy` | `standard` (always) | `conservative` | `headless` (M1 ≈ conservative) |
| Init stop-points | prompt user | resolve from config | resolve from config |
| `branch.mode` 1d prompt | yes | no (use config) | no (use config) |
| `branch.worktree = "ask"` | prompts (default `false`) | `true` | `true` |
| Compact soft-stop (Plan→Execute) | emitted | skipped | skipped |
| Telegram notifications | — | opt-in | opt-in |
| `unattended.json` written at | step 2A.1 (interactive ask) | task-init `1f` directly | task-init `1f` directly |

> "Quiet" and "headless" differ only in `degrade_policy` semantics today
> (headless is reserved for future stronger behavior). Both pass through the
> same stop-point auto-decisions.

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

### Optional: Telegram task notifications (unattended mode)

Unattended runs can broadcast progress, decisions, and stop-point notifications to
a Telegram chat — opt-in, no setup required to skip (notifications just
degrade to a `★` warning line in the session log).

**What it is** — the workflow calls the Telegram Bot API directly
(`https://api.telegram.org/bot<token>/sendMessage`) when an unattended task
hits a notification moment (phase transition, key auto-decision, validation
failure, task complete). No MCP plugin required for sending — the companion
`telegram@claude-plugins-official` plugin is used only for **access control**
(`access.json`) and pairing.

**Setup (one-time, three steps):**

1. Install the companion plugin:
   ```
   /plugin install telegram@claude-plugins-official
   ```
2. Pair the bot with your Telegram account and lock it down to yourself:
   ```
   /telegram:configure <your-bot-token-from-BotFather>
   /telegram:access policy allowlist   # after pairing — drops pairing codes
   ```
3. Persist your `chat_id` to the **personal local config** (not a repo file —
   keeps your identifier out of the distribution):
   ```bash
   mkdir -p ~/.claude
   echo "{\"telegram_chat_id\": \"<your chat id>\"}" > ~/.claude/task-defaults.local.json
   chmod 600 ~/.claude/task-defaults.local.json
   ```
   Find your `chat_id` from `~/.claude/channels/telegram/access.json`
   (`allowFrom[0]`) or by sending any message to your bot and reading
   `https://api.telegram.org/bot<token>/getUpdates`.

**Where the value comes from** (resolution order — first hit wins):

1. The current session was started **from Telegram** (`<channel source="telegram">`) — `chat_id` is read from the inbound message.
2. Your personal local config — `~/.claude/task-defaults.local.json` → `telegram_chat_id`. **Recommended for CLI sessions.**
3. The shared task-defaults (`${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` or project-local `<project>/task-defaults.json`). **Not recommended** — the shipped default is `null` (opt-out) and committing a real chat_id leaks your identifier.
4. None of the above — `telegram_chat_id = null`, all Telegram notifications skip with `★ Telegram 通知降级：chat_id 未配置 — ...`. Workflow continues unaffected.

**Security note** — your `chat_id` and bot token are personal identifiers. The
shipped `${CLAUDE_PLUGIN_ROOT}/skills/task/task-defaults.json` deliberately
holds `null` for `telegram_chat_id`; do **not** commit a real value to any
file inside the plugin repo. Always use the personal local config or the
plugin's own `~/.claude/channels/telegram/.env` for secrets.

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
