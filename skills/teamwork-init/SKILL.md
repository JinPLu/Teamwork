---
name: teamwork-init
description: Use when initializing, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, or migrating reusable workflow rules into Teamwork.
---

# Teamwork Init

Use for project workflow setup, instruction slimming, and migration into
Teamwork. Leave only local facts, evidence sources, boundaries, and acceptance
checks needed to apply Teamwork.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence,
  assumptions, platform native boundaries, and artifact rules.
- `skills/using-teamwork/references/project-init.md` for project rule layering,
  MCP policy, and context-cache discipline.
- `skills/using-teamwork/references/artifact-protocol.md` when durable research,
  plan, report, or current-state memory may be warranted.
- `skills/using-teamwork/references/optional-skills.md` before external
  memory, docs graph, MCP, or skill installation.

## Initialization Mode

Installed Codex profile is the default. Ask only for project overrides.
Pro/20x throughput selects `performance-first`; quota, latency, or cost
constraints select `cost-first`.

- `performance-first`: Codex subagents use role-optimized `gpt-5.5`: medium
  routine Explorer/Designer/Worker, high Judge/Reviewer, and xhigh
  Deep Judge/Reviewer only for failed-goal, security, destructive-risk,
  public-contract, or release acceptance work.
- `cost-first`: preserve dispatch economics and downshift only routine Explorer,
  Designer, or Worker tracks; keep Judge/Reviewer high and preserve Deep
  Judge/Reviewer xhigh triggers for high-risk, public, or failed-goal work.

Record `Init Mode: global-default | performance-first | cost-first`; add a
project-local rule only for overrides. If custom-agent models must change, run
`./install.sh --profile <mode> codex-agents` or `project`.

## Full Feature Init

For full setup/full features/memory integration/docs graph, return the
Capability Matrix from `project-init.md`: rows, status
`enabled | missing | blocked | optional | deferred`, evidence, one next
action for each non-enabled row. Initialize scoped core rows.
External memory/docs graph rows stay `optional` or `deferred` until explicit
approval and gate pass.

## Workflow

1. Inspect real project context first: root and repo-local `AGENTS.md`,
   `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, `GEMINI.md`, README guidance,
   `docs/teamwork/` artifacts, and user-provided plans or source documents.
2. Classify content as workflow, project fact, current state, appendix, or
   durable artifact memory.
3. Apply the Collaboration Backbone Audit from `project-init.md`; mark each
   reusable workflow habit `keep`, `migrate`, or `add`.
4. For Codex bootstrap policy, prefer global `~/.codex/AGENTS.md`; for App-wide
   behavior point to `./install.sh codex-policy` and Codex App Personalization.
   Project Codex rules are only for local facts, required values, exceptions,
   or opt-outs. Report `Codex bootstrap policy:` as `app-personalization`,
   `global-agents`, `project-add`, `missing`, or `user-opt-out`, plus
   `Init Mode`.
5. Keep facts, evidence, required values, boundaries, protected actions, and
   acceptance checks in project instructions. Missing values are blockers.
6. Move long path maps, command inventories, and historical navigation to
   appendix docs that are explicitly read on demand.
7. Keep volatile experiment numbers, current task progress, temporary
   conclusions, and chat summaries outside `AGENTS.md`; use artifacts only
   when triggers apply.
8. Return changed files, audit decisions, migration rationale, verification,
   and human decisions.
9. When Teamwork memory exists, keep a short `AGENTS.md` or README pointer to
   `docs/teamwork/README.md`; do not inline the runtime narrative.
10. Bootstrap `docs/teamwork/index.json`, `docs/teamwork/README.md`, and
   `docs/teamwork/current.md` only when project memory setup is in scope; then
   report `Memory Delta:` per `artifact-protocol.md`.

## Artifact Decision

- Lightweight local cleanup: cite evidence in chat; do not create artifacts.
- Reusable audit, cross-repo migration, external calibration, high-risk
  workflow change, or explicit repository-plan request: create or update
  `docs/teamwork/research/` or `docs/teamwork/plans/`.
- Goal-mode or durable conclusion: maintain `docs/teamwork/reports/` as rolling
  memory. Artifacts help retrieval; they are not completion proof.

## Boundaries

- Do not copy full Superpowers, MCP, or project docs into project instructions.
- Do not replace project evidence sources with Teamwork artifacts.
- Do not alter protected planning, secrets, server state, or current experiment
  truth unless the user explicitly asks and evidence supports the update.
- Do not install or initialize external tooling without user approval when that
  action changes system or repository state.
