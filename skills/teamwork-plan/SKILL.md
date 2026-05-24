---
name: teamwork-plan
description: Use when asked to plan, implement, fix, add, change, refactor, or modify behavior and no accepted plan exists before edits.
---

# Teamwork Plan

Use after research, diagnosis, or user direction selects a path. Also use
before non-trivial implementation when no accepted plan exists. The plan must
let a worker execute without reopening scope.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence,
  context, artifacts, and subagent policy.
- `skills/using-teamwork/references/artifact-protocol.md` for durable artifact
  triggers and hygiene.
- `skills/using-teamwork/references/plan-output.md` for plan templates.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal-plan
  revision.

## Inputs

- Goal, failure, or decision to resolve.
- Evidence read: source, logs, tests, diffs, artifacts, commands, or research.
- Scope boundaries, protected boundaries, verification target, budget, and stop
  rules.

If the plan depends on external behavior, unfamiliar APIs, upstream bugs, or
ambiguous architecture without evidence, route to `teamwork-research`.

## Planning Tiers

Use the lightest planning form that preserves correctness.

- Lightweight plan: bounded low-risk work; include goal, scope, steps, focused
  verification, Expected Results, stop condition, and review need.
- Durable plan: required for goal-mode, cross-turn, high-risk, ambiguous,
  public/shared behavior, long-running delegation, complex Worker fan-out, or
  explicit repository-plan requests.

Default durable path: `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.

## Workflow

1. Restate goal or root cause.
2. Read direct evidence or prior research.
3. Label key evidence as `observed`, `inferred`, or `claimed`.
4. Choose lightweight or durable planning and name the artifact path if any.
5. Build Requirements Mapping from each requirement to evidence or
   verification that will prove it.
6. Define in-scope, out-of-scope, and protected boundaries.
7. Choose the smallest producer-side change.
8. Write ordered implementation steps with exact paths when known.
9. Define focused verification, Expected Results, risks, and stop rules.
10. For 2+ independent-track work, define lightweight `Dispatch:` or durable
    `Subagent Routing`; otherwise state why main-agent continuity is cheaper or
    safer.
11. Add Worker Handoff and Review Handoff when durable/delegated/high-risk.
12. Codex native dispatch fields are derived at dispatch time from the accepted
    routing policy.

## Quality Gates

- Every planned file traces to the goal.
- No broad refactor, abstraction, formatting churn, or downstream cleanup
  unless required by evidence.
- Verification has concrete commands, artifacts, checks, or expected behavior.
- Durable plans have no `<...>`, `TODO`, `TBD`, or ellipsis tasks.
- Goal-mode durable plans include all sections required by `plan-output.md`,
  including Search Keys and Abstract.

## Output

Use a compact chat plan for lightweight work. For durable plans, use
`skills/using-teamwork/references/plan-output.md`.
