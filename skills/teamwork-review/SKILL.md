---
name: teamwork-review
description: Use when reviewing a plan, diff, completed implementation, or before claiming non-trivial Teamwork work is complete.
---

# Teamwork Review

Use for a distinct reviewer pass when review adds value. Review reads direct
evidence, preserves dissent, and does not rely only on planner/executor/tool
summaries.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and context rules.
- `skills/using-teamwork/references/review-checks.md` for plan/execution gates.
- `skills/using-teamwork/references/dispatch-policy.md` for Reviewer dispatch and routing checks.
- `skills/using-teamwork/references/subagent-prompt-contract.md` before Reviewer prompts.
- `skills/using-teamwork/references/subagent-packets.md` for Reviewer Verdict Packet.
- `skills/using-teamwork/references/goal-iteration.md` for goal failure routing.

## Shared Rules

- Choose `mode: plan` or `mode: execution`.
- Default to fresh-context Reviewer subagents for non-trivial execution;
  otherwise state why local review is cheaper or safer.
- Inspect source, diff, logs, tests, command output, artifacts, research, plan,
  and user constraints.
- Label important evidence `observed`, `inferred`, or `claimed`.
- Treat executor summaries, `codex review`, CI summaries, and tool output as
  evidence inputs, not final verdicts.
- Do not fix issues during review unless explicitly asked.

## Plan Review

Use `review-checks.md` for scope, assumptions, requirements mapping, evidence,
verification, risks, handoffs, routing, missing Parallelization Gate, prompt
contract, Required Output Schema, and protected-boundary changes.

## Execution Review

Use `review-checks.md` for diff scope, plan conformance, verification,
Routing conformance, Actual Dispatch Log, Worker Completion Packet, Reviewer
Verdict Packet, dispatch economics, workspace hygiene, and next failure route.
Confirm Stage-Routed Proactive Dispatch was evaluated even when the plan did not
name every track.

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
