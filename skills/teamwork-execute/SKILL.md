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

Re-read the accepted Task Contract and inspect owner/flow, tests/config, and
invariants. Change the current producer path; avoid masking wrappers, fallbacks,
or guessed state. Preserve unrelated changes and delegate only disjoint ownership.

Maintain `AC -> change/no-change -> evidence -> result/strength`. Before acting,
classify discoveries:

- `regression` or `contract_violation`: fix in scope or return `revise`/`blocked`;
- `pre_existing`: record without attributing or silently repairing it;
- `scope_delta`: pause and obtain an accepted Contract/version change; or
- `suggestion`: record without editing.

Failed AC evidence stays failed until direct evidence changes that AC.

Verify against the acceptance signal, adding broader checks when planned or
shared/public behavior changed. Report commands, artifacts, diffs, or observed
behavior accurately: build-only and blocked checks are not behavioral proof.
For an unclear reproducible failure, use one bounded confirming pass; route to
debug if root cause remains uncertain. Remove temporary instrumentation and
touched-diff slop.

## Done When

Return changed paths, Contract source, AC trace, proof, discovery classes,
delegation state, deviations, residual risk, and blockers. No track remains open.

## Escalate

Stop when new evidence invalidates scope, required state is absent, or a change
would affect protected/public behavior; route back to research, debug, or plan.

## Conditional Protocols

Use `subagent-dispatch.md` and `subagent-contract.md` for Workers,
`verification-patterns.md` for proof, `debug-mode.md` for runtime failures, and
`artifact-protocol.md` for durable memory. Fresh-context review is required only when the
accepted plan or `review-checks.md` risk gates require it. Paths are under
`skills/using-teamwork/references/`.
