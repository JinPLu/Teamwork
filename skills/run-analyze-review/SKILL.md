---
name: run-analyze-review
description: >-
  Use for independent review in a run-analyze-optimize workflow. Supports
  mode: plan for plan review and mode: execution for implementation review.
disable-model-invocation: true
---

# Run-Analyze Review

Use this subskill for a distinct reviewer pass. The reviewer reads evidence
independently and preserves dissent. Do not rely only on the planner's or
executor's summary.

## Shared Review Rules

- Choose one mode explicitly: mode: plan or mode: execution.
- Read primary evidence: source, diffs, logs, artifacts, tests, and user
  constraints as relevant.
- Separate facts from inferences.
- Check against the goal, sacred boundaries, budget, and stop rules.
- Preserve dissent and uncertainty, even when the final verdict is pass.
- Do not fix issues during review unless explicitly asked; report findings.

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

## Verdict Format

```text
Mode:
- plan | execution

Evidence Read:
- <path/command/artifact>: <finding>

Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>

Dissent / Uncertainty:
- <preserved concern or none>

Verdict:
- pass | pass-with-notes | revise | blocked

Rationale:
- <brief evidence-based reason>
```
