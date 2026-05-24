---
name: teamwork
description: Use when routing a multi-step or evidence-sensitive request through the Teamwork workflow — maps user intent to the right stage skill and defines shared contracts for evidence, subagents, progress anchors, and artifacts.
---

# Teamwork

This is the public router for the package. Use it as a workflow-preference layer
on top of Claude Code, Codex, or Cursor: preserve the platform's native coding
capability, then add Teamwork discipline only when evidence, coordination,
review, or autonomous convergence improves the result. Autonomous convergence is
handled by the dedicated `teamwork-goal` subskill.

In Codex, treat Teamwork as a thin progress layer over native planning,
subagents, reviews, goals, sandbox approvals, and skills. Do not make the main
thread maintain long process ledgers. Anchor the current work to the smallest
state that lets the next decision move forward: active objective, accepted plan
or execution memo, verification target, and review result when needed.

The package preserves the original discipline:

- **Behavior guardrails**: assumptions explicit, simplicity first, surgical
  scope, goal-driven verification, and evidence over confidence.
- **Roundtable-style workflow**: role separation, multi-agent discussion when
  useful, independent review, dissent preservation, and budgeted stopping.
- **No full roundtable infrastructure**: do not import model registries,
  pricing caches, dispatch scripts, or thread ledgers unless the user asks.

## Behavior Guardrails

Apply these guardrails whenever a Teamwork stage is active. For native-flow
tasks, use them as a quick mental check without adding ceremony.

- **Assumptions before action**: state assumptions that affect behavior, scope,
  verification, public contracts, data contracts, architecture, protected
  claims, or user constraints. If a risky assumption would change one of those
  boundaries, stop and ask or route to research instead of guessing.
- **Simplicity first**: choose the smallest sufficient path that solves the
  user's goal. Do not add speculative abstraction, configurability, new
  workflow stages, or broad refactors unless direct evidence shows they are
  needed.
- **Surgical scope**: every planned change, edit, or recommendation must trace
  to the goal. Avoid opportunistic cleanup, formatting churn, neighboring
  refactors, and rewrites. Remove only code or instructions made unused by the
  current change.
- **Goal-driven verification**: translate the task into a concrete success
  condition before declaring it done. For bugs, observe or reproduce the failure
  before fixing when feasible. Run focused verification first, broaden only when
  shared or public behavior is touched, and report any verification gap.
- **Evidence over confidence**: confidence is not evidence. Treat names,
  comments, README prose, summaries, labels such as `latest` or `v2`, and tool
  summaries as claims until corroborated by source, diff, tests, logs, command
  output, artifacts, or primary external evidence.

## Activation Tiers

| Tier | Use when | Planning | Review | Subagents |
|---|---|---|---|---|
| Native flow | Simple, local, low-risk work | None or native task list | Normal verification | Not needed |
| Lightweight Teamwork | Multi-step but bounded work | Concise chat/native checklist | Distinct self-review or focused review | Optional |
| Durable artifact | Cross-agent, cross-turn, high-risk, ambiguous, or explicitly planned work | Markdown artifact under `docs/teamwork/plans/` | Plan/execution review against artifact | Optional but documented if used |
| Goal mode | Explicit autonomous convergence | Mandatory durable artifact and runtime plan anchor | Mandatory passing review/checkpoint | As useful within budget |

Durable artifacts are mandatory for goal mode and high-risk or cross-agent work,
but native flow remains the default for simple Claude Code tasks.

Use artifact directories by purpose:

- `docs/teamwork/research/`: reusable investigation findings.
- `docs/teamwork/plans/`: execution memo and active plan anchor.
- `docs/teamwork/reports/`: final task conclusion for non-trivial, cross-turn,
  cross-agent, goal-mode, or explicitly requested work.

Do not create artifacts just to record every thought. For artifact triggers,
full-text research retrieval, and goal rolling reports, read
`skills/teamwork/references/artifact-protocol.md`.

## Subagent Collaboration Model

