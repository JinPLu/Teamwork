---
name: teamwork-init
description: Use when initializing, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, or migrating reusable workflow rules into Teamwork.
---

# Teamwork Init

Use for project-level agent workflow setup, instruction slimming, and migration
of portable process rules into Teamwork. This stage prepares a project to use
Teamwork without bloating project instructions.

The purpose is to create a reliable human-agent collaboration workflow, not to
turn project instructions into a long project encyclopedia. Distill local good
practice into reusable Teamwork rules, then leave each project with only the
facts, evidence sources, boundaries, and acceptance checks needed to apply
those rules safely.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence,
  assumptions, platform native boundaries, and artifact rules.
- `skills/using-teamwork/references/project-init.md` for project rule layering,
  MCP policy, and context-cache discipline.
- `skills/using-teamwork/references/artifact-protocol.md` when durable research,
  plan, or report memory may be warranted.

## Workflow

1. Inspect the real project context first: root and repo-local instruction
   files such as `AGENTS.md`, `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, `GEMINI.md`, README
   guidance, existing `docs/teamwork/` artifacts, and any user-provided local
   plans or source documents.
2. Classify content as portable workflow, project fact, current state,
   appendix navigation, or durable artifact memory.
3. Apply the Collaboration Backbone Audit from `project-init.md`. For each
   reusable workflow habit, mark `keep`, `migrate`, or `add`: read context
   before edits, plan before complex work, confirm scope, implement in small
   steps, run focused verification, report residual gaps, and produce `/new`
   handoff summaries when switching tasks.
4. For Codex project instructions, ensure an explicit standing authorization
   exists when Teamwork dispatch is desired: the user authorizes Codex to use
   sub-agents, delegation, and parallel agent work for non-lightweight Teamwork
   tasks when independent tracks exist, without needing to repeat "use
   subagents" in each prompt. Prefer `CODEX.md` for Codex-only deltas or a
   clearly labeled Codex section in `AGENTS.md`; keep the rule short and do
   not force dispatch for lightweight, tightly coupled, destructive, or
   credential-sensitive work. In the audit, report
   `Codex authorization: keep | add | user-opt-out`.
5. Keep project facts, evidence sources, remote/local boundaries, protected
   actions, and domain-specific acceptance checks in project instructions.
6. Move long path maps, command inventories, and historical navigation to
   appendix docs that are explicitly read on demand.
7. Preserve volatile experiment numbers, current task progress, temporary
   conclusions, and chat summaries outside `AGENTS.md`; use reviewed project
   evidence docs or Teamwork artifacts only when their triggers apply.
8. Return a slim rules plan with changed files, collaboration audit decisions,
   migration rationale, verification, and any human decisions.

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
