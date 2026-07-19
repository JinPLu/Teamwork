---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff for a direction and contract already selected, or a host requires that execution plan; do not use to brainstorm or settle product/architecture choices, research external facts, diagnose failures, review a candidate, or execute changes.
---

# Teamwork Plan

Translate an already selected direction into work that can be executed without
redesign. Planner may write only the single Plan artifact authorized by this
workflow. Do not redesign or implement.

## Readiness

Confirm that the outcome, chosen direction, scope, protected boundaries, and
acceptance signals are settled. Inspect the local owners, flow, interfaces,
tests, configuration, and repository commands needed to make the steps concrete.
Do not ask for discoverable facts or turn safe implementation details into user
decisions.

If a still-open choice would change user behavior, architecture, public
contracts, data, permissions, migration, or scope, stop and state the exact
decision needed. Do not compare options or hide it as an assumption. Missing
implementation details may remain explicit prerequisites that block only their
dependent steps.

## Plan Shape

Lead with the intended result and scope. Produce owned, ordered actions with
dependencies and direct proof. Each work unit identifies:

- the owner or target surface;
- the concrete change and preserved invariant;
- dependencies and values that must come from source rather than invention;
- the nearest direct success check;
- any public-boundary, migration, rollout, or rollback proof that is actually
  required.

Keep steps outcome-sized: large enough to produce a meaningful result and small
enough to verify. Name parallel tracks only when they are truly independent and
give each non-overlapping ownership. Put real execution before optional cleanup.
Use tests and validation to prove the requested result, never as a substitute for
an available real run.

End with explicit stop or replan conditions: new evidence changes the selected
direction or criteria; required authority or source values are absent; a
protected boundary cannot be verified; or the planned owner is not the real
owner. Do not add a confirmation turn when no decision remains.

Independent Plan Review runs only when the user requests it or a named material
risk gate requires it. When invoked, the reviewer freezes the selected direction,
scope, criteria, protected boundaries, candidate Plan, and direct local evidence;
it returns stable `PR-*` findings and `ACCEPT`, `REVISE`, or `BLOCKED`. Combine
its findings into one repair batch. The same reviewer may perform at most one
bounded delta recheck for that Plan; materially expanded scope requires a fresh
review decision. A reviewed Plan cannot pass with placeholders, ellipses, guessed
values, unresolved alternatives, `or its replacement`, vague “handle edge cases”
work, or redesign disguised as a step. An unreviewed Plan must not be described
as independently accepted.

Save exactly one durable Plan at the explicitly agreed path or
`docs/teamwork/plans/YYYY-MM-DD-<slug>.md`. If artifact authority is unavailable,
return the candidate in conversation and mark the durable workflow incomplete;
do not write another file. A Plan, its review, or approval does not authorize
implementation, release, external effects, or destructive action.
