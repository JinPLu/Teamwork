---
name: using-teamwork
description: Use when a task is ambiguous, non-lightweight, multi-stage, explicitly Teamwork-routed, or asks for grill/grill-me/question-first mode; infer native/research/debug/plan/execute/review/goal/init/update from intent, evidence, and risk.
---

# Using Teamwork

Teamwork sits on native tools: native capabilities execute; Teamwork adds
evidence, dispatch, memory, and acceptance. Default to acting directly on clear
work; escalate only when it improves correctness, continuity, or cost.

Read `references/workflow-contract.md` for shared principles, `references/routing-policy.md`
for ambiguous or uncertainty-driven questioning, and `references/grill-mode.md` for explicit
grill/grill-me/question-first/stress-test requests.

## First: can you proceed?

Proceed when evidence is enough. For uncertain, complex, or non-lightweight
tasks, ask the next decision/risk question before planning or acting when the
answer could change scope, acceptance, public behavior, architecture, risk, or
verification. Decide routine choices yourself.

In explicit grill mode, ask at least one decision/risk question with a
recommended answer unless the user exits or supplied a Shared Understanding
Packet. Do not plan, synthesize research, choose design, edit, start a goal, or
dispatch planning/design/execution agents until packet confirmation or exit.

## Route

Infer the route from user intent and evidence state. Most small, clear tasks
need no Teamwork stage — just do the work natively.

- **Native** — quick facts, one CodeGraph question, small local edits,
  obvious fixes, simple evidence checks, or low-risk mechanical work.
- **Research** (`skills/teamwork-research/SKILL.md`) — source of truth, API
  behavior, stale facts, options, constraints, or repro surface is unclear.
- **Debug** (`skills/teamwork-debug/SKILL.md`) — a failure, flaky run, CI log,
  crash, UI symptom, or regression may be reproducible and root cause is unclear.
- **Plan** (`skills/teamwork-plan/SKILL.md`) — design/planning is requested, or
  the next change affects scope, contracts, architecture, dispatch, or acceptance.
- **Execute** (`skills/teamwork-execute/SKILL.md`) — an accepted plan/checklist
  should be implemented or resumed.
- **Review** (`skills/teamwork-review/SKILL.md`) — review, output/diff scrutiny,
  completion validation, strict quality, deslop, or PR walkthrough is requested.
- **Goal** (`skills/teamwork-goal/SKILL.md`) — iterate until green/done, keep
  going, or work to a budgeted verifiable target.
- **Init** (`skills/teamwork-init/SKILL.md`) — project agent instructions,
  AGENTS/CODEX/CURSOR/CLAUDE, install readiness, or rule migration.
- **Update** (`skills/teamwork-update/SKILL.md`) — Teamwork version, release,
  refresh, or installed skills/agents/policy maintenance.

Users do not need to name stages. Treat stage names as optional force switches.

## Orchestrate

For non-lightweight work, fan out only when an independent track has clear
ownership and enough evidence, time, or context-isolation value to beat its
cost. The main agent owns scope, integration, final verification, and
acceptance. See `references/subagent-dispatch.md`.

For required acceptance of non-lightweight work, prefer a fresh-context
Reviewer; if subagents are unavailable, say so and name the residual risk.

## Output

For lightweight native work, just answer. Reserve a short `Route: ...` line for
non-lightweight handoffs, redirects, blockers, or goal/update work. Include
`Memory Delta:` only when durable project memory was checked or changed.
