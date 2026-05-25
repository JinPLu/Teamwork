# Plan Output

Use this reference when `teamwork-plan` creates a durable artifact or when a
lightweight plan needs a complete handoff. Keep chat plans compact; use the full
shape only when durable or goal-mode work requires it.

## Lightweight Plan

```text
Mode: plan
Research Artifact: <path | none>
Plan Tier: lightweight
Goal: <one sentence>
Scope: In <...>; Out <...>; Protected <...>
Dispatch Guidance: none with rationale | Explorer/Designer/Judge/Worker/Reviewer tracks, ownership, context strategy, cap/batch reason
Steps:
- [ ] <path/component> - <minimal change> - <why>
Verification:
- Focused: <command/artifact/check>
- Broader: <command/check or not needed because ...>
- Expected Results: <exact passing output or behavior>
Stop Rules: <when to stop or replan>
Review Need: <none | local | fresh-context>
```

## Durable Plan Header

```text
Artifact Type: plan
Status: active | superseded | accepted | blocked
Last Updated: YYYY-MM-DD
Search Keys: exact errors, commands, paths, components, dependencies, model/API names, issue/PR IDs, user terms
Abstract: 2-4 sentences covering the goal, selected direction, and applicability boundary.
Linked Artifacts: related research or report paths, or none
```

## Durable Plan Sections

```text
# <Goal> Plan

<header above>

## Goal
## Requirements Mapping
- <requirement>: <observed evidence or verification that will prove it>
## Evidence Read
- <observed|inferred|claimed> <path/command/artifact/research>: <finding>
## Scope
- In: ...
- Out: ...
- Protected boundaries: ...
## Subagent Routing
- Expected: <role, scope, model tier, context strategy, order, independence, owned paths, why; or `none` with continuity rationale>
- Execution may re-run the split and record Actual Dispatch Log.
## Subagent Prompt Packets
- <role>: <mission, source, owned scope, allowed actions, forbidden actions, escalation triggers, required output schema>
## Implementation Steps
- [ ] 1. <path/component> - <minimal change> - <why>
## Verification
- Focused: ...
- Broader: ...
- Expected Results: ...
## Risks
## Stop Rules
## Worker Handoff
- Execute only the steps above. Do not add adjacent cleanup.
## Review Handoff
- Check scope, diff, tests/artifacts, regressions, and acceptance criteria.
## Actual Dispatch Log
- <filled during execution/review when subagents are used; role, native fields, context strategy, ownership, prompt packet, returned packet, status>
```

Goal-mode durable plans must include every durable section. Ordinary durable
plans may stay concise but must preserve goal, scope, steps, verification,
risks, stop rules, handoffs, and routing rationale. Use durable Subagent
Routing for complex, cross-turn, high-risk, or long-running delegation.
`Dispatch Guidance: none` requires rationale, and routing must appear before
steps. Actual dispatch is a stage decision recorded during execution or review;
the plan is not the only authorization source.
