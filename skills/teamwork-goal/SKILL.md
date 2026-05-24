---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget.
---

# Teamwork Goal

Use this stage for `mode: goal` when the user wants autonomous progress to
verified success, budget exhaustion, repeated no-progress, or a hard blocker.
Ordinary one-shot research, planning, execution, or review should use the
narrower Teamwork stage.

Native Codex goal state is the source of truth for the autonomous target and
lifecycle. Teamwork-goal strengthens that native goal with human-reviewed goal
design, direct evidence, durable memory when needed, plan adequacy checks,
focused verification, and execution review.

## Goal Proposal Before Native Goal

If the user asks for autonomous convergence but the objective, verification,
scope, or stop rules are not already crisp, first return a chat-only `Goal
Proposal` and wait for human approval or edits before creating or rewriting
native Codex goal state with `create_goal`.

Skip the proposal only when an active native goal already exists or the user has
already supplied a complete goal with objective, context/constraints, and done
evidence.

Use this two-layer shape:

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, sacred boundaries>
- Iteration Budget: <default 3 if unspecified, or user-specified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested research/plan/report paths and why>
- Subagent Routing: <tracks to split, or why main-agent continuity is better>
- Native Codex Goal Text: <concise target prepared for create_goal>
```

The proposal is not a durable plan artifact, not `update_plan`, and not a
completion claim. It is a human-review gate that designs the native Codex goal
before autonomous work starts. After approval, call `create_goal` with the
`Native Codex Goal Text`.

Read shared references only as needed:

- `skills/teamwork/references/workflow-contract.md` for evidence, context,
  progress anchors, and subagent collaboration.
- `skills/teamwork/references/goal-iteration.md` for the goal input contract,
  Research + Plan Adequacy Gate, and rolling report table.
- `skills/teamwork/references/artifact-protocol.md` for artifact retrieval and
  hygiene.

## Inputs

- Objective, deliverable, failing command, or artifact target.
- Verification evidence that proves success. Recommended shape: achieve
  `<target>`, accept only with `<verifiable evidence>`, preserve
  `<constraints>`, restrict scope to `<files/tools/boundaries>`, and choose the
  next iteration from `<decision rule>`.
- Budget, stop rules, allowed tools/files, sacred boundaries, and mutable scope.
- Existing native Codex goal state, plan artifact, research artifact, or report
  artifact if present.

Ask the user only for destructive risk, auth/credentials, missing required
external resources, sacred-boundary conflict, or ambiguity that changes public
behavior, protected contracts, architecture, or user intent.

## Durable Memory Requirement

For non-lightweight, cross-turn, failed-iteration, cross-agent, high-risk, or
artifact-backed goal work, use durable memory:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

The durable plan is the shared execution and review source of truth. Do not
infer it from newest files, chat history, `update_plan`, or summaries. If the
plan changes, update the artifact and repeat plan review before execution.

Goal-mode durable plans should include: Goal, Requirements Mapping, Evidence
Read, Scope, Implementation Steps, Verification, Risks, Stop Rules, Worker
Handoff, Review Handoff, and Subagent Routing.

## Controller Loop

1. Initialize objective, assumptions, boundaries, verification target, budget,
   active native goal, durable plan, and report when applicable.
2. Retrieve prior research and report rows before repeating a hypothesis.
3. Research or refresh research when causes/options are unclear, external
   assumptions matter, or a focused attempt has no evidence delta.
4. Plan through `teamwork-plan`; create or update durable memory when required.
5. Review the plan with `teamwork-review` mode: plan.
6. Execute the accepted plan through `teamwork-execute`.
7. Verify with focused evidence first.
8. Review execution with `teamwork-review` mode: execution.
9. Append the rolling report row when a report artifact is required.
10. Accept only when verification passes and execution review passes. Otherwise
    enter the Research + Plan Adequacy Gate.

## Research + Plan Adequacy Gate

Enter this gate after failed verification, `revise`/`blocked` review,
acceptance uncertainty, `no-progress`, or plan mismatch. Read failed
verification, current plan, execution review, rolling report, and relevant
research. Decide whether the issue is research gap, plan insufficiency, wrong
scope, over-strict stop rule, implementation deviation, or true blocker.
Refresh research, revise or replace the durable plan, and repeat plan review
when new evidence changes the path.

## Completion Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive `no-progress` iterations.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing required resources, or public-contract/user-intent ambiguity.
- A rolling report is memory, not completion proof.
- Mark the native Codex goal complete only after focused verification and
  execution review pass.
- Completion evidence must map each requirement or acceptance criterion to
  concrete commands, paths, artifacts, diffs, or inspected behavior.

## Output

```text
Route: teamwork-goal
Reason: <one sentence tied to autonomous convergence>
Mode: goal

Goal Proposal:
- <only when proposal is needed>

Native Codex Goal:
- proposed | created | continued | completed | not used
- Native Codex Goal Text: <approved text or none>

Active Plan Artifact:
- docs/teamwork/plans/YYYY-MM-DD-<slug>.md | none

Rolling Report:
- docs/teamwork/reports/YYYY-MM-DD-<slug>.md | none

Iterations:
- <n>: research/plan/execute/review summary

Verification:
- <command/artifact/check>: <result>

Review:
- Plan review: <verdict>
- Execution review: <verdict and dissent>

Completion Evidence:
- <requirement-to-evidence map with paths/commands/artifacts>

Unresolved:
- <none or blockers>

Conclusion:
- accept | blocked | budget exhausted | stopped
```
