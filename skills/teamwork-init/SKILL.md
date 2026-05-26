---
name: teamwork-init
description: Use when initializing, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CLAUDE rules, or migrating reusable workflow rules into Teamwork.
---

# Teamwork Init

Use for project-level agent workflow setup, instruction slimming, and migration
of portable process rules into Teamwork. This stage prepares a project to use
Teamwork without bloating project instructions.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence,
  assumptions, native Codex boundaries, and artifact rules.
- `skills/using-teamwork/references/project-init.md` for project rule layering,
  MCP policy, and context-cache discipline.
- `skills/using-teamwork/references/artifact-protocol.md` when durable research,
  plan, or report memory may be warranted.

## Workflow

1. Inspect root and repo-local instruction files such as `AGENTS.md`,
   `CODEX.md`, `CLAUDE.md`, `GEMINI.md`, README guidance, and existing
   `docs/teamwork/` artifacts.
2. Classify content as portable workflow, project fact, current state,
   appendix navigation, or durable artifact memory.
3. Keep portable workflow in Teamwork skills or references. Keep project facts,
   evidence sources, remote/local boundaries, and protected actions in project
   instructions.
4. Move long path maps, command inventories, and historical navigation to
   appendix docs that are explicitly read on demand.
5. Preserve volatile experiment numbers, current task progress, temporary
   conclusions, and chat summaries outside `AGENTS.md`; use reviewed project
   evidence docs or Teamwork artifacts only when their triggers apply.
6. Return a slim rules plan with changed files, migration rationale,
   verification, and any human decisions.

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
