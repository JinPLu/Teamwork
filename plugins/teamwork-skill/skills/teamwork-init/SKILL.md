---
name: teamwork-init
description: Use when a project needs agent instructions or Teamwork context set up, audited, or slimmed, including memory, MCP/CodeGraph policy, or cross-platform instruction ownership.
---

# Teamwork Init

Audit, bootstrap, or organize project instructions using evidenced facts,
canonical ownership, boundaries, and acceptance checks. It creates no authority.

Read `skills/using-teamwork/references/check-update.md` for readiness,
`workflow-contract.md` for authorization/evidence, and `project-init.md` for
init, ownership, migration, capability, and output rules.

## Choose The Surface

Explicit `teamwork-init` defaults to **Semantic init** unless the user asks only
for audit or deterministic bootstrap.

- **Audit-only:** inspect and classify; make no project or install changes.
- **Deterministic bootstrap:** with authority, run `./install.sh --project-root
  "<project-root>" init-project`; it refreshes global Teamwork and writes project
  instructions, memory, and CodeGraph context, never project-local skills/agents.
- **Semantic init:** inspect evidence, form only a proportional internal Project
  Model, and apply authorized `project-init.md` edits.

From the `teamwork-skill` Codex Marketplace plugin, do not assume a checkout.
Resolve the cache root using the loaded skill's
`scripts/plugin-runtime-root.py`; with authority, run
`<plugin-root>/scripts/check-update.sh --plugin --readiness`, then
`<plugin-root>/install.sh --project-root "<project-root>" plugin-init-project`.
This configures only Codex agents, routing, policy, and selected notifications,
never `~/.agents/skills`, Cursor, or Claude Code. If activation is missing,
explain those changes and get the explicit first-enablement approval required by
`teamwork-update`.

Report bootstrap and semantic results separately. Audit never implies write authority.

## Readiness And Profile

Use the installed profile unless evidence shows a material override. Read it from
`.teamwork-profile`, readiness, and host configuration; do not invent a timeless
profile-to-model mapping. Checkout refreshes use `./install.sh --profile
<profile> all` only with authority; the Marketplace uses its activation marker
and cache-root `plugin-init-project` route.

Before bootstrap or global install, run `./scripts/check-update.sh --readiness`
(or cache-root `--plugin` readiness). Ordinary semantic edits need no global
freshness pass unless install state affects the requested result.

When `INSTALL_READY=no`, run `NEXT` only within authority; remaining gaps are
reported gaps, not stop conditions. Native interaction tools are host capabilities, not Teamwork installation requirements. Do not change host config. Do not install external tooling without approval.

For full bootstrap, refresh global Teamwork first. Project instructions, memory,
and CodeGraph context can continue when the global install returns an actionable
configuration failure. Never install or check project-local Teamwork copies. Cursor manual paste, unavailable CodeGraph CLI,
Context7, or `codex-routing` are capability gaps. For notifications, inspect
`/hooks` and trust only Teamwork `Stop` and `PermissionRequest`, never trust-all.
Ask before credentials, protected server state, destructive effects, or similar
protected actions.

## Semantic Workflow

1. Follow `project-init.md`: inspect instructions, canonical/human docs,
   source/config/tests, commands, trackers/runbooks, and platform surfaces.
2. When useful, form the smallest evidenced init-local project model as an
   internal audit aid; never persist it or invent it. Give each rule/fact one
   owner and link or delta elsewhere.
3. Use `keep`, `merge`, `migrate`, `remove`, `create`, or `unresolved` as
   optional internal classifications; use the root Ask Gate only for conflict.
4. Apply cross-platform ownership and stable/volatile boundaries. Reuse existing
   trackers; create conditional `project.md` only when its triggers and write
   authority hold. This grants no Git or publication authority.
5. Migrate through temporary copy, validation, then atomic replacement. Preserve
   custom/legacy content when no safe migrator exists.
6. Exercise the nearest real changed surface or report its exact activation limit;
   do not add proxy validation. Confirm a rule's owner and user effect, then stop
   unless a named boundary needs another check.
An equivalent audit with no new evidence, classification, or mainline change
writes nothing and reports `no-change`.

Do not duplicate external workflow/MCP/project docs, replace canonical evidence,
or alter protected systems without authority. Keep volatile progress in its
canonical tracker/current artifact. Initialize repo-local CodeGraph only with
bootstrap authority and an existing CLI; otherwise report the gap.

Return the selected surface; separate bootstrap/semantic results, changed or
proposed files, material decisions, verification strength, conflicts, and human
decisions. Do not require a visible Project Model, classification, or Memory
Delta in ordinary output. Include the `project-init.md` Capability Matrix only
for requested full bootstrap.
