# Changelog

All notable changes to hat-flow are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions use the plugin's
`hat-flow--vX.Y.Z` tag scheme.

## [0.5.0]

### Changed
- Execute (P4) now runs zero-blocking: no interactive prompts inside the
  execute loop; abnormal states (e.g. a TDD RED check passing unexpectedly)
  stop visibly in-session with a report instead of raising dialogs. Plan →
  Execute handoff supports a fresh-session handover when context compacts.
- Task phase skills (init / execute / end / setup) slimmed to explicit word
  budgets; operational rules unchanged, background material moved into each
  skill's `references/`.
- Bundled discipline skills (systematic-debugging, test-driven-development,
  dispatching-parallel-agents, receiving-code-review,
  verification-before-completion) fully adopted: Chinese trigger words,
  per-skill changelogs, upstream idioms cleaned, large slim-downs;
  systematic-debugging auxiliary files moved under `references/`.

### Fixed
- Packaging no longer ships tests for scripts that are not part of the
  distribution (BIN_EXCLUDE invariant), removing 76 spurious build-test
  failures in clean environments.
- Stale cross-references corrected across the suite (e.g. task-test pointing
  at a nonexistent section of verification-before-completion).

## [0.4.0]

### Changed
- Plugin hook engine rewritten from bash + `jq` to single-pass Python. `jq` is
  no longer a required dependency for the core workflow.
- Plugin manifests merged into each plugin's SKILL.md frontmatter — one fewer
  file per plugin, parsed in a single pass.

### Removed
- Timing / observability instrumentation removed entirely: the
  `hat-timing-stamp` script and all `observability` config keys are gone.
- Subagent-async dispatch machinery removed; plugin hooks run inline.

### Notes
- This distribution ships with the self-evolution (retrospective) capability
  disabled by default.

## [0.3.1]

### Added
- Headless / unattended mode: `claude -p '/task -q <task>'` runs a task end to
  end with no prompts. Activated by an explicit `-q` / `--quiet` / `--headless`
  signal (no auto-detection of `-p`).
- Three-layer configuration: default template < global user
  (`~/.claude/task-defaults.local.json`) < project-local
  (`<project-root>/task-defaults.json`) < call-time flags.
- Worktree isolation (`branch.worktree`): unattended runs default to an isolated
  git worktree + task branch; the main directory HEAD never moves. Per-project
  opt-out via `branch.worktree:false`.
- Graduated degrade policy for unattended runs (`conservative`): reversible
  stop-points (non-converging review, debt reconciliation) continue with a
  recorded trace; irreversible / high-risk points still hard-stop.

[0.5.0]: https://github.com/HatCloud/hat-flow/releases/tag/hat-flow--v0.5.0
[0.4.0]: https://github.com/HatCloud/hat-flow/releases/tag/hat-flow--v0.4.0
[0.3.1]: https://github.com/HatCloud/hat-flow/releases/tag/hat-flow--v0.3.1
