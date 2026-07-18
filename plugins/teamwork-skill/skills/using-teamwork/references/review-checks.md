# Review Checks

Use for plan or execution scrutiny. Load specialized verification, debug,
artifact, goal, strict-quality, or release-eval protocols only when triggered.

## Plan Review

Check that:

- the goal, in/out scope, protected boundaries, and acceptance meaning agree;
- execution-critical values are sourced or explicitly left as blockers;
- requirements map to evidence or planned verification;
- phases are executable without hidden broad refactors or invented fallbacks;
- delegation has owned boundaries and a useful return contract when used;
- high-risk or durable work has appropriate stop, rollback, and review gates;
- explicit question-first work has a confirmed exit before enactment.

Return the smallest runnable revision. Block only for missing authority,
critical evidence/resources, or protected-boundary conflict.

## Execution Review

Check that:

- the diff stays within accepted behavior and files; exact line-level matching
  is not required when the implementation remains in scope;
- no unrelated churn, duplicate owner, guessed default, target switch, or
  invariant-masking branch/wrapper/fallback was introduced;
- verification evidence supports each material completion claim and reports its
  real strength;
- delegated writes have returned or blocked and are integrated;
- debug instrumentation is removed unless intentionally accepted;
- durable memory changed only when its protocol was triggered;
- goal work preserves invariants and changes strategy after failed evidence.

Build an acceptance map before reaching a verdict: each accepted criterion ->
candidate change/no-change rationale -> direct evidence -> result -> strength.
Classify a discovery as `regression`, `accepted_scope_violation`,
`pre_existing`, `out_of_scope`, or `suggestion`. Only a regression or accepted
scope violation can become a blocking acceptance failure from that discovery
classification; failed gating evidence is also a blocker. Preserve direct
evidence for pre-existing issues and do not make out-of-scope work implicit.

An initial Judge/Reviewer acceptance review is fresh and limited to accepted
criteria, protected boundaries, and direct evidence. Give each material finding
a stable ID and one class: `BLOCKER`, `FOLLOW-UP`, or `SUGGESTION`.
Other classes are non-blocking. If out-of-scope work is required for an accepted
AC, that failed AC stays a `BLOCKER`; otherwise no open `BLOCKER` means `ACCEPT`.

One corrective recheck may reuse the initial Judge/Reviewer thread. Restrict it
to prior finding IDs, claimed fixes, and direct evidence of a fix-introduced
regression; it is not a fresh full rescan, a monitoring loop, or authority for
recursive delegation/rechecks.

Use `review-lenses.md` for strict maintainability/deslop review,
`verification-patterns.md` for behavior/performance/parity claims,
`debug-mode.md` for debug-derived fixes, and `eval-gate.md` only for Teamwork
package or harness behavior changes.

If acceptance fails, state its finding and route: research, plan, fix, or blocker.
