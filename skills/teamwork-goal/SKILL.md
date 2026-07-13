---
name: teamwork-goal
description: Use when the user asks to keep going, fix until green, converge on a verifiable target, or work within an explicit budget.
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

Before retrying, identify the preserved Contract/Invariants, failed claim and
stage, prior evidence, do-not-repeat constraints, and strategy delta. Keep the
Contract version; only an accepted scope delta re-enters Plan.

Route only the affected stage: broad gaps to research, unknown-cause failures to
debug, known fixes to execute, and changed/final acceptance to review. Do not
replay the full workflow. Record each result and strategy change; accept only on
focused proof and required review.

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
formats; use each narrower stage protocol when that stage runs. Paths are under
`skills/using-teamwork/references/`.
