# Goal Iteration

Use only when the user requests convergence, repeated attempts, or an explicit
budget. Preserve the goal while changing strategy in response to evidence.

## Goal Facts

Record the objective, done evidence, scope/non-goals, protected boundaries,
Goal Invariants, available budget or runtime limit, and blocker conditions.
Do not invent a numeric iteration/token/time budget when none was supplied or
provided by the runtime; use a bounded no-progress stop instead.

Retain accepted scope, criteria, authority, and Goal Invariants on every retry.
Failed verification, a new hypothesis, or a known local fix changes strategy,
not those facts. Return to Plan when accepted scope or criteria must change.

Use a native Codex goal only when the user explicitly requests that control
surface or accepts a Goal Proposal. Otherwise keep the accepted plan and, when
cross-turn continuity is needed, a rolling report.

## Loop

```text
read accepted scope, invariants, and latest failed claim
-> select only its affected stage
-> verify that claim
-> review only if acceptance claims changed or the final risk gate requires it
-> accept, change strategy, or stop
```

Use the smallest evidence-backed route:

- known fix to a failed check: Execute -> verify;
- reproducible failure with unknown cause: Debug -> verify, then Execute if a
  known fix results;
- broad missing evidence: Research;
- accepted scope or criteria must change: Plan;
- changed acceptance claim or final required risk gate: Review.

Do not replay research, plan, execute, and review merely because an earlier
check failed.

After a failed, partial, blocked, or no-progress attempt, read the latest failed
evidence and prior attempt summary before more work. Record:

- what was tried and what evidence failed;
- constraints and Goal Invariants that still hold;
- what must not be repeated;
- the strategy delta for the next attempt.

The strategy delta must name the changed evidence, hypothesis, affected claim,
and next stage. If it cannot, count no progress and stop rather than replaying
stages. Apply the shared Ask Gate only when a user-owned required input,
observation, or decision is what prevents a distinct next strategy. Repeated
no-progress attempts are a no-progress stop.

## Durable Checkpoint

Create or update a rolling report only for cross-turn/resumable work, repeated
failures, or when the user requests durable state. A compact attempt row is
enough:

```text
Attempt | Invariants | Change/hypothesis | Verification/failure | Result/next
```

Add a failure reflection only after failed, partial, blocked, or no-progress
work. The report is continuity evidence, not a replacement for source, plan,
verification, or review.

Stop on verified success, exhausted explicit/runtime budget, destructive or
credential risk, unavailable required resources, protected-boundary conflict,
unresolved user-owned intent, or repeated no progress.
