---
name: teamwork
description: Use when a request should enter an evidence-first Teamwork workflow, especially for research, planning, execution, review, or autonomous convergence.
---

# Teamwork

This is the public entrypoint and goal controller for the package. Use it to
coordinate main-agent ownership with subagent research, execution, review, and
acceptance gates. Route a request to the narrowest stage skill, or run a
bounded autonomous loop when the user asks for convergence. In skill-only
installs this autonomy is instructional within the current assistant turn; in
the Claude Code plugin it is runtime-backed by `/rao:goal` state plus a `Stop`
hook that continues incomplete goals across turns until success, budget
exhaustion, or a hard blocker.

The package preserves the original discipline:

- **Karpathy guardrails**: assumptions explicit, simplicity first, surgical
  edits, goal-driven verification.
- **Roundtable-style workflow**: role separation, multi-agent discussion when
  useful, independent review, dissent preservation, and budgeted stopping.
- **No full roundtable infrastructure**: do not import model registries,
  pricing caches, dispatch scripts, or thread ledgers unless the user asks.

## Subagent Collaboration Model

Subagents are a foundation of Teamwork, not a decorative add-on. The main agent
owns scope, decomposition, synthesis, conflict resolution, verification, and
final acceptance. Subagents provide bounded work products:

- Explorer: read-heavy independent investigation with condensed evidence.
- Designer: ambiguous requirements, architecture tradeoffs, cross-module
  solution design, and product behavior choices before execution planning.
- Judge: fresh-context plan review before execution.
- Worker: implementation for an accepted plan with exact file ownership or
  worktree isolation.
- Reviewer: fresh-context execution review against diffs, tests, logs, and
  artifacts.

Use subagents when tracks can run independently, when fresh context reduces
self-confirmation risk, or when splitting context lowers cost. Do not fan out
merely for ceremony, duplicate another agent's unresolved work, or give writing
agents overlapping file ownership.

## Subagent Routing Policy

Subagent role choice and model tier choice are part of routing. Use capability
tiers rather than fixed model IDs so Claude Code, Codex, and Cursor can map the
request to the best available local model:

- `fast`: scoped evidence collection, low-risk mechanical edits, and concise
  documentation cleanup where ambiguity is low.
- `standard`: moderate reasoning, multi-file implementation, or investigation
  that needs synthesis but not high-stakes judgment.
- `high reasoning`: ambiguous requirements, architecture tradeoffs, high-risk
  plan review, final acceptance, regression analysis, or safety/security
  boundary checks.

The main agent is the controller. It chooses the route, verifies evidence,
resolves conflicts, and makes the final decision. Subagents return evidence,
patches, and recommendations; they do not automatically pass their own work.

| Task shape | Role | Model tier | Routing note |
|---|---|---|---|
| Evidence collection or multi-path code research | Explorer | `fast` or `standard` | Use parallel tracks when scopes are independent; raise to `standard` when synthesis is non-trivial. |
| Ambiguous requirements, architecture design, cross-module plans, or product behavior design | Designer | `high reasoning` | Use before planning; do not route unresolved design work to Worker. |
| Plan review or high-risk tradeoff review | Judge | `high reasoning` | Use before execution when the plan is non-lightweight, risky, or ambiguous. |
| Small mechanical implementation or documentation cleanup | Worker | `fast` | Require exact file ownership and accepted scope. |
| Multi-file implementation or public/shared behavior change | Worker, then Reviewer | Worker: `standard`; Reviewer: `high reasoning` | Keep Worker execution bounded by the accepted plan and require fresh-context review. |
| Final acceptance, regression risk, or safety boundary review | Reviewer | `high reasoning` | Treat verification output and diffs as evidence, not automatic approval. |

Goal mode uses the same routing policy inside each iteration. Do not increase
model tier or agent count for ceremony; increase it only when ambiguity, risk,
or cross-module reasoning requires it.

## Evidence Interpretation Contract

Treat narrative labels as claims until verified. File names, directory names,
`v2`, `latest`, comments, README statements, historical notes, issue text, and
executor summaries are not facts by themselves.

Classify important evidence explicitly:

- `observed`: directly inspected source, diff, config, command output, test
  result, log, or artifact.
- `inferred`: a conclusion drawn from observed evidence.
- `claimed`: a statement made by docs, names, comments, summaries, or users
  that still needs corroboration before it drives a decision.

