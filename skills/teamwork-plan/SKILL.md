---
name: teamwork-plan
description: Use when plan/design is requested, whenever Codex is in Plan mode, or a non-trivial change needs evidence-backed scope, verification, or acceptance before action.
---

# Teamwork Plan

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Turn evidence into executable scope, falsifiable proof, and stop boundaries.

## Enter When

Use for requested planning or non-trivial action lacking an accepted plan. Route
unclear external behavior/architecture to research, reproducible failures to
debug; tiny fixed-scope work may execute.

## Do And Boundaries

Resolve decision-critical gaps and map requirements to proof. Define
scope/protected surfaces; for code identify owner/flow, tests/config, invariants,
and the lowest-maintenance solution before the smallest direct change.

A plan is simple only with fixed scope/risk and no material user decision.
Every non-simple Plan enters evidence-first `grill-me`, independent of file count. Once
choices resolve, summarize them in the plan; no extra confirmation turn. A recap
or plan confirmation grants no implementation, release, external-effect, or other authority.

For every material decision, use a brief, human-readable `Settled: ...` /
`Still open: ...` checkpoint: the resolved choice, remaining choice, or `none`;
it grants neither confirmation nor execution authority.

Source critical values from user, repository, or justified derivation. Leave
unresolved values open, blocking only dependent work; recommendations are not facts.

Write owned actions, dependencies, verification, and stop/replan conditions to
execute without redesign. Delegate only independent tracks; use durable plans for
cross-turn, high-risk, delegated, public-contract, or goal work.

## Done When

Every material requirement maps to an owned action and falsifiable proof, with
enough boundaries, sourced values, dependencies, risks, and stops to execute.
Acceptance comes only from the user or governing workflow.

## Escalate

Apply the Ask Gate in `workflow-contract.md` to unresolved Plan inputs and
decisions. Return to research/debug when evidence cannot support a plan.

## Conditional Protocols

In Codex Plan mode, read `skills/using-teamwork/references/plan-output.md` and
apply its native bridge and readiness gate before the authoritative plan. Use
`verification-patterns.md` for proof, dispatch/contract references for delegation,
and `goal-iteration.md` for retry invariants.
