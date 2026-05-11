---
name: run-analyze-plan
description: >-
  Use to turn a selected run-analyze-optimize direction into an executable,
  minimal implementation plan with scope, boundaries, verification, risks, and
  handoff details.
disable-model-invocation: true
---

# Run-Analyze Plan

Use this subskill after research or diagnosis has selected a direction. The
output is a plan that a worker can execute without expanding scope.

## Inputs

- Goal or root cause to address.
- Accepted direction and rejected alternatives, if any.
- Sacred boundaries: files, APIs, architecture, behavior, data, or claims that
  must not change.
- Mutable scope: exact implementation areas that may change.
- Verification target: command, artifact, metric, or acceptance criteria.
- Budget and stop rules.

Make assumptions explicit. If the goal or boundary is ambiguous in a way that
changes behavior, stop and ask rather than planning around a guess.

## Planning Workflow

1. Restate the root cause or goal in one sentence.
2. Define scope: in scope, out of scope, and sacred boundaries.
3. Identify the smallest producer-side change that can satisfy the goal.
4. Break work into ordered, executable steps with exact paths when known.
5. Design focused verification first; add broader checks only when shared
   behavior, public contracts, or user-visible workflows are affected.
6. List risks, rollback/rework strategy, and what evidence would invalidate the
   plan.
7. Prepare a handoff that separates worker tasks from reviewer checks.

## Plan Quality Gates

- Simplicity first: no abstraction or refactor unless required by the root
  cause.
- Surgical edits: every planned file must trace to the goal.
- Evidence-driven: the plan must identify what will prove success.
- Boundary-safe: no step changes protected contracts or principles.
- Budget-aware: include stop conditions for no progress, blocker, or exceeded
  budget.

## Handoff Format

```text
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
```
