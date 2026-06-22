---
name: teamwork-init
description: Use when setting up, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, install readiness, or reusable workflow-rule migration.
---

# Teamwork Init

Use for project workflow setup, instruction slimming, and migration into
Teamwork. Leave only local facts, evidence sources, boundaries, and acceptance
checks needed to apply Teamwork.

Read as needed: `skills/using-teamwork/references/check-update.md` for
readiness, `skills/using-teamwork/references/workflow-contract.md` for
evidence, `skills/using-teamwork/references/project-init.md` for layering/MCP,
and artifact/optional references only when their trigger applies.

## Init Mode

The installed profile is the default on Codex, Cursor, and Claude Code; ask only
for project overrides. Pro/20x throughput selects `performance-first`; quota,
latency, or cost constraints select `cost-first`. Record `Init Mode:
global-default | performance-first | cost-first`; add a project-local rule only
for overrides. Refresh installed agents with `./install.sh --profile` when
model overrides change.

## Full Project Init Default

For setup/init requests, behave like a project `/init`: install the
Teamwork-managed full setup first and report gaps after. Use
`./install.sh --project-root "<project-root>" init-project` from the Teamwork
checkout, or perform the same steps directly when unavailable. The command
installs missing Teamwork-managed global/project skills, agents, and policies;
creates/updates the managed `AGENTS.md` block, `docs/teamwork/`, local ignore
entries, and CodeGraph when the CLI exists. Context7/docs MCP is a read-only
external docs substrate, not a project index; detect and record availability.

Ask only before external MCP/skill installation, credentials, protected server
state, destructive actions, or unresolved required values. Missing Teamwork
surfaces are installed directly. Cursor manual paste, unavailable CodeGraph CLI,
or missing Context7 are reported gaps, not stop conditions.

## Install Readiness Check

Before instruction work, run from the Teamwork checkout:

```bash
./scripts/check-update.sh --readiness --project "<project-root>"
```

When `INSTALL_READY=no`, run the printed `NEXT` equivalent directly as part of
init, copy Cursor policy to the clipboard when possible, and report any
remaining manual Cursor paste or optional substrate gaps.

## Workflow

1. Run the Install Readiness Check; report `Install readiness:` without hard
   gating local files.
2. Run `./install.sh --project-root "<project-root>" init-project`, or create
   the same local surfaces directly when needed.
3. Inspect real project context: local instruction files, README guidance,
   `docs/teamwork/` artifacts, and user-provided plans.
4. Classify content as workflow, project fact, current state, appendix, or
   durable artifact memory.
5. Run the Collaboration Backbone Audit from `project-init.md`; mark each
   reusable workflow habit `keep`, `migrate`, or `add`.
6. Keep facts, required values, boundaries, protected actions, and acceptance
   checks in project instructions.
7. Move long path maps, command inventories, and historical navigation to
   appendix docs read on demand.
8. Keep volatile experiment numbers, task progress, and chat summaries out of
   `AGENTS.md`; use artifacts only when triggers apply.
9. For bootstrap policy, install managed Codex/Claude policy and Cursor agents;
   copy Cursor User Rules when possible. Project files hold only local facts,
   required values, or opt-outs. Report `Bootstrap policy:` and `Init Mode:`.
10. When Teamwork memory exists, keep a short pointer to
   `docs/teamwork/README.md`; do not inline the runtime narrative.
11. For full-setup requests, return the Capability Matrix from `project-init.md`.

## Boundaries

- Do not copy full external workflow, MCP, or project docs into project
  instructions.
- Do not replace project evidence sources with Teamwork artifacts.
- Do not alter protected planning, secrets, server state, or current experiment
  truth without evidence-backed user intent.
- Do not install external tooling without approval. Initializing repo-local
  CodeGraph is allowed when the CLI already exists; otherwise report the gap.

Return changed files, audit decisions, migration rationale, verification, and
human decisions. Include `Memory Delta:` only when durable memory was checked or
changed.
