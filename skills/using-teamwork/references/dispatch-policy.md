# Dispatch Policy

Use when deciding whether to dispatch subagents or when reviewing dispatch
economics. Keep prompt details in `subagent-prompt-contract.md` and packet
schemas in `subagent-packets.md`.

## Stage-Routed Proactive Dispatch

Teamwork stages authorize their own non-destructive subagent dispatch. Do not
wait for the user, `Goal Proposal`, `Dispatch Guidance:`, or durable
`Subagent Routing` to name every track.

- Research: Explorer tracks for 2+ separable evidence questions.
- Plan: Designer for ambiguous choices; Judge for high-risk or delegated plans.
- Execute: Worker split from accepted steps, files, components, and ownership.
- Review: fresh-context Reviewer for non-trivial execution, high-risk diffs, or
  acceptance; same-context self-review cannot accept non-lightweight work.
- Goal: rerun the stage dispatch decision on each failed attempt.

Plans record expected routing. Execution records actual dispatch. Review checks
both.

## Roles

- Explorer: read-heavy investigation with condensed evidence.
- Designer: requirements, architecture, or behavior tradeoffs before planning.
- Judge: fresh-context plan review before execution.
- Worker: implementation with exact file ownership or worktree isolation.
- Reviewer: fresh-context review against diffs, tests, logs, and artifacts.

## Dispatch Economics

- Explorer/Reviewer: default max 3 parallel unless the user gives a larger
  budget; keep raw evidence out of the main context.
- Worker: no fixed numeric cap; dispatch one Worker per independent owned track when
  elapsed time or isolation improves.
- Before dispatching more than 3 Workers, state ownership map, integration
  order, verification, and why parallel is cheaper than serial.
- Use batch or worktree isolation when ownership is uncertain, tracks are many,
  verification is shared, or merge cost may dominate.
- If not dispatching, state why local execution is cheaper or safer. For
  non-lightweight review, unavailable tools or explicit user opt-out are the
  only acceptable reasons to skip a fresh Reviewer; mark acceptance unreviewed.

## Role Profiles

Use model class as the stable policy and translate it through Codex Model
Mapping at dispatch time. Prefer fewer, stronger models over fragile cheap
defaults.

- Explorer: `agent_type:"explorer"`, model class `balanced` by default; may use
  `cheap-fast` only for narrow read-only questions with directly checkable
  evidence; `reasoning_effort:"low"` or `"medium"`;
  context `condensed-evidence-only`.
- Designer: `agent_type:"default"`, model class `balanced`; use `frontier` for
  architecture, public behavior, data contracts, or unfamiliar APIs;
  `reasoning_effort:"medium"` or `"high"`; read-only.
- Judge: `agent_type:"default"`, model class `frontier`;
  `reasoning_effort:"high"`; context `fresh-context-review`; read-only.
- Worker: `agent_type:"worker"`, model class `coding` or `inherited`; use
  `frontier` for cross-module, high-risk, security, or public behavior changes;
  `reasoning_effort:"medium"` or `"high"`; context `owned-files-only`.
- Reviewer: `agent_type:"default"`, model class `frontier`; use `balanced` only
  for small mechanical diffs with complete verification; `reasoning_effort:"high"`;
  context `fresh-context-review`; read-only.

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

- `cheap-fast` -> `gpt-5.4-mini`; only when output is read-only, narrow, and
  directly verifiable.
- `balanced` -> `gpt-5.4`.
- `coding` -> `gpt-5.3-codex` or inherited when the parent is already a strong
  coding model.
- `frontier` -> `gpt-5.5`.
- `inherited` -> omit `model`; record that inheritance is intentional.

Do not combine `fork_context:true` with `agent_type`, `model`, or
`reasoning_effort`; full-history forks inherit parent routing. Codex has no
native `judge`, `reviewer`, or `designer` agent types.

Evaluate the split before implementation steps. Do not wait for a proposal or
plan to explicitly name every track; stage contracts authorize dispatch when
economics and ownership are clear.
