---
name: teamwork-plan
description: Use when the user asks for plan/design or a non-trivial research, engineering, or implementation change needs scope, requirements, protected boundaries, verification, dispatch, memory, or acceptance before action.
---

# Teamwork Plan

## Outcome

Turn an evidence-backed direction into an accepted, executable scope with
falsifiable verification and explicit stopping boundaries.

## Enter When

Use when the user requests planning or non-trivial action lacks an
accepted plan. Route unresolved external behavior or architecture to research,
and reproducible unknown-cause failures to debug. Tiny fixed-scope work may go
straight to execution.

## Do And Boundaries

Restate the goal or root cause and resolve only decision-critical gaps. Map
requirements to observed evidence or planned verification. Define in-scope,
out-of-scope, and protected surfaces; for code, identify the current owner,
control flow, relevant tests/config, and invariants before choosing the smallest
producer-side change. Required paths, commands, environments, models, ports,
credentials, or contracts must come from the user or project evidence.

Write ordered actions with enough ownership, dependencies, verification, and
stop conditions to execute without reopening design. Use a
table or diagram only when it materially clarifies comparison or flow. Delegate
only independent tracks with disjoint ownership and clear integration. Use a
chat plan for bounded work and a durable plan for cross-turn, high-risk,
delegated, public-contract, or goal work.

## Done When

The plan states goal, evidence, scope, steps, verification, dispatch, risks,
stop conditions, and the next executable action. Do not claim acceptance until
the user or governing workflow accepts it.

## Escalate

Ask when a remaining user decision changes behavior, architecture, risk, or
acceptance. Return to research/debug when evidence cannot safely support a plan.

## Conditional Protocols

Use `plan-output.md` for durable plans, `verification-patterns.md` for proof,
`subagent-dispatch.md` and `subagent-contract.md` for delegation,
`goal-iteration.md` for retry invariants, and `grill-mode.md` only for explicit
grill/question-first mode. Paths are under `skills/using-teamwork/references/`.
