---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget — autonomous goal mode using Codex native goals or Claude Stop-hook continuation.
---

# Teamwork Goal

Use this subskill for `mode: goal` only when the user gives a goal, command,
artifact target, or failure and wants autonomous progress to verified success
or a clear stop. Ordinary research, planning, review, or one-shot execution
must use the narrower Teamwork stage skill instead.

Goal mode is intentionally stricter than normal Teamwork. The durable plan,
verification, review, and checkpoint/audit requirements below are safeguards for
autonomous continuation, not requirements for ordinary one-shot tasks. In Codex,
goal mode is protocol-backed through native Codex goals and explicit progress
anchors; in Claude Code plugin mode, it is Stop-hook-backed through `raoctl.py`.

For the detailed goal input contract, Research + Plan Adequacy Gate, and
rolling report table, read `skills/teamwork/references/goal-iteration.md`.

The goal controller owns iteration and acceptance. It does not let one
executor self-declare completion. Every completion claim must be anchored to a
durable plan artifact, focused verification, and execution review.

## Inputs

- Goal objective, explicit deliverables, or failing command/artifact target.
- Verification evidence that proves success. Recommended user-facing shape:
  `/teamwork:goal 达成 <目标>，用 <可验证证据> 验收，保持 <限制条件> 不破坏，只允许使用 <输入/工具/文件边界>，每轮根据 <下一步判断规则> 决策。`
  Angle brackets are prompt guidance only; do not leave `<...>` placeholders in
  artifacts.
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

Codex should not emulate Claude Stop hooks. Use native Codex goal state only
when the user explicitly asks for autonomous convergence or when a goal is
already active; otherwise use the narrower research, plan, execute, or review
stage.

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
   verification target, budget, current `active_plan_artifact`, and current
   report artifact if present.
2. Retrieve prior memory: search relevant `docs/teamwork/research/` artifacts
   and the current `docs/teamwork/reports/` rolling report before repeating an
   old hypothesis.
3. Research if causes or options are unclear, or refresh research when
   execution becomes locally self-confirming: use `teamwork-research`.
   After one focused fix or prompt change with no evidence delta, enter the
   Research + Plan Adequacy Gate before another local guess.
4. Plan: use `teamwork-plan`; ensure the plan artifact is readable and recorded
   as `active_plan_artifact` in Claude runtime state when goal execution changes files.
5. Review the plan: use `teamwork-review` with `mode: plan`; revise until pass
   or blocked.
6. Execute: use `teamwork-execute` on the accepted durable plan artifact.
7. Verify: run focused checks first and collect real evidence.
8. Review execution: use `teamwork-review` with `mode: execution`, comparing
   diff and verification against `active_plan_artifact`.
9. Append the goal rolling report row under
   `docs/teamwork/reports/YYYY-MM-DD-<slug>.md`. In Claude runtime, prefer the
   checkpoint command fields that write this row.
10. In Claude runtime, record the checkpoint:

```bash
raoctl.py checkpoint \
  --plan-review-verdict pass \
  --execution-review-verdict pass \
  --verification-command "focused verification command" \
  --verification-result pass \
  --evidence-delta progress \
  --attempt "hypothesis or attempt" \
  --changes "files or behavior changed" \
  --research-plan-decision "accept plan or refresh research/plan" \
  --next-step "accept, retry, or stop reason"
```

11. Decide: accept only if verification and execution review pass. If
    verification fails, acceptance cannot be judged, review returns
    `revise`/`blocked`, evidence delta is `no-progress`, or a plan mismatch is
    reported, enter the Research + Plan Adequacy Gate. Stop only for true
    blockers or budget exhaustion.

## Research + Plan Adequacy Gate

Before retrying after failure, read the failed verification, execution review,
current durable plan, rolling report, and relevant research. Decide whether the
plan lacked evidence, held a stale assumption, chose the wrong scope, blocked
too aggressively, or whether execution deviated from a valid plan. If research
or plan revision can resolve the issue, update research, revise or replace the
durable plan, record the plan again, repeat plan review, then retry within
budget. Treat only missing credentials/resources, destructive risk,
sacred-boundary conflict, budget exhaustion, or unresolved user intent/public
contract ambiguity as true blockers.

## Autonomous Discipline

- Treat the goal as concrete deliverables plus verification targets.
- Read direct evidence before each decision; do not rely on summaries.
- Keep the plan artifact path visible in worker and reviewer handoffs.
- If verification fails, identify the evidence delta, run the Research + Plan
  Adequacy Gate, then continue only with refreshed research/plan evidence.
- If one focused fix or prompt change produces no evidence delta, refresh
  research before another local implementation attempt.
- Append a rolling report row after every verification/review cycle. The report
  is memory, not completion proof.
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

Rolling Report:
- docs/teamwork/reports/YYYY-MM-DD-<slug>.md

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
