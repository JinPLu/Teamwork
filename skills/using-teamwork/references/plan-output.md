# Plan Output

Plans describe the destination, protected scope, proof, and stopping conditions.
Do not add sections or formats that do not change execution.

## Chat Plan

For clear bounded work, use only what is needed:

```text
Goal:
Scope / protected boundaries:
Steps:
Verification:
Stop / replan condition:
```

Add dispatch or independent-review guidance only when it is material.

## Durable Plan

Use a durable plan for cross-turn, goal, high-risk, public/shared behavior,
long delegation, or an explicit repository plan. Start with the artifact header
from `artifact-protocol.md`, then include the applicable parts below:

- current evidence and selected direction;
- requirements, execution-critical values, and protected boundaries;
- executable phases with ownership and outputs;
- interfaces or artifacts whose contract matters;
- verification and acceptance evidence;
- stop, retry, and rollback conditions;
- delegation or goal state when used;
- next executable actions.

Use tables or diagrams only when they materially clarify comparisons, branching,
ownership, or state transitions. Section names and order are not an acceptance
contract; required decisions and evidence are.

Goal work additionally preserves Goal Invariants, prior failed evidence,
strategy delta, success/no-progress signals, and retry/stop verdict. Bug plans
include repro and runtime-evidence handling only when diagnosis is part of the
plan.

Workers execute accepted scope. Judges and Reviewers check evidence, scope,
verification, and stop conditions. Delegation records may be compact as long as
ownership, return/blocker, and integration status remain auditable.
