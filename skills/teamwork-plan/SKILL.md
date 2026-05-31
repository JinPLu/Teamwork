---
name: teamwork-plan
description: Use when asked to plan, implement, fix, add, change, refactor, or modify behavior and no accepted plan exists before edits.
---

# Teamwork Plan

Use after research, diagnosis, or user direction selects a path. Also use
before non-trivial implementation when no accepted plan exists. The plan lets a
worker execute without reopening scope.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence, artifacts, and boundaries.
- `skills/using-teamwork/references/dispatch-policy.md` for Designer/Judge and Dispatch Guidance.
- `skills/using-teamwork/references/subagent-prompt-contract.md` before delegated prompt packets.
- `skills/using-teamwork/references/plan-output.md` for durable or complete handoff templates.
- `skills/using-teamwork/references/artifact-protocol.md` for durable plan
  triggers and optional current-state lookup.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal-plan revision.

## Inputs

Goal, evidence, scope, protected boundaries, verification target, budget, and
stop rules. If external behavior, unfamiliar APIs, upstream bugs, or ambiguous
architecture lack evidence, route to `teamwork-research`.

## Planning Tiers

Use the lightest planning form that preserves correctness.

- Lightweight plan: bounded low-risk work; include goal, scope, Dispatch
  Guidance, steps, verification, Expected Results, stop condition, review need.
  Use lightweight `Dispatch Guidance:` for expected subagent routing. Use
  `Dispatch Guidance: none` only when the work is single-track, tightly
  coupled, or cheaper to keep local under Dispatch Economics.
- Durable plan: required for goal-mode, cross-turn, high-risk, ambiguous,
  public/shared behavior, long delegation, complex Worker fan-out, or explicit
  repository-plan requests.

Default durable path: `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.

## Workflow

1. Restate goal/root cause and label evidence `observed`, `inferred`, or
   `claimed`.
2. Build Requirements Mapping from each requirement to evidence or
   verification.
3. Define in/out/protected scope and choose the smallest producer-side change.
4. Run the Parallelization Gate before implementation steps: split before implementation steps by default for independent tracks, apply the Subagent Tool
   Discovery Gate when subagents are authorized, or emit `Dispatch Exception:`
   with the allowed reason.
5. Use Designer for ambiguous choices unless observed evidence already fixes
   the decision. Use a fresh-context Judge before delivering high-risk,
   durable, delegated, or goal-mode plans; if unavailable after discovery or
   explicitly opted out, label the plan `unreviewed`.
6. Write `Dispatch Guidance:` or durable `Subagent Routing`; guidance helps
   execution but is not the only dispatch authorization.
7. Add Subagent Prompt Packets only for delegated roles.
8. Write ordered steps, verification, Expected Results, risks, stop rules, and
   handoffs.

## Quality Gates

- Every planned file traces to the goal.
- No broad refactor, abstraction, formatting churn, or downstream cleanup
  unless evidence requires it.
- `Dispatch Guidance: none` requires a continuity rationale.
- Durable/high-risk/ambiguous plans require Judge verdict or an explicit
  `Dispatch Exception:` and `unreviewed` label.
- Delegated plans name prompt contract, context strategy, ownership, and
  Required Output Schema.
- Goal-mode durable plans include Search Keys and Abstract.
- Platform native dispatch fields are derived at dispatch time from the active
  stage decision and runtime platform, not copied blindly from plan prose.

## Output

Use a compact chat plan for lightweight work. For durable plans, use
`skills/using-teamwork/references/plan-output.md`.
Include `Memory Delta:` only when durable project memory was checked or
changed.