For important judgments, cross-check at least one direct evidence category:
source call path, test behavior, configuration, command output, artifact
properties, or git diff. Do not treat a label such as `latest` or `v2` as proof
that the referenced file is current, canonical, or active.

## Context & Cost Discipline

- Prefer local repository evidence before MCP, network, or web research.
- Use MCP or web only when the task needs external tools, official/current
  information, or user-authorized sources that are not available locally.
- Use subagents primarily for read-heavy independent research, design, judge,
  and review tracks. Writing subagents need exact file ownership or worktree
  isolation.
- Ask subagents for condensed evidence and verdicts, not raw log dumps.
- Default to at most 3 parallel research/review subagents unless the user gives
  a larger budget.
- The main agent owns synthesis, conflict resolution, verification, and the
  final decision even when subagents are used.

## Durable Plan Artifacts

`update_plan` and other visible plan widgets are transient UI-only checklist
state. They help show progress during a turn, but they are not the execution
specification, review target, or durable evidence for any plan.

A durable Markdown plan artifact is a normal repository Markdown file. Every
Teamwork planning pass must create or update one before execution, including
lightweight, low-risk, and single-file changes. Default path:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

Use `teamwork-design` with `mode: plan` to create or update that artifact
before execution. The artifact is shared across Cursor, Claude Code, and Codex
because it is plain Markdown in the repo, not Codex native goal state and not
Claude `.claude/teamwork-goals/` runtime state.

Lightweight changes may use a concise artifact, but they still require explicit
scope, implementation steps, focused verification, expected results, and final
review handoff. High-risk, cross-module, or long-running work needs checkbox
tasks, exact paths, test-first or verification-first steps, expected results,
stop rules, and worker/reviewer handoffs.

## Codex Native Integration

When running in Codex, use native platform capabilities instead of emulating
roundtable infrastructure:

- Use `update_plan` only as a transient UI-only checklist for visible progress.
  It must not be the only execution plan or review artifact.
