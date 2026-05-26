# Dispatch Policy

Use when deciding whether to dispatch subagents or when reviewing dispatch
economics. Keep prompt details in `subagent-prompt-contract.md` and packet
schemas in `subagent-packets.md`.

## Stage-Routed Proactive Dispatch

Teamwork stages authorize their own non-destructive subagent dispatch. Do not
wait for the user, `Goal Proposal`, `Dispatch Guidance:`, or durable
`Subagent Routing` to name every track.

- Research: Explorer tracks for 2+ separable evidence questions.
- Plan: Designer for ambiguous choices; Judge for durable, high-risk,
  ambiguous, delegated, or goal-mode plans.
- Execute: Worker split from accepted steps, files, components, and ownership.
- Review: fresh-context Reviewer for non-trivial execution, high-risk diffs, or
  acceptance; same-context self-review cannot accept non-lightweight work.
- Goal: rerun the stage dispatch decision on each failed attempt.

Plans record expected routing. Execution records actual dispatch. Review checks
both.

## Subagent Tool Discovery Gate

Before serializing a second independent track, delivering a durable/high-risk
plan, or accepting non-lightweight work: use active `spawn_agent`; otherwise,
if `tool_search` exists, search `multi-agent spawn_agent`; only failed discovery
proves unavailable tools. Omit `model` normally so subagents inherit the parent;
record conceptual role, model class, native fields, and intentional inheritance.
When required dispatch is skipped, write:

```text
Dispatch Exception: <single-track | tight-critical-path | overlapping-ownership | higher-context-cost | tool-unavailable-after-discovery | user-opt-out>
```

For non-lightweight review or acceptance, the only valid exceptions are
`tool-unavailable-after-discovery` or `user-opt-out`; the verdict must be
marked `unreviewed`.

## Roles

Explorer investigates; Designer resolves tradeoffs; Judge reviews plans; Worker
implements owned scope; Reviewer checks diffs, tests, logs, and artifacts.

## Dispatch Economics

- Explorer/Reviewer: default max 3 parallel unless the user gives a larger
  budget; keep raw evidence out of the main context.
- Worker: no fixed numeric cap; dispatch one per independent owned track when
  elapsed time or isolation improves. Before dispatching more than 3 Workers,
  state ownership map, integration order, verification, and why parallel is
  cheaper than serial.
- Use batch or worktree isolation when ownership is uncertain or merge cost may
  dominate.
- If not dispatching, state why local execution is cheaper or safer. For
  non-lightweight review, unavailable tools or explicit user opt-out are the
  only acceptable reasons to skip a fresh Reviewer; mark acceptance unreviewed.
- CodeGraph may replace Explorer only for a single structural code question.
  Multi-domain research still applies the discovery gate and stage dispatch.

## Role Profiles

Use model class as the stable policy and translate it through Codex Model
Mapping at dispatch time. Prefer fewer, stronger models over fragile cheap
defaults.

- Explorer: `agent_type:"explorer"`, model class `balanced` by default;
  `cheap-fast` only for narrow read-only evidence; context
  `condensed-evidence-only`.
- Designer: `agent_type:"default"`, `balanced`; use `frontier` for architecture,
  public behavior, data contracts, or unfamiliar APIs.
- Judge: `agent_type:"default"`, model class `frontier`, high reasoning,
  `fresh-context-review`, read-only.
- Worker: `agent_type:"worker"`, `coding` or `inherited`; use `frontier` for
  cross-module, high-risk, security, or public behavior changes.
- Reviewer: `agent_type:"default"`, model class `frontier`, high reasoning,
  `fresh-context-review`, read-only.

Do not use `cheap-fast` for Judge, Reviewer, architecture Designer, public
behavior changes, failed-goal adequacy decisions, or non-mechanical Worker
implementation.

## Codex Mapping

- Explorer -> `agent_type:"explorer"`.
- Worker -> `agent_type:"worker"`.
- Designer, Judge, Reviewer -> `agent_type:"default"` with role in prompt.
- `fast` -> `reasoning_effort:"low"`.
- `standard` -> `reasoning_effort:"medium"`.
- `high reasoning` -> `reasoning_effort:"high"`.

## Codex Model Mapping

- `cheap-fast` -> `gpt-5.4-mini`; only read-only, narrow, verifiable output.
- `balanced` -> `gpt-5.4`.
- `coding` -> `gpt-5.3-codex` or inherited from a strong coding parent.
- `frontier` -> `gpt-5.5`.
- `inherited` -> omit `model`; record that inheritance is intentional.

Do not combine `fork_context:true` with `agent_type`, `model`, or
`reasoning_effort`; full-history forks inherit parent routing. Codex has no
native `judge`, `reviewer`, or `designer` agent types.

Evaluate the split before implementation steps. Do not wait for a proposal or plan to explicitly name every track; stage contracts authorize dispatch when economics and ownership are clear.
