---
name: run-analyze-goal
description: >-
  Use as the autonomous controller for a complete run-analyze-optimize loop:
  research/discuss if needed, plan, review plan, execute, review execution, and
  continue or stop based on verification, budget, or blockers.
disable-model-invocation: true
---

# Run-Analyze Goal

Use this subskill when the user gives a goal, command, artifact target, or
failure and wants autonomous progress to verified success or a clear stop.

## Controller Contract

- No executor self-declares completion.
- Every completion claim passes review.
- Assumptions are explicit before they affect behavior.
- Prefer the simplest producer-side fix that satisfies the goal.
- Make surgical, minimal edits only after a reviewed plan.
- Preserve role separation: research, planning, execution, and review are
  distinct passes even when handled by one agent.
- Preserve dissent from independent reads and reviewers.

## Inputs

- Goal, command, failing workflow, or expected artifact.
- Success criteria and verification method.
- Sacred boundaries and mutable scope.
- Budget: max iterations, wall time, token/cost ceiling, or stop signal.

Default budget when unspecified:

- Maximum 3 optimization iterations.
- Stop after 2 consecutive iterations with no evidence delta.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing credentials, unavailable required resources, or ambiguous product
  intent that affects behavior.

## Loop

1. Initialize: state goal, assumptions, sacred boundaries, mutable scope,
   verification target, and budget.
2. Research/discuss if needed: use divergent investigation when causes or
   options are unclear. Read evidence independently and preserve dissent.
3. Plan: produce an executable minimal plan with scope, steps, verification,
   risks, and stop rules.
4. Review plan: run a distinct mode: plan review. Revise until pass or blocked.
5. Execute: implement only the accepted plan with minimal edits.
6. Verify: run focused checks first and collect real evidence.
7. Review execution: run a distinct mode: execution review over diff,
   artifacts, tests, regressions, and acceptance criteria.
8. Decide: accept only if verification and execution review pass; otherwise
   continue with a new hypothesis, stop at budget, or report blocker.

## Continue / Stop Rules

Continue only when:

- The target is unmet and an optimizable root cause remains.
- Verification improved but acceptance criteria are not yet met.
- Review found a fixable issue within scope and budget.

Stop when:

- Success criteria are verified and execution review passes.
- Budget is exhausted.
- Two iterations show no evidence delta.
- The remaining issue would violate sacred boundaries.
- Required credentials, resources, or user decisions are unavailable.
- The user stops the loop.

## Final Report

```text
Goal:
- ...

Boundary:
- Sacred boundary: untouched | blocked at <issue>

Iterations:
- <n>: research/plan/execute/review summary

Verification:
- <command/artifact/check>: <result>

Review:
- Plan review: <verdict>
- Execution review: <verdict and dissent>

Unresolved:
- <none or blockers>

Conclusion:
- accept | blocked | budget exhausted | stopped
```
