---
name: teamwork-execute
description: Use when an accepted Teamwork plan is ready for bounded implementation and focused verification.
---

# Teamwork Execute

Use this stage only after a plan has been accepted. Execution implements the
plan; it does not self-declare completion.

Read shared rules only as needed:

- `skills/teamwork/references/workflow-contract.md` for progress anchors,
  evidence labels, context discipline, and the Subagent Collaboration Model.
- `skills/teamwork/references/subagent-routing.md` for Worker dispatch and
  Codex routing constraints.
- `skills/teamwork/references/goal-iteration.md` when a failed goal attempt
  may require research or plan revision.

## Preconditions

- Accepted lightweight plan or durable artifact plan.
- A durable Markdown plan artifact path is required for goal-mode, cross-agent,
  cross-turn, high-risk, ambiguous, or explicitly artifact-backed work.
- If a durable artifact exists, re-read it before editing and treat it as the
  execution source of truth.
- Workspace status is understood enough to avoid overwriting other work.
- Required files, commands, credentials, and environments are available, or the
  missing item is reported as a blocker.
- Command safety is classified before execution: read-only, workspace-writing,
  networked, destructive, or outside sandbox. Follow the active sandbox and
  approval model; do not bypass it.

If a precondition is missing, stop and report a blocker.

## Worker Boundary

Workers execute the accepted plan. They do not reopen product behavior,
architecture, requirements, or scope during execution. If new evidence changes
those decisions, stop and route back to `teamwork-research` or
`teamwork-plan`.

Delegated Worker prompts must include the plan source, exact file ownership,
allowed edits, verification expectation, model tier when relevant, context
strategy, and the instruction not to expand scope. Writing Workers need
disjoint file ownership or worktree isolation. For artifact-backed work, include
the durable Markdown plan artifact path.

For non-lightweight execution, prefer parallel Worker subagents when the plan
names independent tracks with disjoint file ownership. Dispatch early, keep the
main thread on orchestration/integration, and wait only when the next merge or
verification step depends on the result. If no useful parallel Worker track
exists, preserve the plan's main-agent continuity rationale.

## Codex Routing Checks

Before delegated dispatch, validate native fields against the router:

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
