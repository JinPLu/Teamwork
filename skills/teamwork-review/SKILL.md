---
name: teamwork-review
description: Use when the user asks whether work is correct or complete, wants a plan, artifact, diff, implementation, or claim checked, or needs findings and acceptance evidence.
---

# Teamwork Review

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Issue an independent, evidence-based `accept`, `revise`, or `blocked` verdict
for a plan, execution, or output. Review does not fix findings.

## Enter When

Use for requested review, acceptance, or risk-gated completion. Give a fresh
Judge/Reviewer the scope, criteria, candidate, and direct evidence. Fresh context
is required for high-risk, public-contract, delegated, security, destructive, release, or
goal acceptance; lightweight checks may self-review otherwise.

## Do And Boundaries

Select plan/execution/output mode. Read primary sources; summaries and test
reports are inputs, not verdicts. Map ACs to evidence and inspect scope,
owner/flow, tests/config, invariants, masking fallbacks, proof, and diff hygiene.
Unaccepted work becomes an out-of-scope finding or follow-up, never an implicit gate.

Give findings stable IDs and one class: `BLOCKER`, `FOLLOW-UP`, or `SUGGESTION`.
A blocker is a failed AC, boundary breach, regression, or missing gating
evidence. Out-of-scope work remains non-blocking unless a current AC cannot pass
without it; that failed AC remains a blocker. State evidence, affected AC, and
route. Never upgrade weak or blocked proof.

Permit one corrective recheck in the same Judge/Reviewer thread. Inspect prior
IDs, claimed fixes, new direct evidence, and regression risk proportional to the
fix. Do not delegate, monitor, or recursively recheck. If the candidate has
materially expanded beyond the reviewed surface, require a fresh review instead.
Remaining blockers stay open.

## Done When

Each criterion has evidence, actionable findings name their criterion and route,
and the verdict matches the proof. `ACCEPT` requires no open `BLOCKER`.

## Escalate

Before returning `blocked` for missing evidence or access, apply the Ask Gate in
`workflow-contract.md` when the user can provide it. Return `revise` for
correctable scope, quality, or proof failures.

## Conditional Protocols

Under `skills/using-teamwork/references/`, load the relevant review/proof lens;
load debug, goal, or `eval-gate.md` only when that gate applies.
