# Review Checks

Use for `teamwork-review` when a plan or execution needs evidence-based scrutiny.

## Plan Review

1. **Scope and verification**: every step traces to the goal; scope has explicit in/out/protected boundaries; verification includes focused checks and Expected Results; Required Values / Invariants and accepted fallback contracts are explicit; assumptions, uncertainty, and confidence match observed evidence.

2. **Evidence and requirements**: requirement gaps are resolved or the plan is `ask`/`blocked-for-clarification`; each acceptance criterion maps to observed evidence or verification; current APIs, upstream bugs, and ambiguous architecture cite evidence or explain why local evidence suffices. For broad/seeded research, require coverage/source-class/citation/rejected-source evidence.

3. **Dispatch and handoff**: independent material tracks have Dispatch Guidance; delegated work has prompt packets, output schema, ownership, and escalation triggers; durable/high-risk/public plans have a Judge/Reviewer verdict or explicit residual risk statement.

4. **Goal continuity**: goal-mode retry plans include Goal Invariants, Replay Preflight, Do Not Repeat, Goal Anchor fields, Drift Verdict, and Retry Verdict.

Return `revise` when required artifacts are missing, placeholders remain, confidence is overstated without observed evidence, requirement gaps are unresolved, or dispatch/handoff requirements are unmet.

## Execution Review

1. **Diff scope**: touches only planned files/lines; no unrelated edits, generated churn, cleanup hiding producer bugs, invariant-masking branches, guessed hyperparameters, or target switches.

2. **Verification**: focused verification ran with concrete evidence; acceptance claims match observed diff, logs, tests, or artifacts; expected artifacts, outputs, or UI state match acceptance criteria. For behavioral, UI, performance, memory, migration, or parity claims, check `verification-patterns.md` for baseline/treatment and proof strength.

3. **Dispatch accounting**: Actual Dispatch Log records roles, native fields, prompts, returned packets, and blocker rationale for delegated work.

4. **Durable memory check**: if current-state files changed, require a material delta and evidence; reject churn-only writes. If accepted active state changed without a memory update or explicit `none`/`deferred` disposition, name the residual risk. Memory promotion check: candidate memory or docs graph output requires direct evidence paths, currentness, scope, and protected data disposition before becoming canonical Teamwork memory.

5. **Manual smoke**: Manual smoke evidence captures source, observed behavior, pass/fail result, and acceptance criterion mapping for any claim that depends on human-observed state.

6. **Debug evidence**: debug-derived fixes require repro evidence or justified
   non-repro path, hypothesis-to-evidence mapping, root-cause support, post-fix
   verification, and cleanup of temporary instrumentation/logs/scaffolding.
   Leftover debug artifacts are acceptance failures unless the plan keeps them
   as intentional observability.

7. **Maintainability/deslop lens**: when strict code quality review, deslop, PR
   walkthrough, fallback masking, or structural regression appears, use
   `review-lenses.md`. Keep bounded deslop separate from broad structural review.

8. **Goal drift**: goal-mode acceptance requires Attempt Record, Failure Reflection when applicable, and no lifecycle verdict outside `accept | revise | blocked`.

If work cannot be accepted, state the next route: research refresh, plan revision, implementation correction, or true blocker.
