---
name: teamwork-review
description: Use when a Teamwork plan or execution result needs independent review from direct evidence.
---

# Teamwork Review

Use this subskill for a distinct reviewer pass. The reviewer reads evidence
independently and preserves dissent. Do not rely only on the planner's or
executor's summary.

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

## mode: plan

Review an implementation plan before execution.

Check:

- Durable plan artifact: non-lightweight work has a Markdown plan artifact path,
  normally `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`, and the review reads it
  directly instead of relying on `update_plan`, chat summaries, or executor
  claims.
- Scope: every step traces to the stated goal or root cause.
- Assumptions: missing inputs are explicit and safe.
- Feasibility: files, commands, environments, and dependencies are plausible.
- Requirements-to-evidence mapping: each requirement or acceptance criterion
  maps to observed evidence or a verification step that will prove it.
- Sacred boundaries: no protected contracts, architecture, claims, or user
  constraints are changed.
- Verification design: focused checks prove the goal; broader checks are
  included when warranted, with expected results stated.
- Risk: regressions, rollback/rework path, and stop rules are identified.
- Simplicity: no broad refactor, abstraction, or downstream cleanup unless
  required by evidence.
- Subagent Routing: non-lightweight plans include role, task scope, model tier,
  parallel or serial ordering, and why each role is needed or skipped. Design
  work should not be assigned to Worker, and high-risk plan or execution review
  should not use a low-capability tier.

Hard gates:

- For non-lightweight work, a missing durable plan artifact, a plan that relies
  only on transient `update_plan` or chat state, or a plan whose artifact cannot
  be read must return `revise` or `blocked`.
- A plan with unresolved placeholders, ellipses as executable steps, vague
  testing instructions, missing requirements-to-evidence mapping, missing
  verification design, missing expected results, or missing worker/reviewer
  handoffs must return `revise` or `blocked`.
- A non-lightweight plan missing Subagent Routing, or routing design work to
  Worker, or using an underpowered tier for high-risk review, must return
  `revise` or `blocked`.
- A plan that changes protected contracts, architecture, or public behavior
  without explicit scope and verification must return `blocked`.

## mode: execution

Review completed implementation before any completion claim.

Check:

- Diff: only planned files and necessary lines changed.
- Artifacts: expected files, outputs, metrics, or UI state exist and match the
  acceptance criteria.
- Tests: focused verification ran; broader validation is present when warranted.
- Regressions: look for broken contracts, hidden behavior changes, brittle
  assumptions, and cleanup masking producer bugs.
- Deviations: any departure from the plan is justified by evidence.
- Plan conformance: for non-lightweight work, compare the diff and verification
  against the accepted durable plan artifact; unexplained drift from that plan
  must return `revise` or `blocked`.
- Routing conformance: compare the actual agent roles and model tier choices to
  the accepted routing; unexplained drift from the routing must return
  `revise` or `blocked`.
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
