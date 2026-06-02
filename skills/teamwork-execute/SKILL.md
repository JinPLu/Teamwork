---
name: teamwork-execute
description: Use when a user says go ahead, proceed, do it, implement this plan, continue, or resume an accepted plan or approved checklist.
---

# Teamwork Execute

Use after a plan is accepted, approved, resumed, or continued. Execution
implements the plan; it does not self-declare completion.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence, progress anchors, boundaries.
- `skills/using-teamwork/references/dispatch-policy.md` for Worker split and
  platform mapping.
- `skills/using-teamwork/references/subagent-prompt-contract.md` before Worker prompts.
- `skills/using-teamwork/references/subagent-packets.md` for Worker Completion Packet and Actual
  Dispatch Log.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal attempts.
- `skills/using-teamwork/references/artifact-protocol.md` when execution needs
  durable memory or current-state lookup.

## Preconditions

- Accepted lightweight or durable plan.
- Durable plan path for goal-mode, cross-turn, high-risk, ambiguous, long
  delegation, complex Worker fan-out, or artifact-backed work.
- Re-read durable artifacts before editing.
- Workspace status is understood enough to avoid overwriting other work.
- Required files, commands, credentials, and environments are available.
- Classify command safety, sandbox boundaries, and active approvals.

If a precondition is missing, stop and report a blocker.

## Worker Boundary

Workers execute the accepted plan. They do not reopen behavior, architecture,
requirements, or scope. If evidence changes those decisions, stop and route
back to research or plan.

For non-lightweight execution, re-run the Worker split from accepted steps,
files, components, and ownership. Dispatch parallel Worker subagents when
tracks are independent and pass Dispatch Economics by default, even if the
plan did not name every Worker. Apply the Subagent Tool Discovery Gate before
claiming needed subagents are unavailable. Before dispatching more than 3 Workers, state
ownership map, integration order, verification plan, and why parallel beats
serial.

Worker prompts follow the Subagent Prompt Contract, use disjoint ownership or
worktree isolation, and require Worker Completion Packet.

## Execution Steps

1. Re-read plan and relevant source.
2. Dispatch Workers for independent tracks or emit `Dispatch Exception:` with
   continuity rationale; start Actual Dispatch Log when subagents run.
3. State files you or Workers intend to touch.
4. Make only planned, minimal, producer-side edits.
5. Integrate Worker Completion Packets before final verification.
6. Mark each delegated track `closed`, `blocked`, or
   `abandoned-after-discovery` with Closure Evidence after integration.
7. Stop if new evidence invalidates the plan.

## Verification And Failure

Run focused verification first. Add broader checks only when planned or
shared/public behavior changes. Cite command output, artifacts, diffs, or test
results.

Classify failures as fixed, improved, unchanged, regressed, new, unrelated, or
blocked. Goal-mode failure returns to the Research + Plan Adequacy Gate.
Destructive risk, auth failure, sacred-boundary conflict, missing credentials,
or budget exhaustion is a blocker.

## Handoff To Review

Return implemented paths, plan source, verification, Actual Dispatch Log or
continuity rationale, deviations, failures/blockers, and review request.
Execution cannot accept its own work. For non-lightweight work, request a
fresh-context Reviewer subagent before any completion claim; if subagents are
unavailable after discovery or the user forbids them, report that acceptance is
unreviewed. Do not claim completion while any delegated track is still open.
Include `Memory Delta:` only when durable project memory was checked or changed.
