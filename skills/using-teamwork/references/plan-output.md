# Plan Output

## Lightweight Plan

For small-to-medium clear work, state in chat:

```text
Goal: <one sentence>
Scope: <paths/components in and out>
Steps: <short ordered bullets, or a table when 3+ comparable steps>
Verification: <focused command/check and expected result>
Stop: <condition that triggers ask/replan>
```

Add Dispatch Guidance or Review Need only when dispatch or review materially affects execution. Use a compact step table when three or more comparable steps exist.

## Durable Plan Contract

Durable plans are reviewable specs before edits and executable runbooks after
acceptance. Favor tables and diagrams over prose when they make state, gates, or
handoffs easier to audit. Write `none` with rationale instead of leaving a
section ambiguous.

## Durable Plan Header

```text
Artifact Type: plan
Status: active | superseded | accepted | blocked
Last Updated: YYYY-MM-DD
Search Keys: <errors, commands, paths, components, model/API names, issue/PR IDs>
Abstract: 2-4 sentences covering goal, selected direction, and applicability boundary.
Linked Artifacts: <related research or report paths, or none>
```

## Durable Plan Sections

Use this order unless the task has a stronger local convention:

1. `# <Goal> Plan` and the header above.
2. `## 0. Current State` table:
   `Item | Evidence / Current Conclusion`.
3. `## 1. Flow` Mermaid `flowchart` for multi-stage, branching, delegated, or
   goal-mode work.
4. `## 2. Scope And Requirements` table:
   `Requirement | Evidence | Planned Handling | Verification`.
5. `## 3. Execution Table`:
   `Phase | Owner | Input | Output | Verification | Stop / Replan`.
6. `## 4. Artifacts / Interfaces`:
   `Artifact or File | Purpose | Required Contents / Contract`.
7. `## 5. Gates`:
   `Gate | Go Condition | Stop Condition`.
8. `## 6. Dispatch / Goal Surface`:
   `Track | Owner | Native Fields | Owned Scope | Packet / Closure`.
9. `## 7. Acceptance Checklist`:
   `Check | Required Evidence | Strength`.
10. `## 8. Next Actions` numbered list.

## Goal-Mode Additions

In `Dispatch / Goal Surface`, name the control plane: Codex native goal, or
Cursor/Claude rolling report. Include budget, success signal, no-progress stop,
retry/research trigger, and acceptance review. The plan is not the goal state;
it is the current runnable approach.

For bug/failure plans, state the route: `research -> plan -> execute`,
`debug -> plan -> execute`, or `debug -> execute`. Include repro path,
hypotheses, instrumentation, runtime evidence, cleanup, and review acceptance
when debug is part of the route.

## Handoff Rules

- Worker: execute only the accepted rows; no adjacent cleanup.
- Reviewer/Judge: check evidence adequacy, scope, gates, verification, and
  acceptance criteria.
- Actual Dispatch Log records review-relevant roles, native fields, prompt
  packets, returned packets, final status, closure evidence.

Goal-mode plans include every section. Ordinary durable plans stay concise but
preserve current state, scope, execution, verification strength, gates, risks,
stop rules, and routing rationale.
