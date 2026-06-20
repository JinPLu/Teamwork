---
name: using-teamwork
description: Use when starting any coding-agent task: infer native/research/debug/plan/execute/review/goal/init/update from user intent, evidence state, and acceptance risk.
---

# Using Teamwork

Teamwork sits on native tools: native capabilities execute; Teamwork adds
evidence, dispatch, memory, and acceptance. Default to acting directly on clear
work; escalate only when it improves correctness, continuity, or cost.

Read `references/workflow-contract.md` for shared principles and platform map.
Read `references/routing-policy.md` when the route is ambiguous or the user
describes symptoms instead of naming a stage.

## First: can you proceed?

Default to proceeding. Ask one short question first only when you hit a real
obstacle, lack information you cannot obtain yourself, or face a core decision
you cannot resolve — scope, acceptance, a required value, an irreversible
action, or public behavior. Decide routine matters (tool/MCP choice, naming,
approach) yourself. Do not narrate this as a gate.

## Route

Infer the route from user intent and evidence state. Most small, clear tasks
need no Teamwork stage — just do the work natively.

- **Native** — quick facts, one CodeGraph question, tiny edits, obvious local
  fixes, or low-risk mechanical work.
- **Research** (`skills/teamwork-research/SKILL.md`) — source of truth, API
  behavior, stale facts, options, constraints, or repro surface is unclear.
- **Debug** (`skills/teamwork-debug/SKILL.md`) — a failure, flaky run, CI log,
  crash, UI symptom, or regression may be reproducible and root cause is unclear.
- **Plan** (`skills/teamwork-plan/SKILL.md`) — design/planning is requested, or
  implementation affects scope, contracts, architecture, dispatch, or acceptance.
- **Execute** (`skills/teamwork-execute/SKILL.md`) — an accepted plan/checklist
  should be implemented or resumed.
- **Review** (`skills/teamwork-review/SKILL.md`) — review, diff scrutiny,
  completion validation, strict quality, deslop, or PR walkthrough is requested.
- **Goal** (`skills/teamwork-goal/SKILL.md`) — iterate until green/done, keep
  going, or work to a budgeted verifiable target.
- **Init** (`skills/teamwork-init/SKILL.md`) — project agent instructions,
  AGENTS/CODEX/CURSOR/CLAUDE, install readiness, or rule migration.
- **Update** (`skills/teamwork-update/SKILL.md`) — Teamwork version, release,
  refresh, or installed skills/agents/policy maintenance.

Users do not need to name stages. Treat stage names as optional force switches.

## Orchestrate

When the work is non-lightweight and an independent track can run in parallel
with clear ownership, fan out subagents to go faster — proactively, without
waiting for the user to ask. The main agent stays the orchestrator: it owns
scope, integration, final verification, and acceptance. See
`references/subagent-dispatch.md`.

For required acceptance of non-lightweight work, prefer a fresh-context
Reviewer; if subagents are unavailable, say so and name the residual risk.

## Output

For lightweight native work, just answer. Reserve a short `Route: ...` line for
non-lightweight handoffs, redirects, blockers, or goal/update work. Include
`Memory Delta:` only when durable project memory was checked or changed.
