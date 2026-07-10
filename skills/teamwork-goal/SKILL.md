---
name: teamwork-goal
description: Use when the user asks to keep going, run until it passes, fix until green, iterate until done, converge on a verifiable target, or work within an explicit budget.
---

# Teamwork Goal

## Outcome

Iterate until a verifiable target passes, the authorized budget ends, or a hard
stop is reached.

## Enter When

Use for explicit persistence such as “keep going,” “until green,” or a stated
budget. Ordinary one-shot work stays in its narrower stage. If objective,
verification, scope, Goal Invariants, or stop rules are unclear, propose them
and obtain approval before creating goal state.

## Do And Boundaries

Use Codex native goal state when available; otherwise keep a rolling report in
`docs/teamwork/reports/`. Record the target, protected boundaries, Goal
Invariants, verification, and the budget supplied by the user/runtime or
accepted plan. Do not invent a fixed iteration budget.

Before retrying, run Replay Preflight: identify prior attempts, current evidence,
do-not-repeat constraints, and the strategy delta.
Route broad unknowns to research, reproducible unknown-cause failures to debug,
scope decisions to plan, changes to execute, and acceptance to review. After
each verify/review cycle, append the attempt result; failures and no-progress
cycles also record why and what must change. Accept only when focused
verification and the required review pass.

## Done When

Mark complete only after the success signal passes. Otherwise return the
current attempt evidence, remaining budget if defined, next strategy, or the
specific stop reason.

## Escalate

Stop on repeated no-progress without an evidence-backed strategy delta,
destructive risk, auth/resource failure, protected-boundary conflict, or
unresolved user intent. Ask before expanding authority or scope.

## Conditional Protocols

Use `goal-iteration.md` for proposal, replay, attempt, and rolling-report
formats; use each narrower stage protocol when that stage runs. Use
`grill-mode.md` only for explicit grill/question-first mode. Paths are under
`skills/using-teamwork/references/`.
