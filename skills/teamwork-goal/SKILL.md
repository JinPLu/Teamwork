---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget.
---

# Teamwork Goal

Use when the user wants autonomous progress to verified success, budget
exhaustion, repeated no-progress, or hard blocker. Ordinary one-shot research,
planning, execution, or review should use the narrower stage.

Platform goal surface is the source of truth for autonomous lifecycle:

- Codex: native goal state; after approval call `create_goal` with the Goal Text.
- Cursor: no native goal; initialize a rolling report as durable goal state and
  drive the controller loop from chat.
- Claude Code: no native goal; initialize a rolling report as durable goal
  state and drive the controller loop from chat, same as Cursor.

Teamwork-goal adds goal design, evidence, durable memory when needed, plan
adequacy, verification, and review.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and context rules.
- `skills/using-teamwork/references/dispatch-policy.md` for stage dispatch decisions.
- `skills/using-teamwork/references/subagent-packets.md` for attempt packets and Actual Dispatch Log.
- `skills/using-teamwork/references/goal-iteration.md` for `Goal Proposal`, Research + Plan Adequacy
  Gate, output format, and rolling report.
- `skills/using-teamwork/references/artifact-protocol.md` for durable memory.

## Goal Proposal Before Platform Goal Handoff

If objective, verification, scope, or stop rules are not crisp, return a
chat-only `Goal Proposal` and wait for approval before native goal handoff or
rolling-report initialization. Skip only when an active goal surface exists or
the user supplied a complete target.

The approved Goal Text goes into the platform goal surface: Codex `create_goal`,
or Cursor rolling-report header and Abstract. Proposal `Subagent Routing` is
initial only; `teamwork-plan` reruns the Parallelization Gate and each active
stage reruns Stage-Routed Proactive Dispatch.

## Inputs

Objective, deliverable, failing command, done evidence, budget, stop rules,
allowed tools/files, protected boundaries, mutable scope, active goal, and any
research/plan/report artifact.

Ask only for destructive risk, auth/credentials, missing required resources,
protected-boundary conflict, or ambiguity that changes public behavior,
architecture, contracts, or user intent.

## Loop

1. Initialize target, assumptions, boundaries, verification, budget, goal,
   durable plan, and report if needed.
2. Retrieve prior research/report rows before repeating a hypothesis.
3. Research unclear causes/options; use Explorer packets for independent
   tracks after the Subagent Tool Discovery Gate.
4. Plan through `teamwork-plan`; use Designer/Judge when risk warrants. Durable
   or high-risk plans remain `unreviewed` until a Judge verdict exists.
5. Execute through `teamwork-execute`; dispatch Workers when ownership splits.
6. Verify, then review through `teamwork-review`; every attempt closes or
   blocks all delegated tracks before acceptance or retry.
7. Accept only when verification and execution review pass; otherwise enter the
   Research + Plan Adequacy Gate.

## Stop Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive `no-progress` iterations.
- Stop immediately on destructive risk, auth failure, missing resources,
  protected-boundary conflict, or user-intent ambiguity.
- Mark the platform goal surface complete only after focused verification and
  execution review pass: Codex native goal complete, or Cursor / Claude Code
  rolling report `Status: accepted`.

## Output

Use `skills/using-teamwork/references/goal-iteration.md`.
Goal iterations that read or change durable project memory include
`Memory Delta:` per `skills/using-teamwork/references/artifact-protocol.md`.
