---
name: teamwork-design
description: Use when a Teamwork request needs divergent research or an executable plan before implementation.
---

# Teamwork Design

Use this subskill before implementation. It has two explicit modes:

- `mode: research` - divergent investigation, discussion, option generation.
- `mode: plan` - convert a selected direction into executable worker steps.

Keep the modes separate. Research may recommend a direction, but it must not
pretend to be an execution plan. Planning requires a chosen direction; if the
direction is still uncertain, return to `mode: research`.

## Shared Inputs

- Goal, failure, or decision to resolve.
- Known evidence: command output, logs, artifacts, diffs, source locations.
- Sacred boundaries: principles, contracts, architecture, user constraints.
- Mutable scope: exact areas that may change.
- Verification target: command, artifact, metric, or acceptance criteria.
- Budget and stop rules.

State missing inputs as assumptions before they affect behavior. If an
assumption would change public behavior, protected claims, data contracts, or
architecture, stop and ask instead of guessing. In `teamwork`
`mode: goal`, safe internal details should become explicit assumptions rather
than user questions.

## Evidence Interpretation Contract

Treat file names, directory names, version labels such as `v2`, `latest`,
comments, README prose, historical notes, and prior summaries as claims, not
facts. Before using them to choose a direction or write a plan, corroborate
them with direct evidence such as source call paths, tests, configuration,
command output, artifact properties, or git diff.

Label important findings as:

- `observed`: direct evidence you inspected.
- `inferred`: a conclusion drawn from observed evidence.
- `claimed`: narrative, naming, or documentation text that still needs
  corroboration.

Do not let a claimed label decide scope, canonical files, version freshness, or
completion status without at least one direct evidence cross-check.

## Context & Cost Discipline

- Prefer local files, diffs, logs, tests, and artifacts before MCP or web.
- Use MCP/web only for external constraints, official/current information, or
  user-authorized evidence not present locally.
- Use subagents for independent read-heavy tracks by default. Give writing
  subagents exact file slices or worktree isolation.
- Use a Designer pass with `high reasoning` when the uncertainty is about
  requirements, architecture, cross-module plans, or product behavior. Use
  Explorer for evidence collection; use Designer for option framing and
  tradeoffs.
- Ask subagents to return condensed evidence, confidence, dissent, and open
  questions instead of large raw logs.
- Default research/review fan-out is at most 3 parallel subagents unless the
  user gives a larger budget.

## mode: research

Use when the next step is unclear, the problem has multiple plausible causes,
or option generation is useful before selecting a direction.

Use Codex subagents for independent research tracks when available and useful.
Each subagent prompt must include the exact question, scope, evidence to read,
constraints, and return format. Do not give subagents broad permission to edit
unless they are explicitly the worker for an accepted plan with file ownership.
If subagents are unavailable, use separate local passes and label the
limitation.

If the research question includes ambiguous requirements, architecture choices,
cross-module design, or product behavior, consider a Designer with
`high reasoning` before planning. Do not substitute a Worker for unresolved
design work; Workers execute accepted plans.

Workflow:

1. Define the research question and success criteria.
2. Split the topic into independent tracks when useful: symptoms, source paths,
   artifacts, external constraints, alternative designs.
3. Assign each track a role or pass. Each pass reads primary evidence directly
   and returns findings, confidence, and open questions.
4. Generate options before committing. Prefer simple, local, producer-side
   fixes over broad rewrites or downstream cleanup.
5. Compare options against the goal, sacred boundaries, verification path, and
   budget.
6. Preserve dissent. Label minority findings as blocker, warning, or follow-up.
7. Stop when a direction is selected, evidence is insufficient, budget is
   exhausted, or only protected/ambiguous decisions remain.

Output:

```text
Mode:
- research

Research Question:
- ...

Assumptions:
- ...

Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>

Options:
1. <option> - benefits, risks, verification, boundary impact
2. ...

Dissent / Unresolved:
- ...

Recommendation:
- <selected direction or blocked>
- Why this is the simplest sufficient path
```

## mode: plan

Use after research or diagnosis has selected a direction. The output is a plan
that a worker can execute without expanding scope.

### Plan Artifact Requirement

All plans must be written to a durable Markdown plan artifact before execution,
including lightweight, low-risk, and single-file changes. Default path:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

- Lightweight changes may use a concise artifact, but they still need the
  artifact path, scope, implementation steps, focused verification, expected
  results, and final review handoff.
- High-risk, cross-module, ambiguous, or long-running work: the artifact must
  use checkbox tasks, exact paths, test-first or verification-first steps,
  necessary code snippets, expected command output or artifact properties, and
  explicit worker/reviewer handoffs.

The durable artifact is the execution and review source of truth. `update_plan`
may mirror progress as a transient checklist, but it must never be the only
plan.

Workflow:

1. Restate the root cause or goal in one sentence.
2. Classify the detail tier and write or update the durable plan artifact.
   Report its path.
3. Map each requirement or acceptance criterion to evidence already read or to
   the exact verification that will prove it.
4. Define scope: in scope, out of scope, and sacred boundaries.
5. Identify the smallest producer-side change that can satisfy the goal.
6. Break work into ordered, executable steps with exact paths when known.
7. Design focused verification first; add broader checks only when shared
   behavior, public contracts, or user-visible workflows are affected.
8. List expected verification results, risks, rollback/rework strategy, and
   evidence that would invalidate the plan.
9. Avoid unresolved placeholders, ellipses as tasks, and generic testing or
   edge-case instructions; each step must be executable or explicitly blocked.
10. Define Subagent Routing: role, task scope, model tier, parallel or serial
    ordering, and why each role is needed or skipped.
11. Prepare separate handoffs for worker execution and reviewer checks.

Plan quality gates:

- Simplicity first: no abstraction or refactor unless required by evidence.
- Surgical edits: every planned file must trace to the goal.
- Evidence-driven: the plan identifies what will prove success.
- Boundary-safe: no step changes protected contracts or principles.
- Budget-aware: include stop conditions for no progress, blocker, or budget.
- Durable always: every plan has a Markdown artifact at
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- Routing-aware: every plan includes Subagent Routing with role, task scope,
  model tier, parallel or serial ordering, and why each role is needed or
  skipped. A plan without Subagent Routing is incomplete.

Output:

```text
Mode:
- plan

Plan Artifact:
- Path: docs/teamwork/plans/YYYY-MM-DD-<slug>.md
- Durable source of truth: yes

Root Cause / Goal:
- ...

Requirements Mapping:
- <requirement or acceptance criterion>: <observed evidence or verification that will prove it>

Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>

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
- Explorer: <needed | skipped> | scope: <evidence track> | model tier: <fast | standard> | <parallel | serial> | why: <...>
- Designer: <needed | skipped> | scope: <requirements/architecture/product behavior> | model tier: <high reasoning> | <parallel | serial> | why: <...>
- Judge: <needed | skipped> | scope: <plan review> | model tier: <high reasoning> | <serial before execution> | why: <...>
- Worker: <main agent | subagent> | scope: <exact files or modules> | model tier: <fast | standard> | <serial or parallel with non-overlapping ownership> | why: <...>
- Reviewer: <main distinct pass | subagent | codex review command> | scope: <diff, artifacts, tests, regressions> | model tier: <high reasoning> | <serial after verification> | why: <...>
```