Subagents are a tool for independent context, parallel evidence collection,
isolated execution, or fresh review. They are not required for every Teamwork
request. The main agent owns scope, decomposition, synthesis, conflict
resolution, verification, progress anchoring, and final acceptance. Subagents
provide bounded work products:

- Explorer: read-heavy independent investigation with condensed evidence.
- Designer: ambiguous requirements, architecture tradeoffs, cross-module
  solution design, and product behavior choices before execution planning.
- Judge: fresh-context plan review before execution.
- Worker: implementation for an accepted plan with exact file ownership or
  worktree isolation.
- Reviewer: fresh-context execution review against diffs, tests, logs, and
  artifacts.

When Teamwork is active, treat the user as granting standing authorization for
automatic subagent delegation on independent non-lightweight tracks. Do not ask
for extra "fan out" confirmation. Ask only when dispatch would need new
credentials, destructive actions, unclear write ownership, or another
approval-gated capability.

For non-lightweight work, first split the next decision into independent tracks.
Fan out when 2 or more tracks can run without blocking the main agent's
immediate next step. Good fan-out has a specific question, bounded evidence
scope, expected return format, and non-overlapping write ownership when edits
are allowed. Dispatch useful Explorers, Workers, or Reviewers early, then keep
working locally on non-overlapping tasks. Wait only when the next local step
depends on a subagent result.

Do not fan out merely for ceremony, duplicate another agent's unresolved work,
delegate the critical-path blocker, or give writing agents overlapping files.
Keep the work local when continuity matters more than independent context or
when coordination overhead exceeds the value of parallelism.

## Subagent Routing Policy

Use subagents only when independent context, parallel evidence, isolated
execution, or fresh review improves correctness or speed. Name the conceptual
role, scope, model tier, context strategy, order, and why. `fast`, `standard`,
and `high reasoning` are capability tiers, not fixed model IDs. For detailed
role mapping, Codex Dispatch Mapping, `fork_context:true` limits, and the fact
that Designer/Judge/Reviewer are conceptual roles, read
`skills/teamwork/references/subagent-routing.md`.

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

- Use local repository evidence first to establish the actual project state,
  active code paths, current progress, and mainline constraints.
- For non-trivial research, use external calibration as part of the evidence
  process, not merely as a last-resort fallback. Use MCP or web when model or
  prompt work, VLM/video understanding, platform APIs, dependencies, upstream
  bugs, performance, unfamiliar frameworks, or repeated failures could affect
  the answer.
- Prefer official/current primary sources, papers, release notes, and upstream
  issue threads. If external access is unavailable, record that limitation
  instead of silently relying on local guesses.
- Fan out subagents only for independent read-heavy research, design, judge, or
  review tracks that improve reliability or speed without blocking the main
  agent's next step. Writing subagents need exact file ownership or worktree
  isolation.
- Ask subagents for condensed evidence and verdicts, not raw log dumps.
- Default to at most 3 parallel research/review subagents unless the user gives
  a larger budget.
- The main agent owns synthesis, conflict resolution, verification, and the
  final decision even when subagents are used.

## Progress Anchors And Artifacts

`update_plan` and other visible plan widgets are transient UI-only checklist
state. They help show progress during a turn, but they are not the execution
specification, review target, or durable evidence for artifact-backed plans.

A durable Markdown plan artifact is required for cross-agent execution,
cross-turn work, high-risk or ambiguous changes, and all goal-mode execution.
Use it as an execution memo: concise objective, scope, steps, verification,
stop rules, and handoffs. Default path:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

For lightweight work, a concise chat plan or native task list is enough when it
captures scope, verification, and stop conditions. Do not create repository plan
files merely for ceremony.

The durable artifact is shared across Cursor, Claude Code, and Codex because it
is plain Markdown in the repo, not Codex native goal state and not Claude
`.claude/teamwork-goals/` runtime state.

Write a final report only when the result itself needs to be reusable later.
Goal mode additionally keeps a rolling report for every iteration:

