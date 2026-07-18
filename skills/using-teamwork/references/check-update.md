# Check Update

Use with `teamwork-init` (readiness) and `teamwork-update` (global refresh).
It checks Teamwork-controlled user surfaces, never project-local Teamwork
packages.

## Checkout Mode

From a Teamwork checkout, `./scripts/check-update.sh` reports source versus
upstream, remote tag, and latest GitHub Release; installed skills, agents, managed
policies, routing, notifications, and bounded content drift for Codex, Cursor,
and Claude Code. `--readiness` prints `MANAGED_INSTALL_READY`,
`HOST_ACTIVATION`, `MANUAL_ACTIONS`, `MISSING`, and `NEXT`; `--no-fetch` skips
remote checks. `INSTALL_READY` is only a compatibility alias for managed file
and config convergence, never proof of live host behavior. In particular,
`codex-routing` drift remains a managed configuration gap, not a claim that a
live custom-agent spawn was observed.

Before checkout-based project initialization, run
`./scripts/check-update.sh --readiness`. When it is not ready, execute `NEXT`
only within authority, then continue project instructions and available
CodeGraph setup. `init-project` refreshes global Teamwork first and never
creates project-local skills or agents. Only the user-level Codex installer
repairs routing; restart Codex after it changes. Cursor User Rules still require
`./install.sh cursor-policy-copy` and a manual paste.

For a user-requested checkout refresh, inspect the report, pull only with
repository-update authority, then run `./install.sh all --profile <profile>`
unless notifications were explicitly declined. Do not initialize project
context here. For `review-required`, inspect `/hooks` and trust only Teamwork
`Stop` and `PermissionRequest`; never trust-all.

## Marketplace Plugin Mode

From a loaded `teamwork-skill` plugin, resolve the cache root with its bundled
`skills/using-teamwork/scripts/plugin-runtime-root.py`; do not use the current
directory. Run `<plugin-root>/scripts/check-update.sh --plugin --readiness`.
It verifies `codex plugin list --json`, the installed cache manifest, the
activation marker at `~/.codex/teamwork/plugin-activation.json` (or
`CODEX_HOME`), Codex agents, routing, policy, notification setting, and that no
legacy user skill copies remain.

`PLUGIN_ACTIVATION=missing` requires one explicit approval before
`<plugin-root>/install.sh plugin-codex-bootstrap`. Bootstrap installs only
Codex agents, routing, managed policy, and notification resources; it removes
only verified Teamwork legacy skill copies and never writes
`~/.agents/skills`. `plugin-init-project` adds project context through the same
Codex-only bootstrap.

When `PLUGIN_CACHE` or `PLUGIN_CATALOG` is stale, run `codex plugin marketplace
remove teamwork`, add `JinPLu/Teamwork` again without a pinned tag, reinstall
`teamwork-skill@teamwork`, open a new Codex task, and invoke `$teamwork-update`.
The unpinned Marketplace can advance through future upgrades. After bootstrap,
restart Codex. If notifications are enabled, `/hooks` still requires individual
trust for the exact two Teamwork hooks.

## Release Boundary

Package versioning, changelogs, tags, and GitHub Releases are maintainer work
under the repository `AGENTS.md`, not installed user-refresh work. Do not add
external MCP, memory services, project dependencies, or non-Teamwork plugins
without separate authority. Interaction tools belong to the current host/runtime;
this refresh path neither enables nor proves them.
