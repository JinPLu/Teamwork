---
name: teamwork-update
description: Use when the user asks to check or refresh globally installed Teamwork skills, agents, policy, routing, or notifications; project initialization belongs to teamwork-init.
---

# Teamwork Update

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.
Refresh global user installations only. Project initialization and project-context
changes belong to `teamwork-init`; read `check-update.md` for freshness.

## Codex Marketplace Plugin

From `teamwork-skill`, do not assume a checkout. Resolve the cache root with the
loaded skill's `scripts/plugin-runtime-root.py`, then run
`<plugin-root>/scripts/check-update.sh --plugin` first.

If `PLUGIN_ACTIVATION=missing`, explain that full setup installs Codex agents,
routing, managed policy, selected notifications, and removes only verified legacy
Teamwork skill copies. Ask one explicit confirmation before
`<plugin-root>/install.sh [--profile <reported-profile>] [--no-notifications]
plugin-codex-bootstrap`; installation alone is not authorization and never copies
skills to `~/.agents/skills`.

An explicit update for an activated plugin authorizes the same refresh. Bootstrap,
then rerun cache-root `--plugin --readiness`. When `PLUGIN_CACHE` or
`PLUGIN_CATALOG` is stale, remove the `teamwork` Marketplace, add
`JinPLu/Teamwork` again without a pinned tag, reinstall
`teamwork-skill@teamwork`, open a new task, and invoke `$teamwork-update`. The
unpinned Marketplace can advance through future upgrades. Restart Codex after
routing changes. For `CODEX_NOTIFICATIONS=review-required`, inspect `/hooks`
and trust only Teamwork `Stop` and `PermissionRequest`, never trust-all.

## Checkout Workflow

1. Run `./scripts/check-update.sh`; pull only with repository-update authority,
   and preserve the current install profile from source/config or the report.
2. Run `./scripts/check-update.sh --readiness`. Execute `NEXT`, or its exact
   `--no-notifications` commands, for a global-only refresh of skills, agents, managed policy, and routing. Do not rewrite project context; route it to `teamwork-init`. An explicit update authorizes this safe, in-scope refresh: do not stop at command advice while the command remains safe and in scope.
3. Run `./install.sh cursor-policy-copy` when possible; manual Cursor paste is
   unverifiable. For review-required Codex notifications, inspect `/hooks` and
   trust only Teamwork `Stop` and `PermissionRequest`.
4. Rerun readiness. `MANAGED_INSTALL_READY=yes` proves managed files are current;
   it is not full host activation when `HOST_ACTIVATION=manual-action-required`.
   Report every manual action/restart and verify each Teamwork skill appears once.

## Boundaries

- Never edit `VERSION`, plugin manifests, changelogs, release commits, tags, or
  GitHub Releases; maintainer publication is outside this installed skill.
- Do not install project dependencies, non-Teamwork plugins, external MCP/memory,
  or paid tooling without separate user authority.
- Native interaction tools remain host-owned; static freshness proves no live host behavior.
- Preserve unrelated files; report versions, profile, global status, manual actions,
  restart need, and unresolved drift.

## Done When

The repeated readiness check reports `MANAGED_INSTALL_READY=yes` and
`HOST_ACTIVATION=ready`. If a human action remains, show it and say activation is
incomplete; never call `INSTALL_READY=yes` alone full capability or treat static
freshness as live-host proof.
