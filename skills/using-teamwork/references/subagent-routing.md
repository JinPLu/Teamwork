# Subagent Routing

Use this reference only when a Teamwork stage dispatches subagents or reviews
routing. Do not load it for simple native-flow work.

## Roles

- Explorer: read-heavy independent investigation with condensed evidence.
- Designer: ambiguous requirements, architecture tradeoffs, cross-module design,
  or product behavior choices before execution planning.
- Judge: fresh-context plan review before execution.
- Worker: implementation for an accepted plan with exact file ownership or
  worktree isolation.
- Reviewer: fresh-context execution review against diffs, tests, logs, and
  artifacts.

## Model Tiers

- `fast`: scoped evidence collection, low-risk mechanical edits, concise docs.
- `standard`: moderate reasoning, multi-file implementation, or investigation
  that needs synthesis.
- `high reasoning`: ambiguous requirements, high-risk plan review, final
  acceptance, regression analysis, or safety/security boundaries.

## Dispatch Economics

- Explorer/Reviewer: default max 3 parallel unless the user gives a larger
  budget. Keep only condensed evidence in the main context.
- Worker: no fixed numeric cap. Dispatch one Worker per independent owned
  track when parallel execution lowers elapsed time or isolation risk.
- Before dispatching more than 3 Workers, state the ownership map,
  merge/integration order, verification plan, and why parallel execution is
  cheaper than serial execution.
- Use batch or worktree isolation when ownership is uncertain, tracks are
  numerous, verification is shared, or merge cost may dominate.
- If not dispatching, state why local execution is cheaper or safer.

The main agent owns synthesis, conflict resolution, integration, verification,
and final acceptance.

## Parallel Execution

For non-lightweight implementation, dispatch Worker subagents by default when
planned work has disjoint file ownership or independent components and passes
Dispatch Economics. Evaluate the split before implementation steps. The plan
should name each track, owned paths, allowed
edits, verification expectation, and merge order. Dispatch Workers early and
keep the main thread on orchestration, integration, verification, and review.

Use local main-thread execution instead when the edit is small, tightly coupled,
requires one continuous mental model, has unclear ownership, or would cause
Workers to touch overlapping files. Do not split work merely for ceremony.

## Codex Dispatch Mapping

Map conceptual roles to Codex fields only at dispatch time:

- Explorer -> `agent_type:"explorer"`.
- Worker -> `agent_type:"worker"`.
- Designer, Judge, Reviewer -> `agent_type:"default"` with the conceptual role
  in the prompt.
- `fast` -> `reasoning_effort:"low"`.
- `standard` -> `reasoning_effort:"medium"`.
- `high reasoning` -> `reasoning_effort:"high"`.
- `xhigh` is not a normal Teamwork tier. Use `reasoning_effort:"xhigh"` only
  for explicitly high-risk final gates where cost is justified.

Full-history forks inherit parent type/model/effort. Do not combine
`fork_context:true` with `agent_type`, `model`, or `reasoning_effort`. Use
`fork_context:false` or omit `fork_context` when explicit routing overrides are
needed.

Codex has no native `judge`, `reviewer`, or `designer` agent types.
