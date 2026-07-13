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
verification, scope, Goal Invariants, or stop rules are unclear, inspect
discoverable evidence first. Propose and obtain approval only for remaining
user-owned values before creating goal state.

## Do And Boundaries

Use Codex native goal state only when the user explicitly requests Goal mode or
accepts a Goal Proposal; otherwise keep a rolling report in
`docs/teamwork/reports/`. Record the target, protected boundaries, Goal
Invariants, verification, and the budget supplied by the user/runtime or
accepted plan. Do not invent a fixed iteration budget.

Before retrying, identify the preserved scope/invariants, failed claim and
stage, prior evidence, do-not-repeat constraints, and strategy change. Re-enter
Plan only when accepted scope or criteria must change.

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
unresolved required input. A failure alone does not justify a question; apply
the Ask Gate before asking.

## Conditional Protocols

Use `goal-iteration.md` for proposal, replay, attempt, and rolling-report
formats; use each narrower stage protocol when that stage runs. Paths are under
`skills/using-teamwork/references/`.
