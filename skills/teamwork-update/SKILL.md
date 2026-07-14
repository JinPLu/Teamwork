---
name: teamwork-update
description: Use when checking or refreshing installed Teamwork skills, agents, global policy, notifications, routing, or project surfaces from an existing Teamwork checkout.
---

# Teamwork Update

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.
Refresh user installations only. Read
`skills/using-teamwork/references/check-update.md` for the freshness contract.

## Workflow

1. From the Teamwork checkout, run `./scripts/check-update.sh`; add `--project
   "<project-root>"` when project surfaces are in scope.
2. If the checkout is behind upstream, pull only with repository-update
   authority. Preserve the current install profile from source/config or the
   report; never guess it.
3. Run `./scripts/check-update.sh --readiness` with the same optional project
   argument. Execute `NEXT`, or its exact commands with an explicitly requested
   `--no-notifications`, to refresh all global skills, agents, managed policy,
   routing, and applicable project surfaces.
4. Run `./install.sh cursor-policy-copy` when possible and report that the
   Cursor User Rules paste cannot be verified automatically. For
   `CODEX_NOTIFICATIONS=review-required`, inspect `/hooks` and trust only the
   exact Teamwork `Stop` and `PermissionRequest` hooks; never use trust-all.
5. Rerun the same readiness check until it reports `INSTALL_READY=yes`, or
   report each remaining gap and its next action. Restart Codex only when the
   routing check says it is required.

## Boundaries

- Never edit `VERSION`, plugin manifests, changelogs, release commits, tags, or
  GitHub Releases. Maintainer publication is repository work governed outside
  this installed skill.
- Do not install project package dependencies, non-Teamwork plugins, external
  MCP/memory services, or paid tooling unless the user asks separately.
- Native interaction tools remain host-owned. Static content freshness does not
  prove live host behavior.
- Preserve unrelated files and report source version, installed versions,
  profile, global/project status, manual actions, restart need, and unresolved
  drift.

## Done When

The repeated readiness check truthfully reports `INSTALL_READY=yes`, or every
remaining drift item, manual action, and exact next step is visible without
claiming that static freshness proves live host behavior.
