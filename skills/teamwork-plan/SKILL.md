---
name: teamwork-plan
description: Use when selected evidence or a user request requires a lightweight or durable execution plan before edits.
---

# Teamwork Plan

Use this stage after research, diagnosis, or user direction has selected a
direction. The plan must let a worker execute without reopening scope.

Read shared rules only as needed:

- `skills/teamwork/references/workflow-contract.md` for the Evidence
  Interpretation Contract, Context & Cost Discipline, Progress Anchors And
  Artifacts, and Subagent Collaboration Model.
- `skills/teamwork/references/artifact-protocol.md` for durable artifact
  triggers and placeholder hygiene.
- `skills/teamwork/references/goal-iteration.md` for Goal Plan Revision after
  failed autonomous attempts.

## Inputs

- Goal, failure, or decision to resolve.
- Evidence already read: source, logs, tests, diffs, artifacts, commands, or a
  `docs/teamwork/research/YYYY-MM-DD-<slug>.md` research artifact.
- Scope boundaries, sacred boundaries, verification target, budget, and stop
  rules.

If the plan depends on current external behavior, unfamiliar APIs, upstream
bugs, or ambiguous architecture and no adequate evidence exists, route to
`teamwork-research` before planning.

## Evidence And Context

Apply the shared Evidence Interpretation Contract: label important inputs as
`observed`, `inferred`, or `claimed`. Treat names, comments, README prose,
version labels, and prior summaries as claims until corroborated by direct
evidence.

Apply Context & Cost Discipline: prefer local evidence and existing research
artifacts before new external research; fan out only for independent questions
that materially improve the plan.

## Planning Detail Tiers

Use the lightest planning form that preserves correctness.

- Lightweight plan: concise chat/native checklist for bounded low-risk
  single-agent work. Include goal, scope, steps, focused verification, Expected
  Results, and stop condition.
- Durable artifact plan: required for goal-mode, cross-agent, cross-turn,
  high-risk, ambiguous, public/shared behavior, and explicit repository-plan
  requests.

Default durable path:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

`update_plan` may mirror progress, but it is a transient UI-only checklist and
is not the durable source of truth.

Goal-mode durable plans must contain all durable sections below. A compact
execution memo is only for ordinary non-goal work; it is not enough for
non-lightweight autonomous convergence.

## Workflow

1. Restate the root cause or goal in one sentence.
2. Read prior research or direct evidence. If required evidence is missing,
   route to `teamwork-research`.
3. Choose lightweight or durable artifact planning and name the artifact path
   when one exists.
4. Build a Requirements Mapping from each requirement or acceptance criterion
   to observed evidence or verification that will prove it.
5. Define in-scope, out-of-scope, and sacred boundaries.
6. Select the smallest producer-side change that can satisfy the goal.
7. Write ordered implementation steps with exact paths when known.
8. Define focused verification first, broader verification only when warranted,
   and Expected Results for each check.
9. Name risks, stop rules, and evidence that would invalidate the plan.
10. Define Subagent Routing if subagents are used, or when the plan is durable,
    delegated, high-risk, or goal-mode. Include conceptual role, task scope,
    model tier, context strategy, order, independence, owned paths, and why.
    For non-lightweight plans with no subagents, state why main-agent
    continuity is sufficient and why parallel Worker tracks would not help.
    Codex native dispatch fields are derived at dispatch time from the router
    mapping; include native overrides only when they are part of the routing
    decision.
11. Add Worker Handoff and Review Handoff for durable, delegated, high-risk, or
    goal-mode work.

## Goal Plan Revision

When goal verification fails, review returns `revise` or `blocked`, evidence
delta is `no-progress`, acceptance cannot be judged, or execution reports a
plan mismatch, do not retry blindly. Read refreshed research, failed
verification, execution review, rolling report, and current plan. Revise or
replace the durable plan when evidence shows missing research, a stale
assumption, wrong scope, invalid stop rule, or over-strict blocker. Record the
changed plan again and require plan review before execution resumes.

## Quality Gates

- Every planned file traces to the goal.
- No broad refactor, abstraction, cleanup, or downstream behavior change unless
  required by evidence.
- Requirements Mapping is concrete enough for review.
- Verification has commands, artifacts, or checks plus Expected Results.
- Durable plans have no `<...>`, `TODO`, `TBD`, or ellipsis tasks.
- Goal-mode durable plans include all required sections for execution and
  review: Goal, Requirements Mapping, Evidence Read, Scope, Implementation
  Steps, Verification, Risks, Stop Rules, Worker Handoff, Review Handoff, and
  Subagent Routing.
- If subagents are used, routing is specific; if skipped for non-lightweight
  work, the skip rationale is explicit.

## Output

```text
Mode:
- plan

Research Artifact:
- <docs/teamwork/research/YYYY-MM-DD-<slug>.md | none>

Plan Tier:
- <lightweight | durable artifact>
- Artifact Path: <docs/teamwork/plans/YYYY-MM-DD-<slug>.md | none>

Goal:
- ...

Requirements Mapping:
- <requirement>: <observed evidence or verification that will prove it>

Evidence Read:
- <observed|inferred|claimed> <path/command/artifact/research>: <finding>

Scope:
- In: ...
- Out: ...
- Sacred boundaries: ...

Implementation Steps:
- [ ] 1. <path/component> - <minimal change> - <why>

Verification:
- Focused: <command/artifact/check>
- Broader: <command/check or not needed because ...>
- Expected Results: <exact passing output, artifact property, or behavior>

Risks:
- <risk> - <mitigation>

Stop Rules:
- ...

Worker Handoff:
- Execute only the steps above. Do not add adjacent cleanup.

Review Handoff:
- Check scope, diff, tests/artifacts, regressions, and acceptance criteria.

Subagent Routing:
- <role, scope, model tier, context strategy, order, independence, owned paths, and why; or main-agent continuity rationale>
```

For lightweight plans, keep the output compact while preserving Goal, Scope,
Steps, Verification, Expected Results, Stop Rules, and Review Need. For durable
goal-mode plans, keep the memo compact but include every section in the
template.
