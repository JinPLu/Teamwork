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

Inspect only the owner, flow, state, and invariants needed for the next safe
change. Modify the current producer path, avoiding masking wrappers, fallbacks,
or guessed state. Preserve unrelated changes; delegate only disjoint work.

Reach the shortest safe real run or artifact as early as possible. Use an
auxiliary test, build, review, or inspection only when it unlocks the next
change, distinguishes the current failure, directly checks changed behavior, or
protects a named high-risk boundary. Never substitute plan/mock/static success
for an available real path. Before broadening work, classify discoveries:

- `regression` or `accepted_scope_violation`: fix in scope or stop;
- `pre_existing`: record without attributing or repairing;
- `out_of_scope`: pause and route through the Ask Gate; or
- `suggestion`: record without editing.

On a real failure, fix the first result blocker and rerun the same real path. Use
Debug only while uncertainty prevents a safe fix. Reuse unchanged evidence;
repeat only after a relevant code/environment change, new failure or hypothesis,
or named boundary. Report material results/blockers; remove temporary
instrumentation and diff slop.

## Done When

The requested result is observed on the real path, or the nearest available
direct path is truthfully blocked. With no unchecked named boundary, stop.

## Escalate

When required state or authority is absent, apply the Ask Gate through the root
before blocking. Stop when new evidence invalidates scope or a change would
affect protected/public behavior; route back to research, debug, or plan.

## Conditional Protocols

Under `skills/using-teamwork/references/`, load only the needed delegation,
verification, debug, artifact, or risk-gated review reference.
