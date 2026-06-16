---
name: teamwork-review
description: Use when reviewing a plan, diff, implementation, or non-trivial completion claim.
---

# Teamwork Review

Use for non-lightweight acceptance and reviewer passes. Review reads evidence
directly and never relies on summaries.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence rules; `skills/using-teamwork/references/review-checks.md` for the
plan/execution checks; `skills/using-teamwork/references/role-playbook.md` for
Reviewer method; `skills/using-teamwork/references/subagent-dispatch.md` and
`skills/using-teamwork/references/subagent-contract.md` for Reviewer dispatch and
the verdict packet; `skills/using-teamwork/references/artifact-protocol.md` when
review needs durable memory.

## Rules

- Choose `mode: plan` or `mode: execution`.
- Prefer a fresh-context Reviewer subagent for non-lightweight required
  acceptance — high-risk, public-contract, delegated, security, destructive,
  release, and goal-mode work. Same-context self-review is not acceptance.
- Local review is fine for lightweight work, same-context checks, or when
  subagent tools are unavailable after discovery; label any required fresh-review
  verdict as unreviewed when no fresh review ran.
- Inspect source, diff, logs, tests, command output, artifacts, plan, and user
  constraints. Label key evidence `observed`, `inferred`, or `claimed`, and check
  confidence against it.
- Treat executor summaries, `code-reviewer` output, git diff, CI summaries, and
  test output as inputs, not final verdicts.
- Do not fix issues during review unless asked.
- Reject open delegated tracks without a blocker rationale.

## Plan Review

Check scope, requirements mapping, evidence, verification, explicit required
values (no silent fallback defaults), risks, dispatch split, and
protected-boundary changes. See `review-checks.md`.

## Execution Review

Check diff scope, plan conformance, verification evidence, no silent fallback
defaults, the Actual Dispatch Log, Worker packets when Workers ran, dispatch
economics, and workspace hygiene. Confirm the dispatch split was considered even
when the plan did not name every track. For re-review after `revise`, require
the prior verdict, the required fixes, fix evidence, and a re-review verdict.

## Verdict

```text
Mode: plan | execution
Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>
Requirements / Evidence Map:
- <requirement or step> -> <evidence> -> <pass|fail|partial|not reviewed>
Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>
Dissent / Uncertainty: <none or concern>
Verdict: accept | revise | blocked
Rationale: <brief evidence-based reason>
```

Use `blocker`, `major`, `minor` consistently: unsafe/impossible acceptance,
required-before-proceed, or follow-up note. Include `Memory Delta:` only when
durable project memory was checked or changed.
