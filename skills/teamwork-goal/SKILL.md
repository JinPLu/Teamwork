---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget — autonomous goal mode with Stop-hook continuation.
---

# Teamwork Goal

Use this subskill for `mode: goal` only when the user gives a goal, command,
artifact target, or failure and wants autonomous progress to verified success
or a clear stop. Ordinary research, planning, review, or one-shot execution
must use the narrower Teamwork stage skill instead.

Goal mode is intentionally stricter than normal Teamwork. The durable plan,
checkpoint, and completion-audit requirements below are runtime safeguards for
autonomous continuation, not requirements for ordinary Claude Code tasks.

The goal controller owns iteration and acceptance. It does not let one
executor self-declare completion. Every completion claim must be anchored to a
durable plan artifact, focused verification, and execution review.

## Inputs

- Goal objective, explicit deliverables, or failing command/artifact target.
- Budget: max iterations, stop rules, and completion promise when provided.
- Sacred boundaries and mutable scope.
- Active plan artifact when one already exists.
- Runtime state:
  - Codex: native Codex goal state when explicitly requested or already active.
  - Claude Code plugin: `.claude/teamwork-goals/*.goal.md`, including
    `active_plan_artifact`, `active_plan_artifact_sha256`, checkpoint review
    verdicts, verification result, evidence delta, and `no_progress_count`
    when set.

If a goal is active, continue it rather than creating a second goal. Ask the
user only for destructive risk, auth/credentials, missing required external
resources, sacred-boundary conflict, or ambiguity that changes public behavior,
protected contracts, architecture, or user intent.

## Plan Anchor Requirement

Every goal iteration that can execute changes must use a durable Markdown plan
artifact before execution:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

If no readable plan artifact exists, first route to `teamwork-plan` and write
one. In Claude Code plugin mode, record the selected artifact in goal state with:

```bash
raoctl.py plan docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

The recorded `active_plan_artifact` is the shared anchor for continuation,
Worker execution, execution review, and completion audit. Do not infer the
active plan from the newest file in `docs/teamwork/plans`, chat history,
`update_plan`, or a summary.

When a new iteration needs a materially different plan, create or update the
durable plan artifact first, then update `active_plan_artifact` before
execution continues.

Claude runtime records the plan file SHA-256 at plan-record time. If the file
changes afterward, record the plan again and repeat plan review, execution
review, and checkpoint recording before automatic completion.

## Default Budget

- Maximum 3 optimization iterations when unspecified.
- Stop after 2 consecutive iterations with no evidence delta.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing credentials, unavailable required resources, or ambiguous product
  intent that affects behavior.

## Controller Loop

1. Initialize: state objective, assumptions, sacred boundaries, mutable scope,
   verification target, budget, and current `active_plan_artifact`.
2. Research only if causes or options are unclear, or refresh research when
   execution becomes locally self-confirming: use `teamwork-research`.
3. Plan: use `teamwork-plan`; ensure the plan artifact is readable and recorded
   as `active_plan_artifact` in Claude runtime state when goal execution changes files.
4. Review the plan: use `teamwork-review` with `mode: plan`; revise until pass
   or blocked.
5. Execute: use `teamwork-execute` on the accepted durable plan artifact.
6. Verify: run focused checks first and collect real evidence.
7. Review execution: use `teamwork-review` with `mode: execution`, comparing
   diff and verification against `active_plan_artifact`.
8. In Claude runtime, record the checkpoint:

```bash
raoctl.py checkpoint \
  --plan-review-verdict pass \
  --execution-review-verdict pass \
  --verification-command "focused verification command" \
  --verification-result pass \
  --evidence-delta progress
```

9. Decide: accept only if verification and execution review pass; otherwise
   continue with a new hypothesis, stop at budget, or report a blocker.

## Autonomous Discipline

- Treat the goal as concrete deliverables plus verification targets.
- Read direct evidence before each decision; do not rely on summaries.
- Keep the plan artifact path visible in worker and reviewer handoffs.
- If verification fails, identify the evidence delta, choose the next smallest
  hypothesis, and continue within budget.
- If there is no evidence delta for 2 consecutive iterations, stop with a
  blocker or budget/no-progress conclusion.
- In Codex, create a native goal only when the user explicitly asks for
  autonomous convergence and no active goal exists. Mark it complete only after
  focused verification and execution review pass.
- In Claude Code plugin mode, emit the configured completion promise only after
  verification and execution review pass, and include the required structured
  completion audit in the same final assistant message.

## Completion Audit

Claude Code plugin auto-completion requires the configured completion promise
and this structured audit in the same final assistant message:

```text
<completion_audit>
<plan_artifact>docs/teamwork/plans/YYYY-MM-DD-<slug>.md</plan_artifact>
<plan_artifact_sha256>recorded sha256</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>map each requirement to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

The `plan_review_verdict` and `execution_review_verdict` must each be exactly
`pass` or `pass-with-notes`. The `plan_artifact` and
`plan_artifact_sha256` must match runtime state. The runtime checkpoint must be
current for that SHA, verification result must be `pass`, and both stored
review verdicts must be passing. The Stop hook must not auto-complete on the
completion promise alone, on an audit without matching plan identity, without
a current checkpoint, or on non-passing review or verification state.

## Output

```text
Route: teamwork-goal
Reason: <one sentence tied to autonomous convergence>
Mode: goal

Goal:
- ...

Active Plan Artifact:
- docs/teamwork/plans/YYYY-MM-DD-<slug>.md

Iterations:
- <n>: research/plan/execute/review summary

Verification:
- <command/artifact/check>: <result>

Review:
- Plan review: <verdict>
- Execution review: <verdict and dissent>

Completion Audit:
- plan_artifact: <path>
- plan_artifact_sha256: <sha256>
- plan_review_verdict: <pass | pass-with-notes>
- execution_review_verdict: <pass | pass-with-notes>
- requirements_mapping: <evidence map>
- verification_evidence: <commands/artifacts/inspection>
- dissent: <none or residual risk>

Codex Goal State:
- native goal created | continued | not used
- completion marked only after verification + execution review

Unresolved:
- <none or blockers>

Conclusion:
- accept | blocked | budget exhausted | stopped
```
