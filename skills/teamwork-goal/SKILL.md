---
name: teamwork-goal
description: Use when the user asks to keep going, run until it passes, fix until green, iterate until done, converge on a verifiable target, or work within an explicit budget.
---

# Teamwork Goal

Use when the user wants autonomous progress to verified success, budget
exhaustion, repeated no-progress, or a hard blocker. Ordinary one-shot work uses
the narrower stage.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and judgment; `skills/using-teamwork/references/goal-iteration.md` for
the Goal Proposal, controller loop, adequacy gate, and rolling report;
`skills/using-teamwork/references/subagent-dispatch.md` for stage dispatch;
`skills/using-teamwork/references/debug-mode.md` for runtime failure diagnosis;
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

1. Initialize target, Goal Invariants, assumptions, boundaries, verification,
   budget, and a durable plan/report when needed.
2. Retrieve prior research/report rows before repeating a hypothesis. After any
   failed, partial, blocked, or no-progress attempt, run Replay Preflight before
   refreshing the plan or dispatching more work.
3. Research broad unknowns; route reproducible unknown-cause failures through
   `teamwork-debug`; plan through `teamwork-plan`; execute through
   `teamwork-execute`, dispatching subagents when ownership splits.
4. Verify, then review through `teamwork-review`. Each attempt records
   delegated packets or blockers before acceptance or retry.
5. Append an Attempt Record after each verify/review cycle. For failed,
   partial, blocked, or no-progress attempts, add a Failure Reflection before
   entering the Research + Plan Adequacy Gate.
6. Accept only when verification and execution review pass; otherwise revise
   from the replayed evidence and Goal Invariants.

## Stop Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive no-progress iterations unless a fresh strategy delta
  is evidence-backed. Same failure plus no strategy delta counts as no-progress.
- Failed debug attempts return to the Research + Plan Adequacy Gate before
  another fix attempt.
- Stop immediately on destructive risk, auth failure, missing required
  resources, protected-boundary conflict, or user-intent ambiguity.
- Mark complete only after focused verification and execution review pass: Codex
  native goal complete, or Cursor / Claude Code rolling report `Status: accepted`.

## Output

Use `goal-iteration.md` for the attempt table and report format. Include
`Memory Delta:` when durable project memory was checked or changed.
