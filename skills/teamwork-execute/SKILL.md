---
name: teamwork-execute
description: Use when a user says go ahead, proceed, do it, implement this plan, continue, or resume an accepted plan or approved checklist.
---

# Teamwork Execute

Use this stage after a plan has been accepted, approved, resumed, or the user
asks to execute a prior Teamwork checklist. Execution implements the plan; it
does not self-declare completion.

Read shared rules only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for progress
  anchors, evidence labels, context discipline, and the Subagent Collaboration
  Model.
- `skills/using-teamwork/references/subagent-routing.md` for Worker dispatch
  and Codex routing constraints.
- `skills/using-teamwork/references/goal-iteration.md` when a failed goal
  attempt may require research or plan revision.

## Preconditions

- Accepted lightweight plan or durable artifact plan.
- Durable plan path is required for goal-mode, cross-agent, cross-turn,
  high-risk, ambiguous, or explicitly artifact-backed work.
- If a durable artifact exists, re-read it before editing and treat it as the
  execution source of truth.
- Workspace status is understood enough to avoid overwriting other work.
- Required files, commands, credentials, and environments are available.
- Classify command safety: read-only, workspace-writing, networked,
  destructive, or outside sandbox. Follow active sandbox approvals.

If a precondition is missing, stop and report a blocker.

## Worker Boundary

Workers execute the accepted plan. They do not reopen product behavior,
architecture, requirements, or scope during execution. If new evidence changes
those decisions, stop and route back to `teamwork-research` or
`teamwork-plan`.

Delegated Worker prompts must include plan source, file ownership, allowed
edits, verification, model tier when relevant, context strategy, and no scope
expansion. Writing Workers need disjoint files or worktree isolation. For
artifact-backed work, include the durable plan path.

For non-lightweight execution, dispatch parallel Worker subagents by default
when the plan names independent tracks with disjoint file ownership. Dispatch
early, keep the main thread on orchestration/integration, and wait only when
merge or verification depends on the result. If no useful parallel Worker track
exists, preserve the plan's main-agent continuity rationale.

## Codex Routing Checks

Before delegated dispatch, validate native fields against route policy:

- Do not combine `fork_context:true` with `agent_type`, `model`, or
  `reasoning_effort`; full-history forks inherit the parent type, model, and
  effort.
- Do not use nonexistent Codex agent types such as `judge`, `reviewer`, or
  `designer`. Use the default native type and state the conceptual role in the
  prompt.
- Do not claim `high reasoning` when a full-history fork would inherit lower
  effort. Use an explicit non-inheriting dispatch when high reasoning is needed.

## Execution Steps

1. Re-read the accepted plan and relevant source files.
2. State the files you intend to touch.
3. Make only planned edits, matching existing style.
4. Keep changes minimal and producer-side.
5. Remove only code made unused by your own edit.
6. If new evidence invalidates the plan, stop and report the mismatch.

## Verification

- Run the focused verification from the plan first.
- Add broader checks only when the plan calls for them or the edit affects
  shared/public behavior.
- Verification must cite real command output, artifact properties, inspected
  diff evidence, or test results.
- If verification fails, classify it as fixed, improved, unchanged, regressed,
  new, unrelated, or blocked.

## Failure Handling

- Plan mismatch: stop and request replanning.
- Failure caused by your edit: rework only the causal change.
- Unrelated failure: record evidence and avoid masking it.
- Goal mode failure: return to the Research + Plan Adequacy Gate instead of
  blind retry.
- Sacred-boundary conflict, destructive risk, missing credentials, or budget
  exhaustion: stop and report a blocker.

## Handoff To Review

```text
Implemented:
- <path>: <change and plan step>

Plan Source:
- <lightweight accepted plan | docs/teamwork/plans/YYYY-MM-DD-<slug>.md>

Verification:
- <command/check>: <result>

Deviations:
- <none or exact deviation and why it was necessary>

Failures / Blockers:
- <none or evidence>

Review Request:
- Validate diff, artifacts, tests, regressions, and acceptance criteria.
```