```text
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

## Codex Native Integration

When running in Codex, use native platform capabilities instead of emulating
roundtable infrastructure or Claude Stop-hook behavior:

- Use `update_plan` only as a transient UI-only checklist for visible progress.
  It must not be the only execution plan or review artifact when a durable
  artifact is required.
- Use durable Markdown plan artifacts for goal-mode, cross-agent, cross-turn,
  high-risk, or ambiguous execution plans, with the default path
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- Use Codex goals only for explicit autonomous convergence requests or an
  existing active goal. Do not create a goal for ordinary research, planning,
  review, or one-shot execution.
- Use Codex subagents for independent Explorer, Designer, Judge, Worker, or
  Reviewer tracks only when the track can run in parallel or fresh context
  materially improves the result. Dispatch focused prompts, continue local
  non-overlapping work while they run, wait only when blocked on their result,
  synthesize conflicts locally, and close agents that are no longer needed.
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
| Research options, compare approaches, discuss tradeoffs, gather evidence | `teamwork-research` | `skills/teamwork-research/SKILL.md` |
| Convert a chosen direction into an executable implementation plan | `teamwork-plan` | `skills/teamwork-plan/SKILL.md` |
| Execute an accepted plan with minimal edits and verification | `teamwork-execute` | `skills/teamwork-execute/SKILL.md` |
| plan-review: review a plan before execution | `teamwork-review` with `mode: plan` | `skills/teamwork-review/SKILL.md` |
| execution-review: review diffs, artifacts, tests, and results after execution | `teamwork-review` with `mode: execution` | `skills/teamwork-review/SKILL.md` |
| Iterate autonomously until verified success, budget exhaustion, or blocker | `teamwork-goal` with `mode: goal` | `skills/teamwork-goal/SKILL.md` |

Do not create separate plan-review and execution-review subskills. The single
`teamwork-review` subskill has two explicit modes so reviewer orchestration
stays shared while the rubric changes by review target.

Research and planning are separate subskills. `teamwork-research` owns evidence
and research artifacts; `teamwork-plan` owns executable implementation plans.
Autonomous convergence belongs to the dedicated `teamwork-goal` subskill.

## Routing Rules

Use the narrowest subskill that adds value:

- If the task is simple, local, low-risk, or answerable directly, stay in native
  flow and continue normally.
- If the user asks "what should we do?", "research", "compare", "discuss", or
  "find options", route to `teamwork-research`.
- If the user asks for a plan, or the work is complex enough that a plan reduces
  risk, route to `teamwork-plan`.
- If the user gives an accepted plan or says to implement/execute, route to
  `teamwork-execute`.
- If the user asks to review a proposed plan, route to
  `teamwork-review` with `mode: plan`.
- If the user asks to review a diff, patch, artifacts, test result, or completed
  execution, route to `teamwork-review` with `mode: execution`.
- If the user asks to "run until it passes", "iterate until convergence",
  "keep going until done", or gives a verifiable target plus budget, route to
  `teamwork-goal` with `mode: goal`.

## Shared Contract

All Teamwork stages follow the same contract:

- Apply the Behavior Guardrails before stage-specific steps.
- State assumptions and sacred boundaries before committing to behavior when
  they affect the work.
- Read direct evidence: files, diffs, logs, tests, artifacts, or command output.
- Separate `observed`, `inferred`, and `claimed` evidence before important
  decisions.
- Prefer the smallest producer-side fix over downstream cleanup.
- Keep mutable implementation details separate from protected principles,
  architecture, and public contracts.
- Use independent agents only when subtasks are separable, non-overlapping, and
  useful in parallel or when a second view reduces real risk; otherwise run
  distinct local passes.
- Preserve dissent in the final verdict instead of smoothing it away.
- Stop on verified success, budget exhaustion, repeated no-progress,
  unresolvable blocker, or sacred-boundary conflict.

## Route Output

When routing to a Teamwork stage, report the selected subskill and why:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to user intent>
Mode: <research | plan | execution | goal, when applicable>
```

For native-flow tasks, do not emit a route banner; continue normally.
