# Dispatch Policy

Use when dispatching subagents or reviewing dispatch economics. Keep prompts in
`subagent-prompt-contract.md`; keep packet schemas in `subagent-packets.md`.

## Stage-Routed Proactive Dispatch

Teamwork activation is standing authorization for non-destructive stage
dispatch. For non-lightweight work, parallel subagents are the default execution substrate when independent tracks exist. Do not wait for the user to say "fan out subagents", or for `Goal Proposal`, `Dispatch Guidance:`, or
durable `Subagent Routing` to explicitly name every track.

- Research: Explorer tracks for 2+ separable evidence questions.
- Plan: Designer for ambiguity; Judge for durable, risky, delegated, or
  goal-mode plans.
- Execute: Worker split from accepted steps, files, components, and ownership.
- Review: fresh-context Reviewer for non-trivial execution, high-risk diffs, or
  acceptance; self-review cannot accept non-lightweight work.
- Goal: rerun stage dispatch on each failed attempt.

Plans record expected routing. Execution records actual dispatch. Review checks
both. If non-lightweight work stays serial, record the allowed exception.

## Subagent Tool Discovery Gate

Before serializing a second independent track, delivering a durable/high-risk
plan, or accepting non-lightweight work: use the active platform subagent tool
(`spawn_agent` on Codex, `Task` on Cursor or Claude Code); on Codex, if
`tool_search` exists, search `multi-agent spawn_agent` before claiming
unavailability. Only failed discovery proves unavailable tools. For bounded
Codex role dispatch, set an explicit Role Profile model; use `inherited` only
for full-history forks, parent-model continuity, or explicit user model intent.
Record role, model class, native fields, and pin/inherit reason.
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

- Explorer/Reviewer: default max 3 parallel unless user gives larger budget;
  keep raw evidence out of the main context.
- Worker: no fixed numeric cap; dispatch per independent owned track when
  elapsed time or isolation improves. Before dispatching more than 3 Workers,
  state ownership map, integration order, verification, and why parallel is
  cheaper than serial.
- Use batch or worktree isolation when ownership is unclear or merge cost may
  dominate.
- If not dispatching, state why local execution is cheaper or safer. For
  non-lightweight review, unavailable tools or explicit user opt-out are the
  only acceptable reasons to skip a fresh Reviewer; mark acceptance unreviewed.
- CodeGraph may replace Explorer for one structural code question.
  Multi-domain research still applies discovery gate and stage dispatch.

## Role Profiles

Use model class as stable policy; translate through active platform Model
Mapping. Prefer fewer, stronger models over fragile cheap defaults.

- Explorer: model class `balanced` by default; use `frontier` for broad,
  ambiguous, unfamiliar, or high-risk evidence. `cheap-fast` is opt-in only for
  trivial read-only evidence under explicit latency/quota pressure; reasoning
  `fast` or `standard`; context
  `condensed-evidence-only`.
- Designer: `balanced`; use `frontier` for architecture, public behavior, data
  contracts, or unfamiliar APIs; reasoning `standard` or `high`; read-only.
- Judge: model class `frontier`, reasoning `high`; context
  `fresh-context-review`; read-only.
- Worker: `coding` or `inherited`; use `frontier` for cross-module, high-risk,
  security, or public behavior changes; reasoning `standard` or `high`; context
  `owned-files-only`.
- Reviewer: model class `frontier` by default, reasoning `high`; use
  `balanced` only for low-risk mechanical diffs; context `fresh-context-review`;
  read-only.

Do not use `cheap-fast` for normal Pro/20x Codex workflows, Judge, Reviewer,
architecture Designer, public behavior changes, failed-goal adequacy decisions,
or non-mechanical Worker implementation.

## Platform Dispatch Fields

- Codex: `agent_type`, `model`, `reasoning_effort`, `fork_context`.
- Cursor: `subagent_type`, `model`; no `reasoning_effort` or `fork_context`.
- Claude Code: `subagent_type` (matches a user-defined agent name under
  `~/.claude/agents/` or `general-purpose`); `model` is fixed on the agent
  definition, not per-`Task`-call.
- All platforms: conceptual role, model class, and context strategy stay the
  same; only native field translation changes.

## Codex Mapping

- Prefer Teamwork custom agents under `.codex/agents/` or `~/.codex/agents/`:
  Explorer -> `agent_type:"teamwork_explorer"`, Worker ->
  `agent_type:"teamwork_worker"`, Designer -> `agent_type:"teamwork_designer"`,
  Judge -> `agent_type:"teamwork_judge"`, Reviewer ->
  `agent_type:"teamwork_reviewer"`.
- Fallback when custom agents are unavailable: Explorer -> `agent_type:"explorer"`;
  Worker -> `agent_type:"worker"`; Designer, Judge, Reviewer ->
  `agent_type:"default"` with role in prompt.
- `fast` -> `reasoning_effort:"low"`.
- `standard` -> `reasoning_effort:"medium"`.
- `high reasoning` -> `reasoning_effort:"high"`.

## Codex Model Mapping

- `cheap-fast` -> `gpt-5.4-mini`; opt-in only for trivial read-only,
  verifiable output under explicit latency/quota pressure.
- `balanced` -> `gpt-5.4`.
- `coding` -> `gpt-5.3-codex`; use `frontier` when task risk or breadth
  matters more than credit efficiency.
