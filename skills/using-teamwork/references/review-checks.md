# Review Checks

Use for `teamwork-review` plan/execution evidence scrutiny.

## Plan Review

1. **Scope and verification**: every step traces to the goal; scope has explicit in/out/protected boundaries; verification has Expected Results; Required Values / Invariants and accepted fallback contracts are explicit; assumptions and confidence match observed evidence.

2. **Evidence and requirements**: gaps are resolved or the plan is `ask`/`blocked-for-clarification`; acceptance maps to observed evidence or verification; current APIs, upstream bugs, and ambiguous architecture cite evidence or explain why local evidence suffices. For broad/seeded research, require coverage/source-class/citation/rejected-source evidence.

3. **Dispatch and handoff**: material tracks have Dispatch Guidance; delegated work has prompt packets, output schema, ownership, and escalation triggers; durable/high-risk/public plans have a verdict or residual risk.

4. **Question-first handoff**: active grill/question-first override has a confirmed packet or explicit exit before planning, execution, goal handoff, or Worker dispatch.

5. **Goal continuity**: retry plans include Goal Invariants, Replay Preflight, Do Not Repeat, Goal Anchor, Drift Verdict, and Retry Verdict.

Return `revise` when required artifacts are missing, placeholders remain, confidence is overstated without observed evidence, requirement gaps are unresolved, or dispatch/handoff requirements are unmet.

## Execution Review

1. **Diff scope**: only planned files/lines; no unrelated edits, generated churn, bug-hiding cleanup, invariant-masking branches, branch/mode accumulation, duplicate owners, guessed defaults, or target switches.

2. **Verification**: focused verification ran with evidence; claims match observed diff, logs, tests, or artifacts. For behavioral, UI, performance, memory, migration, or parity claims, check `verification-patterns.md` for baseline/treatment and proof strength.

3. **Dispatch accounting**: Actual Dispatch Log records roles, native fields, prompts, returned packets, and blocker rationale for delegated work.

4. **Durable memory check**: current-state changes need material delta and evidence; reject churn-only writes. If accepted active state changed without memory update or `none`/`deferred`, name residual risk. Memory promotion check: candidate memory or docs graph output needs direct evidence paths, currentness, scope, and protected data disposition.

5. **Manual smoke**: Manual smoke evidence captures source, observed behavior, pass/fail result, and acceptance criterion mapping for any claim that depends on human-observed state.

6. **Debug evidence**: debug-derived fixes require repro evidence or justified
   non-repro path, hypothesis-to-evidence mapping, root-cause support, post-fix
   verification, and cleanup of temporary instrumentation/logs/scaffolding.
   Leftover debug artifacts are acceptance failures unless the plan keeps them
   as intentional observability.

7. **Maintainability/deslop lens**: when strict code quality review, deslop, PR
   walkthrough, fallback masking, or structural regression appears, use
   `review-lenses.md`. Keep bounded deslop separate from broad structural review.
   Require existing-path evidence before accepting new branches, modes, wrappers,
   or fallback.

8. **Goal drift**: goal-mode acceptance requires Attempt Record, Failure Reflection when applicable, and only `accept | revise | blocked`.

9. **Question-first drift**: missing packet/exit, invented answers, premature enactment, edits, or subagent bypass during active override means `revise` or `blocked`.

If work cannot be accepted, state the next route: research refresh, plan revision, implementation correction, or true blocker.
