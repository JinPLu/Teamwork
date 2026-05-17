---
name: teamwork-plan
description: Use when a multi-step or risky change needs an executable plan before implementation, or when the user asks for a plan — invoke before writing code to keep scope and verification explicit.
---

# Teamwork Plan

Use this subskill after `teamwork-research`, direct diagnosis, or explicit user
direction has selected a direction. Prefer reading the research artifact when
one exists before planning. The output is a plan that a worker can execute
without expanding scope.

## Shared Inputs

- Goal, failure, or decision to resolve.
- Research artifact path when prior research exists, normally
  `docs/teamwork/research/YYYY-MM-DD-<slug>.md`.
- Known evidence: command output, logs, artifacts, diffs, source locations.
- Sacred boundaries: principles, contracts, architecture, user constraints.
- Mutable scope: exact areas that may change.
- Verification target: command, artifact, metric, or acceptance criteria.
- Budget and stop rules.

If the plan depends on current external behavior, unfamiliar API details,
upstream errors, or ambiguous product/architecture choices and no research
artifact exists, stop and route to `teamwork-research` before planning.

State missing inputs as assumptions before they affect behavior. If an
assumption would change public behavior, protected claims, data contracts, or
architecture, stop and ask instead of guessing. In `teamwork-goal`
`mode: goal`, safe internal details should become explicit assumptions rather
than user questions.

## Evidence Interpretation Contract

Treat file names, directory names, version labels such as `v2`, `latest`,
comments, README prose, historical notes, and prior summaries as claims, not
facts. Before using them to choose a plan, corroborate them with direct evidence
such as source call paths, tests, configuration, command output, artifact
properties, git diff, or a readable research artifact.

Label important findings as:

- `observed`: direct evidence you inspected.
- `inferred`: a conclusion drawn from observed evidence.
- `claimed`: narrative, naming, or documentation text that still needs
  corroboration.

Do not let a claimed label decide scope, canonical files, version freshness, or
completion status without at least one direct evidence cross-check.

## Context & Cost Discipline

- Prefer local files, diffs, logs, tests, artifacts, and existing research
  artifacts before new MCP or web research.
- Route back to `teamwork-research` when external constraints or stale
  assumptions need investigation before planning.
- Fan out subagents only when planning needs independent evidence, design,
  judge, or review tracks that can run in parallel without blocking the main
  agent's immediate next step. Each track needs a specific question, scope,
  return format, and non-overlapping write ownership if edits are allowed.
- Ask subagents to return condensed evidence, confidence, dissent, and open
  questions instead of large raw logs.
- Default planning fan-out is at most 3 parallel subagents unless the user gives
  a larger budget. Do not fan out when main-agent continuity is cheaper and
  safer than coordination.

## Planning Detail Tiers

Use the lightest planning form that preserves correctness:

- Lightweight plan: concise chat/native checklist for simple, bounded,
  single-agent work. Must include scope, steps, focused verification, expected
  result, and stop condition.
- Durable artifact plan: required for cross-agent execution, cross-turn work,
  high-risk or ambiguous changes, public/shared behavior changes, explicit user
  requests for a repository plan, and all `teamwork-goal` execution.

Default durable artifact path:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

The durable artifact is the execution and review source of truth when it exists.
`update_plan` may mirror progress as a transient checklist, but it must never be
the only plan for durable-required work.

## Workflow

1. Restate the root cause or goal in one sentence.
2. Read the research artifact if one exists. If required external or ambiguous
   evidence is missing, route to `teamwork-research` before planning.
3. Classify the detail tier. Use a lightweight plan for bounded low-risk work;
   write or update the durable plan artifact when the durable triggers apply.
   Report the chosen tier and artifact path when one exists.
4. Map each requirement or acceptance criterion to evidence already read or to
   the exact verification that will prove it.
5. Define scope: in scope, out of scope, and sacred boundaries.
6. Identify the smallest producer-side change that can satisfy the goal.
7. Break work into ordered, executable steps with exact paths when known.
8. Design focused verification first; add broader checks only when shared
   behavior, public contracts, or user-visible workflows are affected.
9. List expected verification results, risks, rollback/rework strategy, and
   evidence that would invalidate the plan.
10. Avoid unresolved placeholders, ellipses as tasks, and generic testing or
    edge-case instructions; each step must be executable or explicitly blocked.
11. Define Subagent Routing when subagents are used, or when the plan is
    durable, delegated, high-risk, or goal-mode: conceptual role, task scope,
    Teamwork model tier, context strategy, parallel or serial ordering, and why
    each role is needed. For lightweight plans with no subagents, omit the
    routing section instead of explaining ceremony away.
    Codex native dispatch fields are derived at dispatch time from the router
    mapping; include them in a plan only when a non-default native override is
    itself part of the decision.
12. Prepare separate handoffs for worker execution and reviewer checks when the
    plan is durable, delegated, or high-risk.

## Plan Quality Gates

- Simplicity first: no abstraction or refactor unless required by evidence.
- Surgical edits: every planned file must trace to the goal.
- Evidence-driven: the plan identifies what will prove success.
- Research-grounded: plans depending on external behavior, upstream bugs,
  current CLI/API behavior, or ambiguous architecture claims cite a readable
  research artifact or state why local evidence is enough.
- Boundary-safe: no step changes protected contracts or principles.
- Budget-aware: include stop conditions for no progress, blocker, or budget.
- Durable when warranted: goal-mode, high-risk, cross-agent, cross-turn,
  ambiguous, public/shared behavior, and explicitly requested repository plans
  use `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- Routing-aware: if subagents are used, name role, task scope, Teamwork model tier,
  context strategy, parallel or serial ordering, and why. If subagents are
  skipped, state why main-agent continuity is sufficient.
- Codex-aware: ordinary plans use conceptual routing. Native dispatch fields
  are derived from `skills/teamwork/SKILL.md` when dispatching; write them in a
  plan only when a non-default native override is itself part of the routing
  decision.

Output:

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
- <requirement or acceptance criterion>: <observed evidence or verification that will prove it>

Evidence Read:
- <observed|inferred|claimed> <path/command/artifact/research>: <finding>

Scope:
- In: ...
- Out: ...
- Sacred boundaries: ...

Implementation Steps:
- [ ] 1. <path/component> - <minimal change> - <why>
- [ ] 2. ...

Verification:
- Focused: <command/artifact/check>
- Broader: <command/check or not needed because ...>
- Expected Results: <exact passing output, artifact property, or behavioral state>

Risks:
- <risk> - <mitigation>

Stop Rules:
- ...

Worker Handoff:
- Execute only the steps above. Do not add adjacent cleanup.

Review Handoff:
- Check scope, diff, tests/artifacts, regressions, and acceptance criteria.

Subagent Routing:
- <if subagents are used, list role, scope, model tier, context strategy, order, independence from other tracks, and why; for durable/delegated/high-risk/goal-mode plans with no subagents, state main-agent continuity is sufficient>
```

For lightweight plans, keep the output compact while still including Goal,
Scope, Steps, Verification, Stop Rules, and Review Need. For durable artifact
plans, include all sections above in the artifact.
