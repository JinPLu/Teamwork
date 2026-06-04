---
name: teamwork-init
description: Use when initializing, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, or migrating reusable workflow rules into Teamwork.
---

# Teamwork Init

Use for project-level agent workflow setup, instruction slimming, and migration
of portable process rules into Teamwork. Leave projects with only local facts,
evidence sources, boundaries, and acceptance checks needed to apply Teamwork.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence,
  assumptions, platform native boundaries, and artifact rules.
- `skills/using-teamwork/references/project-init.md` for project rule layering,
  MCP policy, and context-cache discipline.
- `skills/using-teamwork/references/artifact-protocol.md` when durable research,
  plan, report, or current-state memory may be warranted.

## Initialization Mode

Installed Codex profile is the global default. During project init, ask only
when the project should override that default. Pro/20x or max performance
intent selects `performance-first`; quota, latency, or cost constraints select
`cost-first`.

- `performance-first`: Codex subagents prefer `gpt-5.5` with high
  reasoning for Explorer, Designer, Worker, Judge, and Reviewer. This is the
  default for Pro/20x Codex workflows.
- `cost-first`: preserve dispatch economics and use lower model classes for
  routine Explorer, Designer, or Worker tracks; still use frontier/high
  reasoning for Judge, Reviewer, high-risk, public, or failed-goal work.

Record `Init Mode: global-default | performance-first | cost-first`; add a
project-local Codex rule only when overriding the installed default. If the
override should change custom-agent models, refresh agents with
`./install.sh --profile <mode> codex-agents` or `project`.

## Workflow

1. Inspect real project context first: root and repo-local `AGENTS.md`,
   `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, `GEMINI.md`, README guidance,
   `docs/teamwork/` artifacts, and user-provided plans or source documents.
2. Classify content as portable workflow, project fact, current state,
   appendix navigation, or durable artifact memory.
3. Apply the Collaboration Backbone Audit from `project-init.md`; mark each
   reusable workflow habit `keep`, `migrate`, or `add`.
4. For Codex, prefer the installed global `~/.codex/AGENTS.md` Teamwork block
   for portable standing authorization and dispatch economics. Add project
   Codex rules only for local exceptions or opt-outs; keep them short, do not
   force dispatch for lightweight, tightly coupled, destructive, or
   credential-sensitive work, and report
   `Codex authorization: global | project-add | user-opt-out` plus the selected
   `Init Mode`.
5. Keep project facts, evidence sources, remote/local boundaries, protected
   actions, and domain-specific acceptance checks in project instructions.
6. Move long path maps, command inventories, and historical navigation to
   appendix docs that are explicitly read on demand.
7. Keep volatile experiment numbers, current task progress, temporary
   conclusions, and chat summaries outside `AGENTS.md`; use artifacts only
   when triggers apply.
8. Return a slim rules plan with changed files, collaboration audit decisions,
   migration rationale, verification, and any human decisions.
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