- `frontier` -> `gpt-5.5`.
- `inherited` -> omit `model`; record why inheritance beats Role Profile
  model.

## Codex Native Field Presets

Teamwork custom agents pin model and reasoning. For built-in fallbacks, Role
Profile selection is a clear reason to set Codex's optional `model`. Do not let
Explorer or Worker inherit a `frontier` parent by accident; inheritance is only
for full-history forks, parent-model continuity, or explicit user model intent.

- Explorer default: `agent_type:"explorer"`, `model:"gpt-5.4"`, `reasoning_effort:"medium"`; escalated uses `model:"gpt-5.5"`, `reasoning_effort:"high"`.
- Worker default: `agent_type:"worker"`, `model:"gpt-5.3-codex"`, `reasoning_effort:"medium"`; escalated uses `model:"gpt-5.5"`, `reasoning_effort:"high"`.
- Designer default: `agent_type:"default"`, `model:"gpt-5.4"`, `reasoning_effort:"medium"`; prompt says `Conceptual Role: Designer`.
- Judge default: `agent_type:"default"`, `model:"gpt-5.5"`, `reasoning_effort:"high"`; prompt says `Conceptual Role: Judge`.
- Reviewer default: `agent_type:"default"`, `model:"gpt-5.5"`, `reasoning_effort:"high"`; `gpt-5.4` only for low-risk mechanical diffs.

Do not combine `fork_context:true` with `agent_type`, `model`, or
`reasoning_effort`; full-history forks inherit parent routing. Without custom
agents, Codex has no native `judge`, `reviewer`, or `designer` types, so they
appear as `default` subagents unless prompt/logs show conceptual role.

## Cursor Mapping

- Explorer -> `subagent_type:"explore"`.
- Worker -> `subagent_type:"generalPurpose"`; use `shell` for shell-only
  isolated tracks.
- Reviewer -> `subagent_type:"code-reviewer"`.
- CI failure investigation -> `subagent_type:"ci-investigator"` when the track
  is a single failing check.
- Designer, Judge -> `subagent_type:"generalPurpose"` with role in prompt.
- Cursor has no native `judge`, `reviewer`, or `designer` subagent types.

## Cursor Task Parameters

- `readonly: true` -> Explorer, Judge, and Reviewer by default.
- `run_in_background: true` -> long Explorer or Worker tracks in Multitask Mode.
- `resume: <id>` -> continue the same Reviewer or Explorer across goal iterations.
- `resume: "self"` -> `full-history-fork` on Cursor.
- `subagent_type: "best-of-n-runner"` -> parallel Worker experiments with worktree
  isolation.
- `subagent_type: "ci-investigator"` -> single failing CI check during goal-mode
  failure analysis.
- Browser or UI verification -> use browser automation when verification needs
  inspected behavior.

## Cursor Model Mapping

Use only models listed in the active `Task` tool schema; prefer the latest
version when the user did not request a specific model.

- `cheap-fast` -> `composer-2.5-fast`; opt-in only for trivial read-only,
  verifiable output under explicit latency/quota pressure.
- `balanced` -> `gpt-5.5-medium` when listed; otherwise strongest
  non-frontier model listed in the active schema.
- `coding` -> `gpt-5.5-medium` when listed; otherwise use the strongest coding
  or non-frontier model listed in the active schema.
- `frontier` -> `claude-opus-4-7-thinking-high`.
- `inherited` -> omit `model`; record that inheritance is intentional.

## Claude Code Mapping

Claude Code subagents are user-defined under `~/.claude/agents/`. Map
conceptual roles to the agent `name` referenced by `Task`'s `subagent_type`.
When a specialized agent is not configured, fall back to `general-purpose` and
state the conceptual role in the prompt.

- Explorer -> `subagent_type:"explore"` if defined, else `general-purpose`.
- Worker -> `subagent_type:"general-purpose"` or a user-defined `worker` agent.
- Reviewer -> `subagent_type:"code-reviewer"` if defined, else
  `general-purpose` with Reviewer role in the prompt.
- Designer, Judge -> `subagent_type:"general-purpose"` with role in prompt.
- Claude Code has no native `judge`, `reviewer`, or `designer` agent types out
  of the box; users may define them.

## Claude Code Task Parameters

- `subagent_type` -> matches an agent name in `~/.claude/agents/` (user scope)
  or `.claude/agents/` (project scope), or the built-in `general-purpose`.
- `description` -> short user-visible label.
- `prompt` -> full task prompt including Native Fields, Owned Scope, and
  Required Output Schema.
- Model and tool allowlist are set on the agent definition, not per-`Task`
  call; mention model class in the prompt but do not encode it as a Task
  parameter.

## Claude Code Model Mapping

Claude Code agent definitions set `model` in agent frontmatter (or inherit
from the session default). Translate model classes at agent-definition time;
the dispatch call itself only references the agent name.

- `cheap-fast` -> `claude-haiku` (latest); only read-only, narrow, verifiable
  output.
- `balanced` -> `claude-sonnet` (latest).
- `coding` -> `claude-sonnet` (latest) or inherited from a strong coding
  parent.
- `frontier` -> `claude-opus` (latest).
- `inherited` -> omit `model` in agent frontmatter; record that inheritance is
  intentional.

Evaluate the split before implementation steps. Do not wait for a proposal or plan to explicitly name every track; stage contracts authorize dispatch when economics and ownership are clear.
