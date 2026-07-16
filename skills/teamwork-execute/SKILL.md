---
name: teamwork-execute
description: Use when the user asks to carry out an accepted plan or checklist, implement an approved change, apply a known fix, continue scoped work, or verify it.
---

# Teamwork Execute

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Implement and verify the accepted scope with the smallest direct change.
Execution does not reopen requirements or expand scope.

## Enter When

Use when an accepted plan, scope, or known root-cause fix has resolved
decision-critical requirements. Required files, commands, environments,
credentials, paths, ports, models, and configs must be explicit or discoverable.

## Do And Boundaries

Re-read scope, criteria, authority, and invariants; inspect owner/flow and
tests/config. Apply the solution surface within scope; change the
current producer path, avoiding masking wrappers, fallbacks, or guessed state.
Preserve unrelated changes; delegate only disjoint work.

Maintain `AC -> change/no-change -> evidence -> result/strength`. Before acting,
classify discoveries:

- `regression` or `accepted_scope_violation`: fix in scope or stop;
- `pre_existing`: record without attributing or repairing;
- `out_of_scope`: pause and route through the Ask Gate; or
- `suggestion`: record without editing.

Failed AC evidence stays failed until direct evidence changes that AC.

Verify against the acceptance signal, adding broader checks for planned or
shared/public changes. Report commands, artifacts, diffs, or observed
behavior accurately: build-only and blocked checks are not behavioral proof.
For an unclear reproducible failure, gather only the evidence warranted to
confirm or reject the current explanation; route to debug if root cause remains
uncertain. Remove temporary instrumentation and touched-diff slop.

## Done When

Each accepted criterion has an in-scope result and proportionate direct evidence;
temporary work is removed and deviations, risks, or blockers stay explicit.

## Escalate

When required state or authority is absent, apply the Ask Gate through the root
before blocking. Stop when new evidence invalidates scope or a change would
affect protected/public behavior; route back to research, debug, or plan.

## Conditional Protocols

Under `skills/using-teamwork/references/`, load only the needed delegation,
verification, debug, artifact, or risk-gated review reference.
