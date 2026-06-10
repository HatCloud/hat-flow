# hat-flow

Spec-driven task workflow for Claude Code — a 6-phase lifecycle
(Init → Design → Plan → Execute → Test → End) with a plugin hook system,
independent code/design/plan review, optional Linear and Telegram integration,
and TDD discipline.

## Install

```
/plugin marketplace add HatCloud/hat-flow
/plugin install hat-flow@hat-flow
```

Then run `/task-setup` to configure Linear identity, optional Telegram
notifications, enabled plugins, and output language.

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
