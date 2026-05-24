---
name: teamwork-review
description: Use when reviewing a plan, diff, completed implementation, or before claiming non-trivial Teamwork work is complete.
---

# Teamwork Review

Use for a distinct reviewer pass when review adds value. Review reads direct
evidence and preserves dissent. Do not rely only on a planner, executor, tool,
or previous reviewer summary.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for shared evidence
  and context rules.
- `skills/using-teamwork/references/review-checks.md` for plan/execution
  checklists and hard gates.
- `skills/using-teamwork/references/subagent-routing.md` for routing checks.
- `skills/using-teamwork/references/goal-iteration.md` for goal failure
  routing.

## Shared Rules

- Choose `mode: plan` or `mode: execution`.
- Prefer fresh-context review for non-trivial execution; otherwise run a
  distinct local review pass and say it was local.
- Inspect primary evidence: source, diff, logs, tests, command output,
  artifacts, research, plan, and user constraints.
- Label important evidence `observed`, `inferred`, or `claimed`.
- Treat executor summaries, `codex review`, CI summaries, and other tool output
  as evidence inputs, not final verdicts.
- Do not fix issues during review unless explicitly asked.

## mode: plan

Use `review-checks.md` to check scope, assumptions, requirements-to-evidence
mapping, research grounding, verification design, risks, handoffs, and subagent
routing. Return `revise` or `blocked` for missing durable artifacts,
placeholders, vague verification, missing handoffs, unsafe routing, or protected
contract changes outside scope.

## mode: execution

Use `review-checks.md` to check diff scope, artifacts, tests, regressions, plan
conformance, Routing conformance, workspace hygiene, and next failure route.

## Verdict Format

```text
Mode: plan | execution
Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>
Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>
Dissent / Uncertainty: <none or concern>
Verdict: pass | pass-with-notes | revise | blocked
Rationale: <brief evidence-based reason>
```
