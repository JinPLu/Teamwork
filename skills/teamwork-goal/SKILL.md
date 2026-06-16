---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget.
---

# Teamwork Goal

Use when the user wants autonomous progress to verified success, budget
exhaustion, repeated no-progress, or a hard blocker. Ordinary one-shot work uses
the narrower stage.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and judgment; `skills/using-teamwork/references/goal-iteration.md` for
the Goal Proposal, controller loop, adequacy gate, and rolling report;
`skills/using-teamwork/references/subagent-dispatch.md` for stage dispatch;
`skills/using-teamwork/references/artifact-protocol.md` for durable memory.

## Goal Surface

- **Codex:** native goal state; after approval call `create_goal` with the Goal
  Text.
- **Cursor / Claude Code:** no native goal; initialize a rolling report under
  `docs/teamwork/reports/` as durable goal state and drive the loop from chat.

## Propose First

If objective, verification, scope, or stop rules are not crisp, return a
chat-only `Goal Proposal` and wait for approval before goal handoff or
rolling-report init. Skip only when an active goal surface exists or the user
supplied a complete target. The approved Goal Text goes into the goal surface.

## Loop

1. Initialize target, assumptions, boundaries, verification, budget, and a
   durable plan/report when needed.
2. Retrieve prior research/report rows before repeating a hypothesis.
3. Research unclear causes; plan through `teamwork-plan`; execute through
   `teamwork-execute`, dispatching subagents when ownership splits.
4. Verify, then review through `teamwork-review`. Each attempt closes or blocks
   every delegated track before acceptance or retry.
5. Accept only when verification and execution review pass; otherwise enter the
   Research + Plan Adequacy Gate and revise.

## Stop Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive no-progress iterations.
- Stop immediately on destructive risk, auth failure, missing required
  resources, protected-boundary conflict, or user-intent ambiguity.
- Mark complete only after focused verification and execution review pass: Codex
  native goal complete, or Cursor / Claude Code rolling report `Status: accepted`.

## Output

Use `goal-iteration.md` for the attempt table and report format. Include
`Memory Delta:` when durable project memory was checked or changed.
