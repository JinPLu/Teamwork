# Plan Output

Use this reference when `teamwork-plan` creates a durable artifact or when a
lightweight plan needs a complete handoff. Keep chat plans compact; use the full
shape only when durable or goal-mode work requires it.

## Lightweight Plan

Use bullets for very small plans:

```text
Goal: <one sentence>
Scope: <paths/components in and out>
Steps: <short ordered bullets>
Verification: <focused command/check and expected result>
Stop: <condition that triggers ask/replan>
```

Add Dispatch Guidance, Review Need, or Design/Judge only when dispatch, review,
or design decisions materially affect execution. When a plan has three or more
comparable steps, prefer a compact table so humans can audit scope, owner,
verification, and stop conditions quickly.

```text
Mode: plan
Research Artifact: <path | none>
Plan Tier: lightweight
Goal: <one sentence>
Clarification Gate: pass | assumptions-stated | blocked-for-clarification
Scope: In <...>; Out <...>; Protected <...>
Dispatch Guidance: optional; include none with rationale only when material dispatch is skipped, or name Explorer/Designer/Judge/Worker/Reviewer tracks, ownership, context strategy, cap/batch reason, and Deep Judge/Reviewer severity when warranted
Steps:
- [ ] <path/component> - <minimal change> - <why>
Verification:
- Focused: <command/artifact/check>
- Broader: <command/check or not needed because ...>
- Expected Results: <exact passing output or behavior>
Stop Rules: <when to stop or replan>
Review Need: <optional; none | local | fresh-context>
Design/Judge: <optional; Designer/Judge packet summary when used>
```

Optional chat-table shape:

| Step | Scope | Owner | Verification | Stop / Replan |
|---|---|---|---|---|
| <n> | <path/component> | <main/role> | <command/check> | <condition> |

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
## Clarification Gate
- Outcome: pass | assumptions-stated | blocked-for-clarification
- Questions asked or blocker: <none | concise question/blocker>
- Non-blocking assumptions: <none | stated assumptions>
## Requirements Mapping
| Requirement | Evidence Or Verification | Status |
|---|---|---|
| <requirement> | <observed evidence or verification that will prove it> | planned |
## Evidence Read
- <observed|inferred|claimed> <path/command/artifact/research>: <finding>
## Scope
- In: ...
- Out: ...
- Protected boundaries: ...
## Designer Decision
- <optional; include Decision Scope, constraints, success criteria, option matrix, recommendation, rejected options, acceptance implications when used>
## Judge Plan Review
- <optional; include verdict, requirements/evidence adequacy, guardrails, stop conditions, acceptance gap, required fixes, residual risks when used>
## Subagent Routing
- Expected: <role, scope, model tier, context strategy, order, independence, owned paths, why; or `none` with continuity rationale>
- Execution may re-run the split and record Actual Dispatch Log.
## Subagent Prompt Packets
- <role>: <mission, source, owned scope, allowed actions, forbidden actions, escalation triggers, required output schema>
## Implementation Steps
| Step | Scope | Owner | Change | Verification | Stop / Replan |
|---|---|---|---|---|---|
| 1 | <path/component> | <main/Worker> | <minimal change> | <command/check> | <condition> |
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
- <filled during execution/review when subagents are used; role, native fields, context strategy, ownership, prompt packet, returned packet, final status, closure evidence>
```

Goal-mode durable plans must include every durable section. Ordinary durable
plans may stay concise but must preserve goal, scope, steps, verification,
risks, stop rules, handoffs, and routing rationale. Use durable Subagent
Routing for complex, cross-turn, high-risk, or long-running delegation.
`Dispatch Guidance: none` requires rationale, and routing must appear before
steps. Actual dispatch is a stage decision recorded during execution or review;
the plan is not the only authorization source.
