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

- Scope: every step traces to the stated goal or root cause.
- Assumptions: missing inputs are explicit and safe.
- Feasibility: files, commands, environments, and dependencies are plausible.
- Sacred boundaries: no protected contracts, architecture, claims, or user
  constraints are changed.
- Verification design: focused checks prove the goal; broader checks are
  included when warranted.
- Risk: regressions, rollback/rework path, and stop rules are identified.
- Simplicity: no broad refactor, abstraction, or downstream cleanup unless
  required by evidence.

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
