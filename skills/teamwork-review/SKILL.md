---
name: teamwork-review
description: Use when the user asks to review/check a plan, artifact, diff, implementation, research output, completion claim, strict quality, deslop pass, PR walkthrough, or acceptance evidence.
---

# Teamwork Review

## Outcome

Issue an independent, evidence-based `accept`, `revise`, or `blocked` verdict
for a plan, execution, or output. Review does not fix findings unless asked.

## Enter When

Use for requested review, acceptance, diff/output scrutiny, strict quality, or
risk-gated completion. An initial Judge/Reviewer is fresh and acceptance-bound:
give it the Contract, candidate, and direct evidence. Fresh context is required
for high-risk, public-contract, delegated, security, destructive, release, or
goal acceptance; lightweight checks may self-review when none is required.

## Do And Boundaries

Select plan/execution/output mode. Read primary sources; summaries and test
reports are inputs, not verdicts. Map ACs to evidence and inspect scope,
owner/flow, tests/config, invariants, masking fallbacks, proof, and diff hygiene.
Unaccepted work becomes a scope delta or follow-up, never an implicit gate.

Give findings stable IDs and one class: `BLOCKER`, `FOLLOW-UP`, `SUGGESTION`, or
`SCOPE_DELTA`. A blocker is a failed AC, boundary breach, regression, or missing
gating evidence. Other classes are non-blocking; if a scope delta is required to
satisfy a current AC, that AC remains a blocker. State evidence, affected AC,
and route. Never upgrade weak or blocked proof.

Permit one corrective recheck in the same Judge/Reviewer thread. Inspect only
prior IDs, claimed fixes, fix regressions, or new direct evidence—no full rescan,
delegation, monitoring, or recursive recheck. Remaining blockers stay open.

## Done When

Return mode, fresh/recheck status, AC/evidence map, proof strength, findings,
uncertainty, verdict, and rationale. No open `BLOCKER` requires `ACCEPT`; name
each AC's actual evidence state.

## Escalate

Stop and return `blocked` when required evidence or access is missing; return
`revise` for correctable scope, quality, or proof failures.

## Conditional Protocols

Use `review-checks.md`, `verification-patterns.md`, and `review-lenses.md` for
the selected review. Load `debug-mode.md` or `goal-iteration.md` only for those
flows. Teamwork package, SkillOpt/HarnessOpt, ledger, and release rules are owned
by `eval-gate.md`; load them only when that gate applies. Paths are under
`skills/using-teamwork/references/`.
