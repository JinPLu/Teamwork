---
name: teamwork-execute
description: Use when implementing an accepted plan — keeps execution bounded to planned steps, prevents scope creep during coding, and ensures focused verification runs before claiming completion.
---

# Teamwork Execute

Use this subskill only after a plan has been accepted. The executor implements
the plan; it does not self-declare completion.

For goal-mode failure recovery, read
`skills/teamwork/references/goal-iteration.md` before turning a failed
verification into another attempt.
For parallel Worker dispatch and Codex routing constraints, read
`skills/teamwork/references/subagent-routing.md`.

## Preconditions

- Accepted lightweight plan or durable artifact plan. A durable Markdown plan
  artifact path is required for goal mode, cross-agent execution, cross-turn
  work, high-risk or ambiguous changes, and any plan that explicitly created an
  artifact. For bounded low-risk work, the accepted chat/native checklist is an
  acceptable execution source.
- When a durable Markdown plan artifact path is required, it must be provided
  and readable before execution begins.
- If a durable artifact path is provided, re-read it before editing and treat it
  as the execution source of truth. Do not infer the active plan from the newest
  file, chat history, or summaries.
- Current workspace status is understood enough to avoid overwriting others.
- Required files, commands, credentials, and environments are available or the
  absence is recorded as a blocker.
- Before running commands, classify whether they are read-only,
  workspace-writing, networked, destructive, or outside the sandbox. Use normal
  execution for safe local commands. If sandboxing blocks a required command,
  request escalation with a concise justification and, when appropriate, a
  narrow reusable prefix rule. Never use `danger-full-access` or bypass
  approvals as part of this skill.

If any precondition is missing, stop and return a blocker instead of guessing.

## Worker Pass

Workers execute the accepted plan. They do not reopen product behavior,
architecture, or requirements design during execution. If execution uncovers
unsettled requirements, architecture, public behavior, or cross-module design
choices, or external evidence gaps, stop and return to `teamwork-research` or
`teamwork-plan` instead of expanding scope.

Delegated Worker prompts must include the accepted plan source, exact file
ownership, allowed modification range, Teamwork model tier when relevant,
context strategy, verification expectation, and a reminder not to expand scope.
Writing Workers must have disjoint file ownership or worktree isolation. For
artifact-backed work, include the durable plan artifact path. Codex native
dispatch fields are derived from the router mapping unless a non-default native
override is itself part of the handoff.

For non-lightweight execution, prefer parallel Worker subagents when the plan
names independent tracks with disjoint file ownership. Dispatch those Workers
early, keep the main thread on orchestration and integration, and wait only when
the next merge or verification step depends on their results. If the plan does
not identify useful parallel tracks, keep execution local and preserve the plan
skip rationale.

In Codex, check native fields immediately before delegated dispatch and reject
illegal or misleading routing:

- Do not combine `fork_context:true` with `agent_type`, `model`, or
  `reasoning_effort`; full-history forks inherit the parent type, model, and
  effort.
- Do not use nonexistent Codex agent types such as `judge`, `reviewer`, or
  `designer`. Use `agent_type:"default"` and state the conceptual Teamwork role
  in the prompt for Designer, Judge, and Reviewer passes.
- Do not claim `high reasoning` routing when the agent is a full-history fork
  from a lower-effort parent. Use `fork_context:false` or omit `fork_context`
  with `reasoning_effort:"high"` when explicit high reasoning is required.

1. Re-read the accepted plan source and relevant source files. For durable
   plans, also re-read the artifact and Subagent Routing when present.
2. State the files you intend to touch.
3. Make only the planned edits, matching existing style.
4. Keep changes minimal and producer-side. Avoid unrelated cleanup, formatting,
   renames, abstractions, or behavior changes.
5. Remove only code made unused by your own edit.
6. If new evidence invalidates the plan, stop and report the mismatch; do not
   expand scope silently.

## Verification

- Run the focused verification from the plan first.
- Add broader verification only when the plan calls for it or the edit touches
  shared/public behavior.
- Verification must cite real command output, artifact properties, or inspected
  diff evidence.
- If verification fails, compare against prior evidence and report whether the
  result is fixed, improved, unchanged, regressed, or new.

## Failure Handling

- On a plan mismatch: stop and request replanning.
- On a test failure caused by your edit: rework only the causal change.
- On unrelated failures: record them with evidence and avoid masking them.
- In goal mode, failed verification, plan mismatch, or acceptance uncertainty
  returns to the Research + Plan Adequacy Gate instead of blind retry.
- On sacred-boundary conflict, destructive risk, missing credentials, or budget
  exhaustion: stop and report a blocker.

## Handoff to Review

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
