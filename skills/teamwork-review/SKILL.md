---
name: teamwork-review
description: Use when the user asks to review/check a plan, artifact, diff, implementation, research output, completion claim, strict quality, deslop pass, PR walkthrough, or acceptance evidence.
---

# Teamwork Review

Use for non-lightweight acceptance, output/diff scrutiny, strict-quality/deslop
checks, PR walkthroughs, and reviewer passes. Review reads evidence directly and
never relies on summaries.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence; `review-checks.md` for plan/execution checks;
`verification-patterns.md` for proof strength; `review-lenses.md` for strict
review/deslop; `role-playbook.md`, `subagent-dispatch.md`, and
`subagent-contract.md` for Reviewer method and packets; `debug-mode.md` for
debug evidence; `artifact-protocol.md` for durable memory; `eval-gate.md` for
Teamwork package/harness gates; `grill-mode.md` for explicit grill mode.

## Rules

- Choose `mode: plan`, `mode: execution`, or `mode: output`.
- Prefer a fresh-context Reviewer subagent for non-lightweight required
  acceptance — high-risk, public-contract, delegated, security, destructive,
  release, and goal-mode work. Same-context self-review is not acceptance.
- Local review is fine for lightweight work, same-context checks, or when
  subagent tools are unavailable after discovery; label any required fresh-review
  verdict as unreviewed when no fresh review ran.
- Inspect sources, artifacts, diff, logs, tests, command output, plan, and user
  constraints; label key evidence `observed`, `inferred`, or `claimed`.
- Treat executor summaries, `code-reviewer` output, git diff, CI summaries, and
  test output as inputs, not final verdicts.
- Do not fix issues during review unless asked.
- Reject delegated tracks without a returned packet or blocker rationale.
- For every code diff, apply the code-maintenance baseline: owner, flow,
  tests/config, invariants, and no fallback masking.
- For Teamwork package behavior changes, require eval results or `no relevant
  eval case`; reject empty release split evidence; check ledgers for material
  skill/harness decisions.
- Release, high-risk harness, and public-contract package changes need fresh
  review after validation/evals; same-context acceptance is insufficient.
- When grill mode was invoked, reject planning or implementation that lacks a
  confirmed Shared Understanding Packet, invented user answers, or edited during
  active grill mode.

## Plan Review

Check scope, requirements mapping, evidence, verification, Required Values /
Invariants, accepted fallback contracts, risks, dispatch split, and boundaries.
For goal-mode retry plans, also verify Goal Invariants, Replay Preflight, and
Goal Anchor fields before accepting.

## Execution Review

Check diff scope, plan conformance, verification, no invariant-masking
fallback, Actual Dispatch Log, Worker packets, dispatch economics, and hygiene.
For re-review after `revise`, require prior verdict, fixes, evidence, and
re-review verdict.
For goal-mode work, require the Attempt Record, any Failure Reflection, and a
drift/retry verdict tied to prior attempts.
For debug-derived work, check repro, hypothesis evidence, root cause, same-surface
post-fix verification, and instrumentation cleanup. Load `review-lenses.md` for
strict quality, deslop, PR walkthrough, or structural regression.

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
