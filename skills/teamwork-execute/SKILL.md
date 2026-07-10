---
name: teamwork-execute
description: Use when an accepted plan, checklist, approved scope, or known root-cause fix should be implemented, continued, resumed, or verified with focused action.
---

# Teamwork Execute

## Outcome

Implement and verify the accepted scope with the smallest direct change.
Execution does not reopen requirements or expand scope.

## Enter When

Use when an accepted plan, scope, or known root-cause fix has resolved
decision-critical requirements. Required files, commands, environments,
credentials, paths, ports, models, and configs must be explicit or discoverable.

## Do And Boundaries

Re-read the accepted scope and inspect the existing owner, control flow,
tests/config, and invariants before editing. Name touched paths, then change the
current producer-side path rather than adding a parallel mode, wrapper, broad
catch, alias, or fallback that masks missing state. Keep unrelated user changes
intact. Delegate only independent tracks with disjoint ownership; integrate all
returned packets before completion.

Verify against the acceptance signal, adding broader checks when planned or
shared/public behavior changed. Report commands, artifacts, diffs, or observed
behavior accurately: build-only and blocked checks are not behavioral proof.
For an unclear reproducible failure, use one bounded confirming pass; route to
debug if root cause remains uncertain. Remove temporary instrumentation and
touched-diff slop.

## Done When

Return changed paths, plan/scope source, verification and cleanup evidence,
delegation results or continuity rationale, deviations, residual risk, and
blockers. No delegated track may remain open.

## Escalate

Stop when new evidence invalidates scope, required state is absent, or a change
would affect protected/public behavior; route back to research, debug, or plan.

## Conditional Protocols

Use `subagent-dispatch.md` and `subagent-contract.md` for Workers,
`verification-patterns.md` for proof, `debug-mode.md` for runtime failures,
`artifact-protocol.md` for durable memory, and `grill-mode.md` only for explicit
grill/question-first mode. Fresh-context review is required only when the
accepted plan or `review-checks.md` risk gates require it. Paths are under
`skills/using-teamwork/references/`.
