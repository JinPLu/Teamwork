---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget.
---

# Teamwork Goal

Use when the user wants autonomous progress to verified success, budget
exhaustion, repeated no-progress, or a hard blocker. Ordinary one-shot
research, planning, execution, or review should use the narrower stage.

Native Codex goal state is the source of truth for autonomous target and
lifecycle. Teamwork-goal adds goal design, evidence, durable memory when
needed, plan adequacy checks, focused verification, and execution review.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for shared evidence
  and context rules.
- `skills/using-teamwork/references/goal-iteration.md` for `Goal Proposal`,
  Research + Plan Adequacy Gate, output format, and rolling report table.
- `skills/using-teamwork/references/artifact-protocol.md` for durable memory.

## Goal Proposal Before Native Goal

If objective, verification, scope, or stop rules are not crisp, first return a
chat-only `Goal Proposal` and wait for approval before calling `create_goal`.
Skip only when an active native goal exists or the user already supplied a
complete target with constraints and done evidence.

The approved `Native Codex Goal Text` is what goes into native Codex goal
state. The proposal is not `update_plan`, not a durable plan, and not a
completion claim.

## Inputs

- Objective, deliverable, failing command, or artifact target.
- Verification evidence that proves success.
- Budget, stop rules, allowed files/tools, protected boundaries, and mutable
  scope.
- Existing native goal, plan artifact, research artifact, or report artifact.

Ask only for destructive risk, auth/credentials, missing required resources,
protected-boundary conflict, or ambiguity that changes public behavior,
architecture, contracts, or user intent.

## Loop

1. Initialize target, assumptions, boundaries, verification, budget, active
   native goal, durable plan, and report if needed.
2. Retrieve prior research/report rows before repeating a hypothesis.
3. Research when causes/options are unclear, external assumptions matter, or a
   focused attempt has no evidence delta.
4. Plan through `teamwork-plan`; review the plan.
5. Execute through `teamwork-execute`; verify with focused evidence.
6. Review execution through `teamwork-review`.
7. Accept only when verification and execution review pass; otherwise enter the
   Research + Plan Adequacy Gate.

## Stop Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive `no-progress` iterations.
- Stop immediately on destructive risk, auth failure, missing required
  resources, protected-boundary conflict, or user-intent ambiguity.
- Mark the native Codex goal complete only after focused verification and
  execution review pass.

## Output

Use the compact goal output in
`skills/using-teamwork/references/goal-iteration.md`.
