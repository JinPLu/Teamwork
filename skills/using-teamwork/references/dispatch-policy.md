# Dispatch Policy

Use when deciding whether and how to dispatch subagents. Native field mapping
lives in `platform-dispatch-mapping.md`; swarm orchestration lives in
`workflow-orchestration.md`.

## Stage-Routed Proactive Dispatch

When the active platform or loaded instructions authorize subagents, use
parallel subagents when non-lightweight independent tracks exist by default.
Do not wait for `Goal Proposal`, `Dispatch Guidance:`, or durable `Subagent
Routing` to explicitly name every track. On Codex, a project or global standing
request can authorize this; otherwise keep work local and record the rationale.

- Exploration: Explorer for codebase orientation, artifacts, or local evidence
  beyond a quick literal read.
- Research: Explorer tracks for evidence, stale assumptions, option comparison,
  or failure analysis.
- Plan: Designer for ambiguity; Judge for durable, risky, delegated, or
  goal-mode plans.
- Execute: Worker split from accepted steps, files, components, and ownership.
- Review: fresh Reviewer for non-trivial execution, high-risk diffs, or
  acceptance; self-review cannot accept non-lightweight work.
- Goal: rerun stage dispatch after failures for independent exploration,
  hypotheses, verification, or review.
- Workflow-class: escalate to `workflow-orchestration.md` for many agents,
  resumable state, cross-checking, or reusable phases.

Plans may record expected routing. Execution records actual dispatch. Review
checks routing when it affects acceptance.

## Lifecycle And Closure

Subagents are bounded tasks, not ongoing owners. A dispatched subagent returns
its packet, then stops. It must not monitor, reopen scope, chain new subagents,
wait for final acceptance, or keep working after `done`, `done_with_concerns`,
`blocked`, `needs_context`, or a Reviewer/Judge verdict.

The main agent owns closure. Use dispatch status `dispatched -> returned ->
closed`, `blocked`, or `abandoned-after-discovery`. After integrating each
packet, record Closure Evidence in the Actual Dispatch Log. Before final
response, no delegated track may remain open; if one cannot close, report the
blocker and do not claim completion.

## Subagent Tool Discovery Gate

Before claiming subagents are unavailable, confirm authorization, then use the
active platform tool (`spawn_agent` on Codex, `Task` on Cursor or Claude Code);
on Codex, search `multi-agent spawn_agent` with `tool_search` when available.
Only failed discovery proves unavailability. For bounded Codex role dispatch,
set an explicit Role Profile model; use `inherited` only for full-history forks,
parent-model continuity, or user model intent. Record role, model class, fields,
and pin/inherit reason.

When a dispatch decision matters but dispatch is skipped, write:

```text
Dispatch Exception: <single-track | tight-critical-path | overlapping-ownership | higher-context-cost | tool-unavailable-after-discovery | authorization-missing | user-opt-out>
```

For non-lightweight review or acceptance, valid exceptions are only
`tool-unavailable-after-discovery`, `authorization-missing`, or `user-opt-out`;
the verdict is `unreviewed`.

## Roles

Teamwork has five conceptual roles; Deep Judge/Reviewer are severity profiles.
Explorer gathers evidence. Designer decides. Judge reviews plans. Worker
implements owned slices. Reviewer checks completed work.

## Dispatch Economics

- Explorer/Reviewer: default max 3 parallel unless budget; keep raw evidence
  out of the main context.
- Worker: no fixed numeric cap; dispatch per track when time or isolation
  helps. Before dispatching more than 3 Workers, state ownership map,
  integration order, verification, and why parallel beats serial.
- Use batch or worktree isolation when ownership or merge cost is unclear.
- If skipping non-lightweight dispatch, state why local execution is cheaper or safer
  with `Dispatch Exception:`.
- CodeGraph may replace Explorer for one structural code question.

## Role Profiles

Use model class as stable policy and translate through platform Model Mapping.
Prefer strong models. Codex `performance-first` uses `gpt-5.5`: medium for
routine Explorer/Designer/Worker, high for Judge/Reviewer, and xhigh only for
Deep Judge/Reviewer. `cost-first` may downshift routine roles but never
high-risk review.

- Explorer: model class `balanced` by default; use `frontier` for broad,
  ambiguous, unfamiliar, or high-risk evidence. `cheap-fast` is opt-in only for
  trivial read-only evidence under explicit latency/quota pressure.
- Designer: `balanced`; use `frontier` for architecture, public behavior,
  contracts, or APIs; read-only.
- Judge: model class `frontier`, reasoning `high`; use Deep Judge `xhigh` for
  failed-goal, security, destructive-risk, public-contract, or release
  adequacy; read-only.
- Worker: `coding` or `inherited`; use `frontier` for cross-module, security,
  or public behavior; context `owned-files-only`.
- Reviewer: model class `frontier`, reasoning `high`; use Deep Reviewer
  `xhigh` for security, destructive-risk, public-contract, failed-goal, or
  release acceptance. Use `balanced` only for mechanical diffs; read-only.

Do not use `cheap-fast` for normal Pro/20x Codex workflows, performance-first
projects, Judge, Reviewer, architecture Designer, public behavior, failed-goal
adequacy decisions, or non-mechanical Worker implementation.

Evaluate the split before implementation steps. Stage contracts authorize
dispatch when economics and ownership are clear.
