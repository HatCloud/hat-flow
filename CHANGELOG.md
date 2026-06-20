# Changelog

All notable changes to hat-flow are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions use the plugin's
`hat-flow--vX.Y.Z` tag scheme.

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

[0.4.0]: https://github.com/HatCloud/hat-flow/releases/tag/hat-flow--v0.4.0
[0.3.1]: https://github.com/HatCloud/hat-flow/releases/tag/hat-flow--v0.3.1
