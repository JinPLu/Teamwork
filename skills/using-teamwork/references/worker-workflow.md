# Worker Workflow

Use for non-lightweight execution and Worker subagent prompts. This owns
Teamwork's compact TDD Gate, Debugging Gate, Staged Execution, delegated Worker
execution, and Verification Before Claims.

## Stage Contract

1. Scope lock: execute only the accepted owned scope. If observed reality
   invalidates the plan, stop and report `blocked` or `needs_context`.
2. Mode declaration: state whether the slice is behavior change, bug/failure,
   mechanical edit, or planned implementation.
3. Evidence setup: identify plan steps, intended files, protected boundaries,
   and proving commands before edits.
4. No silent fallback: confirm required env vars, paths, execution modes,
   hyperparameters, config, and commands are explicit. If missing, block instead
   of inventing defaults or soft redirects.
5. Minimal edit: change producer-side code only; avoid adjacent cleanup unless
   the accepted plan requires it.
6. Fresh verification: run the focused proof after edits and read output before
   claiming support.

## TDD Gate

For behavior changes when practical: write or identify one failing behavior
test, run it to see the expected failure, implement minimally, run passing
focused checks, refactor only while green. If TDD is not practical, record why.

## Debugging Gate

For failures: reproduce or inspect the failure, trace the boundary, state one
hypothesis, test one variable, add or identify a failing repro where practical,
then implement one root-cause fix. After repeated failed fixes or unknown root
cause, stop instead of guessing.

## Run Loop Exit

Every Worker slice needs an exit condition: test passes, expected artifact or
behavior observed, structured output validates, bounded attempt limit reached,
or explicit blocker. Partial verification returns `done_with_concerns`; no
verification returns `blocked` unless the parent explicitly allowed a no-run
handoff.

## Handoff Evidence

Completion must map plan steps to changes, include TDD or repro/root-cause
evidence when applicable, list verification command/result/exit state, and
state whether the evidence supports the claim.
