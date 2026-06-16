---
name: teamwork-init
description: Use when initializing, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, or migrating reusable workflow rules into Teamwork.
---

# Teamwork Init

Use for project workflow setup, instruction slimming, and migration into
Teamwork. Leave only local facts, evidence sources, boundaries, and acceptance
checks needed to apply Teamwork.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and boundaries; `skills/using-teamwork/references/project-init.md` for
rule layering, MCP policy, and context-cache discipline;
`skills/using-teamwork/references/artifact-protocol.md` when durable memory may
be warranted; `skills/using-teamwork/references/optional-skills.md` before
external memory, docs graph, or skill installation.

## Init Mode

The installed Codex profile is the default; ask only for project overrides.
Pro/20x throughput selects `performance-first`; quota, latency, or cost
constraints select `cost-first`.

- `performance-first`: role-optimized `gpt-5.5` — medium Explorer/Designer/
  Worker, high Judge/Reviewer, xhigh Deep Judge/Reviewer for failed-goal,
  security, destructive-risk, public-contract, or release work.
- `cost-first`: downshift routine Explorer/Designer/Worker only; keep
  Judge/Reviewer high and Deep xhigh triggers intact.

Record `Init Mode: global-default | performance-first | cost-first`; add a
project-local rule only for overrides.

## Workflow

1. Inspect real project context: root and repo-local `AGENTS.md`, `CODEX.md`,
   `CURSOR.md`, `CLAUDE.md`, README guidance, `docs/teamwork/` artifacts, and
   user-provided plans.
2. Classify content as workflow, project fact, current state, appendix, or
   durable artifact memory.
3. Run the Collaboration Backbone Audit from `project-init.md`; mark each
   reusable workflow habit `keep`, `migrate`, or `add`.
4. Keep facts, required values, boundaries, protected actions, and acceptance
   checks in project instructions. Missing required values are blockers.
5. Move long path maps, command inventories, and historical navigation to
   appendix docs read on demand.
6. Keep volatile experiment numbers, task progress, and chat summaries out of
   `AGENTS.md`; use artifacts only when triggers apply.
7. For Codex bootstrap, prefer global `~/.codex/AGENTS.md` or `./install.sh
   codex-policy`; project Codex rules hold only local facts, required values, or
   opt-outs. Report `Codex bootstrap policy:` and `Init Mode:`.
8. When Teamwork memory exists, keep a short pointer to
   `docs/teamwork/README.md`; do not inline the runtime narrative.

## Boundaries

- Do not copy full external workflow, MCP, or project docs into project
  instructions.
- Do not replace project evidence sources with Teamwork artifacts.
- Do not alter protected planning, secrets, server state, or current experiment
  truth unless the user asks and evidence supports it.
- Do not install or initialize external tooling without approval when it changes
  system or repository state.

Return changed files, audit decisions, migration rationale, verification, and
human decisions. Include `Memory Delta:` only when durable memory was checked or
changed.
