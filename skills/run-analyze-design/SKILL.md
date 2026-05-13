---
name: run-analyze-design
description: Use when a run/analyze/optimize request needs divergent research or an executable plan before implementation.
---

# Run-Analyze Design

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
architecture, stop and ask instead of guessing. In `run-analyze-optimize`
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

Workflow:

1. Restate the root cause or goal in one sentence.
2. Define scope: in scope, out of scope, and sacred boundaries.
3. Identify the smallest producer-side change that can satisfy the goal.
4. Break work into ordered, executable steps with exact paths when known.
5. Design focused verification first; add broader checks only when shared
   behavior, public contracts, or user-visible workflows are affected.
6. List risks, rollback/rework strategy, and evidence that would invalidate the
   plan.
7. Prepare separate handoffs for worker execution and reviewer checks.

Plan quality gates:

- Simplicity first: no abstraction or refactor unless required by evidence.
- Surgical edits: every planned file must trace to the goal.
- Evidence-driven: the plan identifies what will prove success.
- Boundary-safe: no step changes protected contracts or principles.
- Budget-aware: include stop conditions for no progress, blocker, or budget.

Output:

```text
Mode:
- plan

Root Cause / Goal:
- ...

Scope:
- In: ...
- Out: ...
- Sacred boundaries: ...

Implementation Steps:
1. <path/component> - <minimal change> - <why>
2. ...

Verification:
- Focused: <command/artifact/check>
- Broader: <command/check or not needed because ...>

Risks:
- <risk> - <mitigation>

Stop Rules:
- ...

Worker Handoff:
- Execute only the steps above. Do not add adjacent cleanup.

Review Handoff:
- Check scope, diff, tests/artifacts, regressions, and acceptance criteria.

Subagent Plan:
- Judge agent: <needed | not needed because ...>
- Worker agent: <main agent | subagent with exact scope>
- Review agent: <main distinct pass | subagent | codex review command>
```
