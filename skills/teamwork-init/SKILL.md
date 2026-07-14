---
name: teamwork-init
description: Use when setting up, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, install readiness, or reusable workflow-rule migration.
---

# Teamwork Init

Audit, bootstrap, or semantically organize project instructions while retaining
evidenced facts, canonical ownership, boundaries, and acceptance checks. This is
not a new Teamwork skill, stage, route, mode, artifact, or state machine.

Read `skills/using-teamwork/references/check-update.md` for readiness,
`workflow-contract.md` for authorization/evidence, and `project-init.md` for the
canonical semantic-init, ownership, migration, capability, and output contract.

## Choose The Surface

Explicit `teamwork-init` defaults to **Semantic init** unless the user asks only
for audit or deterministic bootstrap.

- **Audit-only:** inspect and classify; make no project or install changes.
- **Deterministic bootstrap:** when authorized, run `./install.sh --project-root
  "<project-root>" init-project` or an accepted narrower target. It reproducibly
  refreshes managed surfaces but cannot claim semantic review or optimization.
- **Semantic init:** inspect project evidence first, form the proportional
  init-local Project Model, classify relevant rules, and apply only authorized
  edits under `project-init.md`.

Report bootstrap and semantic results separately. Audit never implies install or
write authority.
## Readiness And Profile

Use the installed cross-platform profile unless evidence leaves a material
override. Read the active profile and any material model configuration from the
installed `.teamwork-profile` markers, readiness output, and host configuration;
do not reconstruct a timeless profile-to-model mapping in Init. Report the
selected profile when it materially affects the result. Refresh via
`./install.sh --profile <profile> all` only with install authority.

Before bootstrap or writes, run:

```bash
./scripts/check-update.sh --readiness --project "<project-root>"
```

When `INSTALL_READY=no`, run `NEXT` only within authority. Treat remaining gaps as
reported gaps, not stop conditions.
Native interaction tools are host capabilities, not Teamwork installation requirements.
Do not mutate host config merely to expose them. Do not install external tooling without approval.

For full bootstrap, install first and report gaps afterward.
Project surfaces continue even when the global install returns an actionable configuration failure.
Cursor manual paste, unavailable CodeGraph CLI, Context7, or
`codex-routing` remain capability gaps. For notification review, inspect
`/hooks` and trust only the exact Teamwork `Stop` and `PermissionRequest` hooks
individually; never `trust-all`. Ask before credentials, protected server state,
destructive effects, or other separately protected actions.

## Semantic Workflow

1. Follow `project-init.md`: inspect instructions/imports and human docs,
   canonical project docs, source/config/tests, commands, trackers/runbooks, and
   Codex/Cursor/Claude surfaces before edits.
2. When useful, form the smallest evidenced init-local project model as an
   internal audit aid; never persist it or invent purpose, owners, required
   values, relationships, or current truth.
   Include platform instruction/loading entrypoints and only evidenced deltas;
   give each rule or fact one primary owner and link or delta elsewhere.
3. Use `keep`, `merge`, `migrate`, `remove`, `create`, or `unresolved` as
   optional internal classifications; use the root Ask Gate only for material
   unresolved conflict.
4. Apply canonical cross-platform ownership and stable/volatile boundaries.
   Reuse the existing tracker/runbook; create conditional `project.md` only when
   every reference trigger and write authority hold. This grants no Git or
   publication authority.
5. Migrate through temporary copy, validation, then atomic replacement. Failure
   leaves original bytes unchanged; without a safe migrator preserve custom or
   legacy content and report the candidate.
6. Verify changed surfaces and limit claims to their evidence tier. Static or
   deterministic checks do not prove live host behavior.
An equivalent repeat audit with no new evidence, classification, or mainline
change must write nothing and report `no-change`.

Do not duplicate external workflow/MCP/project docs, replace canonical evidence,
or alter secrets, protected planning, servers, Git/publication, or external
systems without authority. Keep volatile progress in its canonical tracker or a
triggered Teamwork current/artifact surface. Initialize repo-local CodeGraph only
with bootstrap authority and an existing CLI; otherwise report the gap.

Return the selected surface; separate bootstrap and semantic results;
changed/proposed files; material ownership, mainline, and migration decisions;
verification strength; conflicts and human decisions. Do not require a visible
Project Model, six-way classification, or Memory Delta in ordinary output.
Include the `project-init.md` Capability Matrix only when the user explicitly
requested full bootstrap.