- Use durable Markdown plan artifacts for all execution plans, with the default
  path `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- Use Codex goals only for explicit autonomous convergence requests or an
  existing active goal. Do not create a goal for ordinary research, planning,
  review, or one-shot execution.
- Use Codex subagents for independent Explorer, Designer, Judge, Worker, or
  Reviewer tracks when multi-agent support is available. Dispatch focused prompts,
  wait for results when they are needed, synthesize conflicts locally, and
  close agents that are no longer needed.
- If subagents are unavailable or the work is tightly coupled, run clearly
  separated local passes instead of pretending the review is independent.
- For code review of real repository diffs, `codex review --uncommitted`,
  `--base`, or `--commit` may be used as review evidence. It is not an
  automatic pass.
- Respect sandbox and approval policy. Do not bypass approvals. If a required
  command fails because of sandbox or network restrictions, request narrow
  escalation with a concise justification.

## Route By Intent

| User intent | Route | Skill file |
|---|---|---|
| Research options, compare approaches, discuss tradeoffs, gather evidence | `teamwork-design` with `mode: research` | `skills/teamwork-design/SKILL.md` |
| Convert a chosen direction into an executable implementation plan | `teamwork-design` with `mode: plan` | `skills/teamwork-design/SKILL.md` |
| Execute an accepted plan with minimal edits and verification | `teamwork-execute` | `skills/teamwork-execute/SKILL.md` |
| plan-review: review a plan before execution | `teamwork-review` with `mode: plan` | `skills/teamwork-review/SKILL.md` |
| execution-review: review diffs, artifacts, tests, and results after execution | `teamwork-review` with `mode: execution` | `skills/teamwork-review/SKILL.md` |
| Iterate autonomously until verified success, budget exhaustion, or blocker | `teamwork` with `mode: goal` | this skill |

Do not create separate plan-review and execution-review subskills. The single
`teamwork-review` subskill has two explicit modes so reviewer orchestration
stays shared while the rubric changes by review target.

Do not create separate research, plan, or goal subskills. Research and planning
share `teamwork-design` with hard mode boundaries; autonomous convergence is
the router's `mode: goal`.

## Routing Rules

Use the narrowest subskill that satisfies the request:

- If the user asks "what should we do?", "research", "compare", "discuss", or
  "find options", route to `teamwork-design` with `mode: research`.
- If the user asks for a plan, route to `teamwork-design` with `mode: plan`.
- If the user gives an accepted plan or says to implement/execute, route to
  `teamwork-execute`.
- If the user asks to review a proposed plan, route to
  `teamwork-review` with `mode: plan`.
- If the user asks to review a diff, patch, artifacts, test result, or completed
  execution, route to `teamwork-review` with `mode: execution`.
- If the user asks to "run until it passes", "iterate until convergence",
  "keep going until done", or gives a verifiable target plus budget, stay in
  this skill and use `mode: goal`.

## Goal Mode

Use `mode: goal` only when the user gives a goal, command, artifact target, or
failure and wants autonomous progress to verified success or a clear stop.

In Codex, if the user explicitly asks for autonomous convergence and no active
goal exists, create a native Codex goal with the objective and optional budget.
If a goal already exists, continue it instead of creating another. Mark a goal
complete only after focused verification and execution review pass. Do not use
project-local Markdown goal files for Codex-native goal state; the
`.claude/teamwork-goals/` runtime is Claude-plugin-specific.

Default budget when unspecified:

- Maximum 3 optimization iterations.
- Stop after 2 consecutive iterations with no evidence delta.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing credentials, unavailable required resources, or ambiguous product
  intent that affects behavior.

During autonomous goal mode, do not ask the user for ordinary implementation
choices, missing non-critical details, or next-step permission. Convert safe
missing details into explicit assumptions and continue. Ask only for destructive
risk, auth/credentials, missing required external resources, sacred-boundary
conflict, or ambiguity that changes public behavior, protected contracts,
architecture, or user intent.

Controller loop:

1. Initialize: state goal, assumptions, sacred boundaries, mutable scope,
   verification target, and budget.
2. Research/discuss only if causes or options are unclear: use
   `teamwork-design` with `mode: research`.
3. Plan: use `teamwork-design` with `mode: plan`.
4. Review the plan: use `teamwork-review` with `mode: plan`; revise until
   pass or blocked.
5. Execute: use `teamwork-execute` on the accepted plan.
6. Verify: run focused checks first and collect real evidence.
7. Review execution: use `teamwork-review` with `mode: execution`.
8. Decide: accept only if verification and execution review pass; otherwise
   continue with a new hypothesis, stop at budget, or report a blocker.

Goal mode does not let one executor self-declare completion. Every completion
claim must pass execution review.

Autonomous iteration discipline:

- Treat the goal as concrete deliverables plus verification targets.
- Read direct evidence before each decision; do not rely on summaries.
- If verification fails, identify the evidence delta, choose the next smallest
  hypothesis, and continue within budget.
- If there is no evidence delta for 2 consecutive iterations, stop with a
  blocker or budget/no-progress conclusion.
- In Claude Code plugin mode, emit the configured completion promise only after
  verification and execution review pass, and include the required structured
  completion audit in the same final assistant message.

Completion audit format for Claude Code plugin auto-completion:

```text
<completion_audit>
<requirements_mapping>map each requirement to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

The `review_verdict` must be exactly `pass` or `pass-with-notes`. The Stop hook
must not auto-complete on the completion promise alone.

## Shared Contract

All subskills follow the same contract:

- State assumptions and sacred boundaries before committing to behavior.
- Read direct evidence: files, diffs, logs, tests, artifacts, or command output.
- Separate `observed`, `inferred`, and `claimed` evidence before important
  decisions.
- Prefer the smallest producer-side fix over downstream cleanup.
- Keep mutable implementation details separate from protected principles,
  architecture, and public contracts.
- Use independent agents when subtasks are separable or a second view reduces
  risk; otherwise run distinct local passes.
- Preserve dissent in the final verdict instead of smoothing it away.
- Stop on verified success, budget exhaustion, repeated no-progress,
  unresolvable blocker, or sacred-boundary conflict.

## Route Output

After routing, report the selected subskill and why:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to user intent>
Mode: <research | plan | execution | goal, when applicable>
```

Then follow that subskill's instructions directly.

For `mode: goal`, end with:

```text
Goal:
- ...

Iterations:
- <n>: research/plan/execute/review summary

Verification:
- <command/artifact/check>: <result>

Review:
- Plan review: <verdict>
- Execution review: <verdict and dissent>

Completion Audit:
- requirements_mapping: <evidence map>
- verification_evidence: <commands/artifacts/inspection>
- review_verdict: <pass | pass-with-notes>
- dissent: <none or residual risk>

Codex Goal State:
- native goal created | continued | not used
- completion marked only after verification + execution review

Unresolved:
- <none or blockers>

Conclusion:
- accept | blocked | budget exhausted | stopped
```
