---
name: teamwork-goal
description: Use when the user asks to run until it passes, iterate until done, keep going until convergence, or gives a verifiable target with a budget.
---

# Teamwork Goal

Use this stage for `mode: goal` when the user wants autonomous progress to
verified success, budget exhaustion, repeated no-progress, or a hard blocker.
Ordinary one-shot research, planning, execution, or review should use the
narrower Teamwork stage.

Goal mode is stricter than normal Teamwork. Every completion claim must be
anchored to a durable plan artifact, direct verification, execution review, and
checkpoint/audit evidence. Codex uses native goal state; Claude Code uses
`raoctl.py` Stop-hook state.

Read shared references only as needed:

- `skills/teamwork/references/workflow-contract.md` for evidence, context,
  progress anchors, and subagent collaboration.
- `skills/teamwork/references/goal-iteration.md` for the goal input contract,
  Research + Plan Adequacy Gate, and rolling report table.
- `skills/teamwork/references/artifact-protocol.md` for artifact retrieval and
  hygiene.

## Inputs

- Objective, deliverable, failing command, or artifact target.
- Verification evidence that proves success. Recommended shape:
  `/teamwork:goal 达成 <目标>，用 <可验证证据> 验收，保持 <限制条件> 不破坏，只允许使用 <输入/工具/文件边界>，每轮根据 <下一步判断规则> 决策。`
- Budget, stop rules, allowed tools/files, sacred boundaries, and mutable scope.
- Existing `active_plan_artifact` or report artifact if present.
- Runtime state:
  - Codex: native Codex goal state when explicitly requested or already active.
  - Claude: `.claude/teamwork-goals/*.goal.md`, including
    `active_plan_artifact`, `active_plan_artifact_sha256`, checkpoint review
    verdicts, verification result, evidence delta, research disposition,
    artifacts read, agent routing decision, and `no_progress_count`.

Ask the user only for destructive risk, auth/credentials, missing required
external resources, sacred-boundary conflict, or ambiguity that changes public
behavior, protected contracts, architecture, or user intent.

## Plan Anchor Requirement

Every executable goal iteration needs a durable Markdown plan artifact:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

If no readable plan exists, create one through `teamwork-plan`. In Claude
runtime, record it with:

```bash
raoctl.py plan docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

The recorded `active_plan_artifact` and SHA are the shared anchor for
continuation, Worker execution, execution review, checkpointing, and completion
audit. Do not infer the plan from newest files, chat history, `update_plan`, or
summaries. If the plan changes, record it again and repeat plan review,
execution review, and checkpointing.

Claude runtime now accepts only full goal plans with these sections: Goal,
Requirements Mapping, Evidence Read, Scope, Implementation Steps, Verification,
Risks, Stop Rules, Worker Handoff, Review Handoff, and Subagent Routing.

## Controller Loop

1. Initialize objective, assumptions, boundaries, verification target, budget,
   active plan, and active report.
2. Retrieve prior research and report rows before repeating a hypothesis.
3. Research or refresh research when causes/options are unclear, external
   assumptions matter, or a focused attempt has no evidence delta.
4. Plan through `teamwork-plan`; record the durable plan in Claude runtime.
5. Review the plan with `teamwork-review` mode: plan.
6. Execute the accepted plan through `teamwork-execute`.
7. Verify with focused evidence first.
8. Review execution with `teamwork-review` mode: execution.
9. Append the rolling report row under
   `docs/teamwork/reports/YYYY-MM-DD-<slug>.md`.
10. Record the checkpoint in Claude runtime:

```bash
raoctl.py checkpoint \
  --plan-review-verdict pass \
  --execution-review-verdict pass \
  --verification-command "focused verification command" \
  --verification-result pass \
  --evidence-delta progress \
  --research-disposition reuse \
  --research-artifacts-read "docs/teamwork/research/YYYY-MM-DD-<slug>.md" \
  --agent-routing-decision "main-agent continuity; no useful parallel Worker track" \
  --attempt "hypothesis or attempt" \
  --changes "files or behavior changed" \
  --research-plan-decision "accept active plan" \
  --next-step "accept, retry, or stop reason"
```

11. Accept only when verification passes and execution review passes. Otherwise
    enter the Research + Plan Adequacy Gate.

## Research + Plan Adequacy Gate

Enter this gate after failed verification, `revise`/`blocked` review, acceptance
uncertainty, `no-progress`, or plan mismatch. Read failed verification, current
plan and SHA, execution review, rolling report, and relevant research. Decide
whether the issue is research gap, plan insufficiency, wrong scope, over-strict
stop rule, implementation deviation, or true blocker. Refresh research, revise
or replace the durable plan, record the plan again, and repeat plan review when
new evidence changes the path.

## Completion Rules

- Default budget is 3 iterations when unspecified.
- Stop after 2 consecutive `no-progress` checkpoints.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing required resources, or public-contract/user-intent ambiguity.
- A rolling report is memory, not completion proof.
- In Codex, mark the native goal complete only after focused verification and
  execution review pass.
- In Claude, emit the completion promise only after passing checkpoint state and
  include the structured completion audit in the same final assistant message.

## Completion Audit

Claude auto-completion requires the configured promise and this audit:

```text
<completion_audit>
<plan_artifact>docs/teamwork/plans/YYYY-MM-DD-<slug>.md</plan_artifact>
<plan_artifact_sha256>recorded sha256</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>requirement -> command/path/artifact evidence</requirements_mapping>
<verification_evidence>commands, artifacts, paths, or inspected evidence</verification_evidence>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

The `plan_review_verdict` and `execution_review_verdict` must each be exactly
`pass` or `pass-with-notes`; the runtime also lints
`requirements_mapping` and `verification_evidence` for concrete paths,
commands, artifacts, or requirement-to-evidence mappings.

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
- requirements_mapping: <requirement-to-evidence map with paths/commands/artifacts>
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
