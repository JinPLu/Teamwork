---
name: teamwork-plan
description: Use when plan/design is requested, whenever Codex is in Plan mode, or a non-trivial change needs evidence-backed scope, verification, or acceptance before action.
---

# Teamwork Plan

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Turn evidence into an executable scope with falsifiable verification and stop
boundaries.

## Enter When

Use when planning is requested or non-trivial action lacks an accepted plan.
Route unresolved external behavior or architecture to research, and unknown
reproducible failures to debug. Tiny fixed-scope work may go to execution.

## Do And Boundaries

Resolve decision-critical gaps and map requirements to evidence or proof. Define
scope and protected surfaces; for code, identify owner/flow, tests/config, and
invariants, then select the lowest-maintenance solution surface defined in
`workflow-contract.md` before choosing the smallest direct change.

A plan is simple only when scope/risk are fixed and no material user decision
remains. Every non-simple Plan enters evidence-first `grill-me`, independent of
file count. Once material choices are resolved, summarize them in the plan; do
not require an extra confirmation turn. A recap or plan confirmation grants no
implementation, release, external-effect, or other authority.

Source critical values from the user, repository, or justified derivation.
Leave unresolved values open and block only dependent work; recommendations are
not facts.

Write owned actions, dependencies, verification, and stop/replan conditions
sufficient to execute without redesign. Delegate only independent tracks. Use a
durable plan for cross-turn, high-risk, delegated, public-contract, or goal work.

## Done When

Every material requirement maps to an owned action and falsifiable proof, with
enough boundaries, sourced values, dependencies, risks, and stops to execute.
Acceptance comes only from the user or governing workflow.

## Escalate

Apply the Ask Gate in `workflow-contract.md` to unresolved Plan inputs and
decisions. Return to research/debug when evidence cannot support a plan.

## Conditional Protocols

In Codex Plan mode, read `skills/using-teamwork/references/plan-output.md` and
apply its native bridge and readiness gate, including the decision gate, before the
authoritative plan. Use `verification-patterns.md` for proof,
`subagent-dispatch.md` and `subagent-contract.md` for delegation, and
`goal-iteration.md` for retry invariants. Paths are under
`skills/using-teamwork/references/`.
