---
name: teamwork-review
description: Use when reviewing a proposed plan before execution, or reviewing completed implementation before claiming it is done — invoke for high-risk, multi-file, artifact-backed, or goal-mode work even when you wrote the plan yourself.
---

# Teamwork Review

Use this subskill for a distinct reviewer pass when review adds value. The
reviewer reads evidence independently and preserves dissent. Do not rely only on
the planner's or executor's summary.

## Shared Review Rules

- Choose one mode explicitly: mode: plan or mode: execution.
- Start from a fresh-context reading of the review target. Do not rely only on
  planner, executor, tool, or previous reviewer summaries.
- Read primary evidence: source, diffs, logs, artifacts, tests, command output,
  and user constraints as relevant.
- Separate `observed`, `inferred`, and `claimed` evidence. File names,
  directory names, `v2`, `latest`, comments, README prose, historical notes,
  and summaries are claims until corroborated.
- Cross-check important judgments against at least one direct evidence category:
  source call path, test behavior, configuration, command output, artifact
  properties, or git diff.
- Check against the goal, sacred boundaries, budget, and stop rules.
- Preserve dissent and uncertainty, even when the final verdict is pass.
- Do not fix issues during review unless explicitly asked; report findings.
- For execution review in a git repository, inspect the diff directly. When a
  separate native review is useful, `codex review --uncommitted`,
  `codex review --base <branch>`, or `codex review --commit <sha>` may be used
  as review evidence. Treat that output as evidence, not as an automatic pass,
  and preserve any dissent from direct inspection.
- Treat executor summaries, `codex review`, CI summaries, and other tool output
  as evidence inputs, never as the final verdict by themselves.
- For non-trivial execution in Codex, prefer fresh-context review when
  available. If no separate subagent is practical, run a distinct local review
  pass and say it was local.

## mode: plan

Review an implementation plan before execution. First classify the plan target
as lightweight or durable artifact. Lightweight plans are reviewed for scope,
feasibility, verification, and ambiguity. Durable artifact plans are additionally
reviewed against artifact completeness and handoff requirements.

Check:

- Plan source: lightweight plans may live in chat/native checklist state;
  durable-required plans have a Markdown artifact path, normally
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`, and the review reads it directly
  instead of relying on `update_plan`, chat summaries, or executor claims.
- Scope: every step traces to the stated goal or root cause.
- Assumptions: missing inputs are explicit and safe.
- Feasibility: files, commands, environments, and dependencies are plausible.
- Requirements-to-evidence mapping: each requirement or acceptance criterion
  maps to observed evidence or a verification step that will prove it.
- Research grounding: when the plan depends on external behavior, upstream bugs,
  current CLI/API behavior, or ambiguous architecture claims, it references a
  readable research artifact or explicitly states why local evidence is enough.
- Sacred boundaries: no protected contracts, architecture, claims, or user
  constraints are changed.
- Verification design: focused checks prove the goal; broader checks are
  included when warranted, with expected results stated.
- Risk: regressions, rollback/rework path, and stop rules are identified.
- Simplicity: no broad refactor, abstraction, or downstream cleanup unless
  required by evidence.
- Subagent Routing: if subagents are used, the plan includes role, task scope,
  Teamwork model tier, context strategy, parallel or serial ordering,
  independence from other tracks, and why each role is needed. Conceptual
  routing must be specific enough for execution to derive native dispatch
  fields from the router mapping. Design work should not be assigned to Worker,
  and high-risk plan or execution review should not use a low-capability tier.
  For non-lightweight plans, the routing should identify independent tracks or
  explain why there is no useful parallel track.
  If subagents are intentionally skipped for durable, delegated, high-risk, or
  goal-mode work, the plan explains why main-agent continuity is sufficient.

Hard gates:

- For durable-required work, a missing or unreadable plan artifact must return
  `revise` or `blocked`. For lightweight work, absence of a repository artifact
  is not a finding by itself; return `revise` only if scope, steps,
  verification, expected result, or stop condition are unclear.
- A plan with unresolved placeholders, ellipses as executable steps, vague
  testing instructions, missing requirements-to-evidence mapping, missing
  verification design, missing expected results, or missing worker/reviewer
  handoffs for durable-required work must return `revise` or `blocked`.
- If subagents are used, missing or misleading routing must return `revise` or
  `blocked`. If subagents are intentionally skipped for durable, delegated,
  high-risk, or goal-mode work, verify that the plan explains why main-agent
  continuity is sufficient. Lightweight plans without subagents do not need a
  skip rationale.
- A Codex plan that explicitly includes native dispatch fields and combines
  `fork_context:true` with `agent_type`, `model`, or `reasoning_effort`; uses
  nonexistent native agent types such as `judge`, `reviewer`, or `designer`;
  or claims high-reasoning routing that would actually inherit a lower parent
  effort must return `revise` or `blocked`.
- A plan that changes protected contracts, architecture, or public behavior
  without explicit scope and verification must return `blocked`.

## mode: execution

Review completed implementation before any high-risk, artifact-backed, or
goal-mode completion claim.

Check:

- Diff: only planned files and necessary lines changed.
- Artifacts: expected files, outputs, metrics, or UI state exist and match the
  acceptance criteria.
- Tests: focused verification ran; broader validation is present when warranted.
- Regressions: look for broken contracts, hidden behavior changes, brittle
  assumptions, and cleanup masking producer bugs.
- Deviations: any departure from the plan is justified by evidence.
- Plan conformance: for artifact-backed or goal-mode work, compare the diff and
  verification against the accepted durable plan artifact. For lightweight work,
  compare against the accepted chat/native plan and user request.
- Routing conformance: when subagents were used, compare the actual agent roles,
  Teamwork model tier choices, context strategy, and ordering to the accepted
  routing; unexplained drift from the routing must return `revise` or `blocked`.
- Codex dispatch validity: when execution evidence or the accepted plan includes
  native dispatch fields, reject full-history fork plus override fields,
  nonexistent native agent types, or inherited lower-effort routing while
  claiming explicit high reasoning.
- Workspace hygiene: no unrelated edits, generated churn, or overwritten work
  from others.
- Narrative-mislead risk: check whether version names, stale docs, comments, or
  historical explanations caused the executor to edit the wrong path, trust the
  wrong behavior, or declare completion too early.

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
