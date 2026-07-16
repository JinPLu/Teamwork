---
name: teamwork-update
description: Use when the user asks to check or refresh globally installed Teamwork skills, agents, policy, routing, or notifications; project initialization belongs to teamwork-init.
---

# Teamwork Update

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.
Refresh global user installations only. Project initialization and project-context
changes belong to `teamwork-init`. Read
`skills/using-teamwork/references/check-update.md` for the freshness contract.

## Workflow

1. From the Teamwork checkout, run `./scripts/check-update.sh`.
2. If the checkout is behind upstream, pull only with repository-update
   authority. Preserve the current install profile from source/config or the
   report; never guess it.
3. Run `./scripts/check-update.sh --readiness`. Execute `NEXT`, or its exact
   commands with an explicitly requested `--no-notifications`, for a global-only
   refresh of skills, agents, managed policy, and routing. Do not initialize or
   rewrite project context; route that request to `teamwork-init`. An explicit
   update request authorizes this managed refresh: do not stop at command advice
   while the command remains safe and in scope.
4. Run `./install.sh cursor-policy-copy` when possible and report that the
   Cursor User Rules paste cannot be verified automatically. For
   `CODEX_NOTIFICATIONS=review-required`, inspect `/hooks` and trust only the
   exact Teamwork `Stop` and `PermissionRequest` hooks; never use trust-all.
5. Rerun the same readiness check. `MANAGED_INSTALL_READY=yes` proves managed
   files are current; it is not full host activation when
   `HOST_ACTIVATION=manual-action-required`. Complete verifiable in-scope actions,
   then report every remaining manual action and restart need. When the host
   exposes a skill catalog, verify each Teamwork skill appears once.

## Boundaries

- Never edit `VERSION`, plugin manifests, changelogs, release commits, tags, or
  GitHub Releases. Maintainer publication is repository work governed outside
  this installed skill.
- Do not install project package dependencies, non-Teamwork plugins, external
  MCP/memory services, or paid tooling unless the user asks separately.
- Native interaction tools remain host-owned. Static content freshness does not
  prove live host behavior.
- Preserve unrelated files and report source version, installed versions,
  profile, global status, manual actions, restart need, and unresolved drift.

## Done When

The repeated readiness check reports `MANAGED_INSTALL_READY=yes` and
`HOST_ACTIVATION=ready`. If the host requires a human action that Codex cannot
verify, finish with that exact action visible and say activation remains
incomplete; never call `INSTALL_READY=yes` alone full capability or claim that
static freshness proves live host behavior.
