---
name: teamwork-init
description: Use when a project needs agent instructions or Teamwork context set up, audited, or slimmed, including memory, MCP/CodeGraph policy, or cross-platform instruction ownership.
---

# Teamwork Init

Audit, bootstrap, or organize project instructions while preserving evidenced
facts, canonical ownership, boundaries, and acceptance checks. This creates no
new Teamwork stage or authority.

Read `skills/using-teamwork/references/check-update.md` for readiness,
`workflow-contract.md` for authorization/evidence, and `project-init.md` for
init, ownership, migration, capability, and output rules.

## Choose The Surface

Explicit `teamwork-init` defaults to **Semantic init** unless the user asks only
for audit or deterministic bootstrap.

- **Audit-only:** inspect and classify; make no project or install changes.
- **Deterministic bootstrap:** when authorized, run `./install.sh --project-root
  "<project-root>" init-project`. It refreshes global Teamwork and writes project
  instructions, memory, and CodeGraph context; it never copies Teamwork skills
  or agents into the project. It does not claim semantic review.
- **Semantic init:** inspect evidence, form the proportional init-local Project
  Model, classify relevant rules, and apply only authorized `project-init.md`
  edits.

When this skill is loaded from the `teamwork-skill` Codex Marketplace plugin,
do not assume the current directory is a Teamwork checkout. Resolve the bundled
runtime with `skills/using-teamwork/scripts/plugin-runtime-root.py` relative to
the loaded plugin skill. For an authorized deterministic bootstrap, run
`<plugin-root>/scripts/check-update.sh --plugin --readiness`, then
`<plugin-root>/install.sh --project-root "<project-root>" plugin-init-project`.
That route activates only Codex agents, routing, policy, and the selected
notifications before project context; it never copies skills into
`~/.agents/skills` and does not manage Cursor or Claude Code. If no activation
marker exists, explain the managed changes and obtain the same explicit first
enablement approval required by `teamwork-update` before this command.

Report bootstrap and semantic results separately. Audit never implies install or
write authority.
## Readiness And Profile

Use the installed cross-platform profile unless evidence shows a material
override. Read active profile/model configuration from `.teamwork-profile`,
readiness, and host configuration; do not reconstruct a timeless
profile-to-model mapping. Report it only when material. Refresh via
`./install.sh --profile <profile> all` only with install authority. In the
Marketplace runtime, use the activation marker and the cache-root
`plugin-init-project` command above instead; it is Codex-only.

Before deterministic bootstrap or a global install, run
`./scripts/check-update.sh --readiness` (or the cache-root `--plugin` readiness
check in the Marketplace runtime). Ordinary semantic instruction edits do
not require a global freshness pass unless install state affects the requested result.

When `INSTALL_READY=no`, run `NEXT` only within authority. Treat remaining gaps as
reported gaps, not stop conditions.
Native interaction tools are host capabilities, not Teamwork installation
requirements. Do not change host config. Do not install external tooling without
approval.

For full bootstrap, refresh global Teamwork first. Project instructions, memory,
and CodeGraph context can continue when the global install returns an actionable
configuration failure; do not install or check project-local Teamwork copies.
Cursor manual paste, unavailable CodeGraph CLI, Context7, or `codex-routing` are
capability gaps. For notifications, inspect `/hooks`; trust only exact Teamwork
`Stop` and `PermissionRequest` hooks, never `trust-all`. Ask before credentials,
protected server state, destructive effects, or other protected actions.

## Semantic Workflow

1. Follow `project-init.md`: inspect instructions, human/canonical docs,
   source/config/tests, commands, trackers/runbooks, and platform surfaces.
2. When useful, form the smallest evidenced init-local project model as an
   internal audit aid; never persist it or invent facts or relationships. Include
   platform entrypoints and only evidenced deltas; give each rule or fact one
   primary owner and link or delta elsewhere.
3. Use `keep`, `merge`, `migrate`, `remove`, `create`, or `unresolved` as
   optional internal classifications; use the root Ask Gate only for material conflict.
4. Apply cross-platform ownership and stable/volatile boundaries. Reuse the
   tracker/runbook; create conditional `project.md` only when every trigger and
   write authority hold. This grants no Git or publication authority.
5. Migrate through temporary copy, validation, then atomic replacement. Failure
   leaves original bytes unchanged; without a safe migrator preserve custom or
   legacy content and report the candidate.
6. Exercise the nearest real changed surface when available; otherwise report the
   exact activation limit instead of adding proxy validation.
7. For an internal rule change, confirm its canonical owner and user-visible
   effect, then stop unless a named protected boundary needs another check.
An equivalent audit with no new evidence, classification, or mainline change
writes nothing and reports `no-change`.

Do not duplicate external workflow/MCP/project docs, replace canonical evidence,
or alter protected systems without authority. Keep volatile progress in its
canonical tracker/current artifact. Initialize repo-local CodeGraph only with
bootstrap authority and an existing CLI; otherwise report the gap.

Return the selected surface; separate bootstrap/semantic results, changed or
proposed files, material decisions, verification strength, conflicts, and human
decisions. Do not require a visible Project Model, six-way classification, or
Memory Delta in ordinary output. Include the `project-init.md` Capability Matrix
only when the user requested full bootstrap.
