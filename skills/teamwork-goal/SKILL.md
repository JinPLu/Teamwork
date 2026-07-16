---
name: teamwork-goal
description: Use when the user asks Codex to keep working until a verifiable result, fix until green, converge without stopping, or operate within an explicit budget.
---

# Teamwork Goal

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

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
accepts a Goal Proposal. Otherwise keep state in the thread; create a rolling
report only when cross-turn continuity actually needs it. Retain the target,
protected boundaries, Goal Invariants, and any supplied budget. Do not invent a
fixed iteration budget.

Before retrying, identify the preserved scope/invariants, failed claim and
stage, prior evidence, do-not-repeat constraints, and strategy change. Re-enter
Plan only when accepted scope or criteria must change.

Route only the current blocker: broad gaps to research, unknown-cause failures
to debug, and known fixes to execute. Review only when the user asks or a named
high-risk governing gate requires it. Do not replay the workflow or repeat an
unchanged strategy.

## Done When

Mark complete when the real success signal passes and no named protected boundary
remains. Otherwise preserve the current failure and try only an evidence-backed
different strategy, or stop for the specific blocker.

## Escalate

Stop on repeated no-progress without an evidence-backed strategy delta,
destructive risk, auth/resource failure, protected-boundary conflict, or
unresolved required input. A failure alone does not justify a question; apply
the Ask Gate before asking.

## Conditional Protocols

Use `goal-iteration.md` for proposal, replay, attempt, and rolling-report
formats; use each narrower stage protocol when that stage runs. Paths are under
`skills/using-teamwork/references/`.
