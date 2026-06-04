# Dispatch Policy

Use when deciding whether and how to dispatch subagents. Native field mapping
lives in `platform-dispatch-mapping.md`; large swarm orchestration lives in
`workflow-orchestration.md`.

## Stage-Routed Proactive Dispatch
When the active platform or loaded instructions authorize subagents, use
parallel subagents when non-lightweight independent tracks exist by default. Do not
wait for `Goal Proposal`, `Dispatch Guidance:`, or durable `Subagent Routing`
to name every track. On Codex, a project or global standing instruction can
satisfy the explicit request; otherwise keep local and record the rationale.

- Exploration: Explorer for codebase orientation, artifact lookup, or local
  evidence beyond a quick literal read.
- Research: Explorer tracks for evidence, stale assumptions, option comparison,
  or failure analysis.
- Plan: Designer for ambiguity; Judge for durable, risky, delegated, or
  goal-mode plans.
- Execute: Worker split from accepted steps, files, components, and ownership.
- Review: fresh-context Reviewer for non-trivial execution, high-risk diffs, or
  acceptance; self-review cannot accept non-lightweight work.
- Goal: rerun stage dispatch on failures; use sidecar agents for independent
  exploration, hypothesis testing, verification, or review.
- Workflow-class: escalate to `workflow-orchestration.md` when the task needs
  many agents, resumable state, cross-checking, or reusable phases.

Plans may record expected routing. Execution records actual dispatch when
subagents run. Review checks routing when it affects acceptance.

## Lifecycle And Closure

Subagents are bounded tasks, not ongoing owners. A dispatched subagent returns
its required packet, then stops. It must not continue monitoring, reopen scope,
chain new subagents, wait for final acceptance, or keep working after
`done`, `done_with_concerns`, `blocked`, `needs_context`, or a Reviewer/Judge
verdict.

The main agent owns closure. Use dispatch status `dispatched -> returned ->
closed` for normal completion, `blocked` when the packet cannot satisfy the
mission, and `abandoned-after-discovery` when dispatch was attempted but no
usable subagent/tool was available. After integrating each returned packet,
record Closure Evidence in the Actual Dispatch Log. Before final response, no
delegated track may remain open; if a track cannot close, report the blocker
and do not claim completion.

## Subagent Tool Discovery Gate

Before claiming subagents are unavailable: confirm authorization, then use the
active platform subagent tool (`spawn_agent` on Codex, `Task` on Cursor or
Claude Code); on Codex, search `multi-agent spawn_agent` with `tool_search`
when available. Only failed discovery proves unavailable tools. For bounded
Codex role dispatch, set an explicit Role Profile model; use `inherited` only
for full-history forks, parent-model continuity, or user model intent. Record
role, model class, fields, and pin/inherit reason when dispatch runs.
When a dispatch decision matters but dispatch is skipped, write:

```text
Dispatch Exception: <single-track | tight-critical-path | overlapping-ownership | higher-context-cost | tool-unavailable-after-discovery | authorization-missing | user-opt-out>
```

For non-lightweight review or acceptance, the only valid exceptions are
`tool-unavailable-after-discovery`, `authorization-missing`, or `user-opt-out`;
the verdict is `unreviewed`.

## Roles

Explorer investigates; Designer decides; Judge reviews plans; Worker
implements; Reviewer checks diffs and tests.

## Dispatch Economics

- Explorer/Reviewer: default max 3 parallel unless budget;
  keep raw evidence out of the main context.
- Worker: no fixed numeric cap; dispatch per track when time or isolation
  improves. Before dispatching more than 3 Workers, state ownership map,
  integration order, verification, and why parallel beats serial.
- Use batch or worktree isolation when ownership or merge cost is unclear.
- If not dispatching non-lightweight work, state why local execution is cheaper or safer
  with `Dispatch Exception:`. For review, unavailable tools, missing
  authorization, or user opt-out are valid exceptions; mark unreviewed.
- CodeGraph may replace Explorer for one structural code question.
  Multi-domain research still applies discovery gate and stage dispatch.

## Role Profiles

Use model class as stable policy; translate through active platform Model
Mapping. Prefer fewer, stronger models. On Codex, `performance-first` init
maps normal role classes to `gpt-5.5` and high reasoning; `cost-first`
keeps lower routine classes but never downshifts Judge, Reviewer, high-risk,
public, or failed-goal adequacy work.

- Explorer: model class `balanced` by default; use `frontier` for broad,
  ambiguous, unfamiliar, or high-risk evidence. `cheap-fast` is opt-in only for
  trivial read-only evidence under explicit latency/quota pressure; reasoning
  `fast` or `standard`; context `condensed-evidence-only`.
- Designer: `balanced`; use `frontier` for architecture, public behavior,
  contracts, or APIs; reasoning `standard` or `high`; read-only.
- Judge: model class `frontier`, reasoning `high`; context
  `fresh-context-review`; read-only.
- Worker: `coding` or `inherited`; use `frontier` for cross-module, security,
  or public behavior; reasoning `standard` or `high`; context
  `owned-files-only`.
- Reviewer: model class `frontier` by default, reasoning `high`; use
  `balanced` only for mechanical diffs; context `fresh-context-review`;
  read-only.

Do not use `cheap-fast` for normal Pro/20x Codex workflows, performance-first
projects, Judge, Reviewer, architecture Designer, public behavior, failed-goal
adequacy decisions, or non-mechanical Worker implementation.

Evaluate the split before implementation steps. Do not wait for a proposal or plan to explicitly name every track; stage contracts authorize dispatch when economics and ownership are clear.
