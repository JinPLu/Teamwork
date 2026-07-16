---
name: teamwork-execute
description: Use when the user asks to implement, build, change, fix, or continue scoped work and the result-producing path is clear enough to act.
---

# Teamwork Execute

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Produce the requested working result through the shortest authorized path.
Do not reopen scope; verification only supports delivery.

## Enter When

Use when the user authorizes a change and target, result, and boundaries are
explicit or discoverable. A plan is optional; missing state blocks only the
dependent action.

## Do And Boundaries

Inspect only the owner, state, and invariants needed. Modify the current producer;
avoid masking wrappers, fallbacks, or guessed state. Preserve unrelated changes;
delegate disjoint work.

Reach the shortest safe real run or artifact as early as possible. Verify only the changed path
or a named protected boundary. Other checks may only unlock change or distinguish
failure. Never substitute plan/mock/static success for an available real path.
Before broadening, classify discoveries:

- `regression` or `accepted_scope_violation`: fix in scope or stop;
- `pre_existing`: record without attributing or repairing;
- `out_of_scope`: pause and route through the Ask Gate; or
- `suggestion`: record without editing.

On failure, fix the first blocker and rerun the same real path. Use Debug only
while uncertainty prevents a safe fix. Reuse unchanged evidence; repeat only
after relevant change, new failure or hypothesis, or a named boundary. Report
blockers; remove instrumentation and diff slop.

## Done When

Stop when the requested result is observed or the nearest direct path is
truthfully blocked. With no unchecked named boundary, stop.

## Escalate

Apply the Ask Gate through the root only when state or authority is absent.
Authority is separate from plan acceptance. Re-enter Plan only when new evidence
changes accepted scope or criteria. Fresh review only when the user asks or an
accepted risk gate requires it. Protected/public changes require direct boundary
evidence.

## Conditional Protocols

Under `skills/using-teamwork/references/`, load only the needed delegation,
verification, debug, artifact, or risk-gated review reference.
