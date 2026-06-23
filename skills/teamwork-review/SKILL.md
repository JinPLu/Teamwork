---
name: teamwork-review
description: Use when the user asks to review/check a plan, artifact, diff, implementation, research output, completion claim, strict quality, deslop pass, PR walkthrough, or acceptance evidence.
---

# Teamwork Review

Use for non-lightweight acceptance, output/diff scrutiny, strict-quality/deslop
checks, PR walkthroughs, and reviewer passes. Review reads evidence directly and
never relies on summaries.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence rules; `skills/using-teamwork/references/review-checks.md` for the
plan/execution checks; `skills/using-teamwork/references/verification-patterns.md`
for proof strength and baseline/treatment checks; `skills/using-teamwork/references/review-lenses.md`
for strict review, deslop, and reviewer-comprehension lenses; `skills/using-teamwork/references/role-playbook.md` for
Reviewer method; `skills/using-teamwork/references/subagent-dispatch.md` and
`skills/using-teamwork/references/subagent-contract.md` for Reviewer dispatch and
the verdict packet; `skills/using-teamwork/references/debug-mode.md` for
debug-derived evidence and cleanup checks; `skills/using-teamwork/references/artifact-protocol.md` when
review needs durable memory.

## Rules

- Choose `mode: plan`, `mode: execution`, or `mode: output`.
- Prefer a fresh-context Reviewer subagent for non-lightweight required
  acceptance — high-risk, public-contract, delegated, security, destructive,
  release, and goal-mode work. Same-context self-review is not acceptance.
- Local review is fine for lightweight work, same-context checks, or when
  subagent tools are unavailable after discovery; label any required fresh-review
  verdict as unreviewed when no fresh review ran.
- Inspect sources, artifacts, diff, logs, tests, command output, plan, and user
  constraints. Label key evidence `observed`, `inferred`, or `claimed`, and
  check confidence against it.
- Treat executor summaries, `code-reviewer` output, git diff, CI summaries, and
  test output as inputs, not final verdicts.
- Do not fix issues during review unless asked.
- Reject open delegated tracks without a blocker rationale.

## Plan Review

Check scope, requirements mapping, evidence, verification, Required Values /
Invariants, accepted fallback contracts, risks, dispatch split, and
protected-boundary changes. See `review-checks.md`.
For goal-mode retry plans, also verify Goal Invariants, Replay Preflight, and
Goal Anchor fields before accepting.

## Execution Review

Check output/diff scope, plan conformance, verification evidence, no
invariant-masking fallback, the Actual Dispatch Log, Worker packets when
Workers ran, dispatch economics, and workspace hygiene. Confirm the dispatch
split was considered even when the plan did not name every track. For re-review after `revise`, require
the prior verdict, required fixes, fix evidence, and a re-review verdict.
For goal-mode work, require the Attempt Record, any Failure Reflection, and a
drift/retry verdict tied to prior attempts.
For debug-derived work, also check repro evidence, hypothesis-to-evidence
mapping, root-cause support, post-fix repro/verification on the same surface,
and cleanup of temporary instrumentation. When explicitly asked for strict code
quality review, deslop, PR walkthrough, or when acceptance reveals structural
regression, load `review-lenses.md`.

## Verdict

```text
Mode: plan | execution | output
Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>
Requirements / Evidence Map:
- <requirement or step> -> <evidence> -> <pass|fail|partial|not reviewed>
Verification Strength: live-verified | targeted-test-verified | build-only | blocked | failed | not_applicable
Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>
Dissent / Uncertainty: <none or concern>
Verdict: accept | revise | blocked
Rationale: <brief evidence-based reason>
```

Use `blocker`, `major`, `minor` consistently: unsafe/impossible acceptance,
required-before-proceed, or follow-up note. Include `Memory Delta:` only when
durable project memory was checked or changed.
