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

Return the smallest revision that makes the plan runnable. Block only for
missing authority, critical evidence/resources, or a protected-boundary
conflict.

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

Use `review-lenses.md` for strict maintainability/deslop review,
`verification-patterns.md` for behavior/performance/parity claims,
`debug-mode.md` for debug-derived fixes, and `eval-gate.md` only for Teamwork
package or harness behavior changes.

If acceptance fails, state the actionable finding and next route: research,
plan revision, implementation correction, or true blocker.
