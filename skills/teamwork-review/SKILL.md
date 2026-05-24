---
name: teamwork-review
description: Use when a Teamwork plan or implementation needs an independent evidence-based review before execution or completion.
---

# Teamwork Review

Use this stage for a distinct reviewer pass when review adds value. The
reviewer reads direct evidence and preserves dissent. Do not rely only on a
planner, executor, tool, or previous reviewer summary.

Read shared rules only as needed:

- `skills/teamwork/references/workflow-contract.md` for the Evidence
  Interpretation Contract, context discipline, progress anchors, and subagent
  collaboration.
- `skills/teamwork/references/subagent-routing.md` for routing conformance.
- `skills/teamwork/references/goal-iteration.md` for goal-mode failure routing.

## Shared Rules

- Choose one mode explicitly: mode: plan or mode: execution.
- Prefer fresh-context review for non-trivial execution. If no separate
  subagent is practical, run a distinct local review pass and say it was local.
- Read primary evidence: source, diffs, logs, artifacts, tests, command output,
  research, plan artifacts, and user constraints as relevant.
- Separate `observed`, `inferred`, and `claimed` evidence. Names, comments,
  README prose, version labels, historical notes, and summaries are claims until
  corroborated.
- Treat executor summaries, `codex review`, CI summaries, and other tool output
  as evidence inputs, never as the final verdict by themselves.
- For git repositories, inspect the diff directly. `codex review
  --uncommitted`, `codex review --base <branch>`, or `codex review --commit
  <sha>` may be supporting evidence, not automatic approval.
- Preserve dissent and uncertainty even when the verdict passes.
- Do not fix issues during review unless explicitly asked.

## mode: plan

Review whether the plan is safe to execute.

Check:

- Plan source: lightweight plans may be chat/native checklists; durable-required
  plans must have a readable Markdown artifact under
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- Scope: every step traces to the goal.
- Assumptions: missing inputs are explicit and safe.
- Requirements-to-evidence mapping: each requirement or acceptance criterion
  maps to observed evidence or verification that will prove it.
- Research grounding: external behavior, upstream bugs, current APIs, or
  ambiguous architecture claims cite readable research or explain why local
  evidence is enough.
- Verification design: focused checks, broader checks when warranted, and
  Expected Results are present.
- Risk, stop rules, worker handoff, and review handoff are adequate.
- Subagent Routing: If subagents are used, the plan records role, task scope,
  model tier, context strategy, order, independence, and why. It should identify
  independent tracks or explain main-agent continuity. High-risk plan or
  execution review should not use a low-capability tier.

Hard gates:

- For durable-required work, a missing or unreadable artifact must return
  `revise` or `blocked`. Lightweight work does not need a repository artifact
  unless scope, steps, verification, Expected Results, or stop condition are
  unclear.
- Plans with placeholders, ellipsis tasks, vague testing, missing
  requirements-to-evidence mapping, missing verification design, missing
  Expected Results, or missing durable handoffs must return `revise` or
  `blocked`.
- If subagents are used, misleading or incomplete routing must return `revise`
  or `blocked`; if skipped for durable/delegated/high-risk/goal-mode work, the
  continuity rationale must be present.
- A plan that explicitly includes native dispatch fields and combines
  `fork_context:true` with `agent_type`, `model`, or `reasoning_effort`, uses
  nonexistent native agent types, or claims inherited lower-effort routing as
  high reasoning must return `revise` or `blocked`.
- Protected contracts, architecture, or public behavior changes outside stated
  scope must return `blocked`.

## mode: execution

Review implementation before any high-risk, artifact-backed, or goal-mode
completion claim.

Check:

- Diff: only planned files and necessary lines changed.
- Artifacts: expected files, outputs, metrics, or UI state match acceptance.
- Tests: focused verification ran; broader validation exists when warranted.
- Regressions: contracts, hidden behavior changes, brittle assumptions, and
  cleanup masking producer bugs.
- Plan conformance: compare diff and verification to the durable artifact or
  accepted lightweight plan.
- Routing conformance: when subagents were used, compare actual roles, model
  tier, context strategy, order, and file ownership to accepted routing.
- Parallel execution fit: for non-lightweight work, check whether useful
  disjoint Worker tracks were used or skipped with rationale.
- Codex dispatch validity: reject full-history fork plus override fields,
  nonexistent native agent types, and inherited lower-effort routing claimed as
  high reasoning.
- Workspace hygiene: no unrelated edits, generated churn, or overwritten work.
- Narrative-mislead risk: verify version names, stale docs, comments, or
  historical explanations did not steer execution to the wrong path or early
  completion.
- Goal failure routing: if work cannot be accepted, state whether the next
  action is research refresh, plan revision, implementation correction, or true
  blocker.

## Verdict Format

```text
Mode:
- plan | execution

Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>

Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>

Dissent / Uncertainty:
- <preserved concern or none>

Verdict:
- pass | pass-with-notes | revise | blocked

Rationale:
- <brief evidence-based reason>
```
