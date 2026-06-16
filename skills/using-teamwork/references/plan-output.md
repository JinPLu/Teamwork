# Plan Output

## Lightweight Plan

For small-to-medium clear work, state in chat:

```text
Goal: <one sentence>
Scope: <paths/components in and out>
Steps: <short ordered bullets>
Verification: <focused command/check and expected result>
Stop: <condition that triggers ask/replan>
```

Add Dispatch Guidance or Review Need only when dispatch or review materially affects execution. Use a compact step table when three or more comparable steps exist.

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

```text
# <Goal> Plan

<header above>

## Goal

## Scope
- In: ...
- Out: ...
- Protected boundaries: ...

## Evidence Read
- <observed|inferred|claimed> <source>: <finding>

## Implementation Steps
| Step | Scope | Owner | Change | Verification | Stop / Replan |
|---|---|---|---|---|---|

## Verification
- Focused: ...
- Expected Results: ...

## Risks

## Stop Rules

## Subagent Routing
- Expected: <role, scope, model tier, order, owned paths; or `none` with rationale>
- Actual Dispatch Log: <role, native fields, prompt packet, returned packet,
  final status, closure evidence>

## Handoff
- Worker: execute only the steps above; no adjacent cleanup.
- Reviewer: check scope, diff, tests, regressions, and acceptance criteria.
```

Goal-mode plans include every section. Ordinary durable plans stay concise but preserve goal, scope, steps, verification, risks, stop rules, and routing rationale.
