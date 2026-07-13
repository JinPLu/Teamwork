# Plan Output

Plans describe the destination, protected scope, proof, and stopping conditions.
Do not add sections or formats that do not change execution.

## Codex Plan Mode Bridge

Codex Plan mode owns interaction and the authoritative `plan`; Teamwork owns its
quality gate. The root applies the shared Ask Gate and uses the host's native
input surface when callable. Incorporate answers into the plan; questions are
not completion, and the host owns wait/timeout/resume.

## Decision Gate

Classify from evidence, not file count. A plan is simple only when scope and risk
are fixed and no material user-owned decision remains. Every other plan enters
`grill-me`; explicit negative intent suppresses the interview, not required-input
or safety gates.

Inspect evidence first. Resolve evidence/agent-owned gaps; apply the shared Ask
Gate and ask one material decision at a time with a recommendation.

When no such decision remains, provide one concise **Decision Summary**: goal,
chosen approach, material rejected alternatives, scope/non-goals, protected
boundaries, acceptance meaning, material residual risk, and implementation
authority. Confirm it before the final plan. A change returns to the affected
decision; confirmation does not authorize implementation or extra scope.

Readiness gate before the final plan:

- inspect owner/flow, tests/config, active artifacts, and protected boundaries;
- classify gaps as evidence-owned, agent-owned, user-decision, required-input, or
  confirmation; resolve the first two and send remaining candidates through the Ask Gate;
- source critical values as `user`, `repository`, `derived`, or `unresolved`;
  justify derivations and pause only actions dependent on unresolved values;
- reconcile corrections and discard invalidated premises;
- map each requirement to an owned action and proof; name each phase's surface,
  inputs, output, dependencies, verification, and stop/replan condition; and
- state scope/non-goals, protected surfaces, risks, blockers, and next action.

## Chat Plan

For clear bounded work, use only what is needed:

```text
Goal:
Scope / protected boundaries:
Steps:
Verification:
Stop / replan condition:
```

Add dispatch/review guidance only when material.

## Durable Plan

Use a durable plan for cross-turn, goal, high-risk, public/shared, delegated, or
explicit repository work. Start with the `artifact-protocol.md` header, then:

- current evidence and selected direction;
- requirements, sourced execution-critical values, and protected boundaries;
- executable phases with ownership and outputs;
- interfaces or artifacts whose contract matters;
- verification and acceptance evidence;
- stop, retry, and rollback conditions;
- delegation or goal state when used;
- next executable actions.

Use visuals only when they clarify comparison, branching, ownership, or state.
Section order is not an acceptance contract; coverage, sourced values, ownership, and proof are.

Goal work preserves invariants, failed evidence, strategy delta, success/no-progress,
and retry/stop verdict. Bug plans add repro/runtime evidence only for diagnosis.

Workers execute accepted scope; Judges/Reviewers check evidence, scope, proof,
and stops. Delegation stays auditable by owner, result/blocker, and integration.
