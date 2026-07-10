# Goal Iteration

Use only when the user requests convergence, repeated attempts, or an explicit
budget. Preserve the goal while changing strategy in response to evidence.

## Goal Contract

Record the objective, done evidence, scope/non-goals, protected boundaries,
Goal Invariants, available budget or runtime limit, and blocker conditions.
Do not invent a numeric iteration/token/time budget when none was supplied or
provided by the runtime; use a bounded no-progress stop instead.

Use a native Codex goal only when the user explicitly requests that control
surface or accepts a Goal Proposal. Otherwise keep the accepted plan and, when
cross-turn continuity is needed, a rolling report.

## Loop

```text
read invariants and latest evidence
-> research/debug if needed
-> update the runnable plan
-> execute
-> verify
-> independent review when required
-> accept, change strategy, or stop
```

After a failed, partial, blocked, or no-progress attempt, read the latest failed
evidence and prior attempt summary before more work. Record:

- what was tried and what evidence failed;
- constraints and Goal Invariants that still hold;
- what must not be repeated;
- the strategy delta for the next attempt.

If there is no evidence-backed strategy delta, count no progress and stop or ask
for direction rather than repeating the attempt.

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
