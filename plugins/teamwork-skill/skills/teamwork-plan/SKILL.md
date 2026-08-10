---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff and the outcome and direction are already selected; do not use to choose the direction, research external facts, diagnose a failure, review a candidate, or execute changes.
---

# Teamwork Plan

Plan is the current execution-design stage. Planner turns one selected direction
into executable, verifiable work; Root owns the brief and any stage switch. Do
not require a prior Collaborate artifact, reopen settled choices, implement the
plan, or treat plan acceptance as execution authority.

## Prepare

Confirm the intended result, selected direction, scope, constraints, protected
boundaries, and observable acceptance signals. Inspect the actual owners,
interfaces, dependencies, tests, configuration, and commands needed to make the
work concrete. Resolve discoverable details directly. Return an unresolved
material direction to its decision owner instead of hiding it as an assumption.

## Build The Plan

Organize outcome-sized work in dependency order. For each work unit, state the
responsible owner, exact target surface, concrete outcome and protected
behavior, upstream and downstream dependencies, and the nearest real
verification. Include migration, rollout, rollback, cleanup, or risk work only
when the selected direction actually creates it.

Use parallel tracks only for bounded work that is genuinely independent and
non-overlapping; there is no prescribed agent or dispatch count. Replace vague
steps, guessed values, unresolved alternatives, and generic “handle edge cases”
language with an action, evidence need, or exact blocker. Tests support the
outcome but do not substitute for an available real-path check.

End with dependency and verification relationships plus the conditions that
would stop execution or require replanning, such as a changed direction, wrong
owner, missing authority, or unverifiable protected boundary.

An independent Plan Review is a separate current stage only when the user asks
for it or an actual gate requires it. Importance, complexity, release wording,
or subjective risk alone does not create that gate. Root suspends Plan, switches
to Review, and resumes only if later planning work is needed.

Planner is required. Root must not imitate it when unavailable. Suspend Plan,
switch to Update for readiness repair, wait, and resume or return the exact
blocker.

## Codex Role Dispatch

On Codex, dispatch Planner and Writer through `spawn_agent.agent_type` as
`teamwork_planner` and `teamwork_writer`. Use `fork_turns` set to `none` or a
bounded recent context, then observe a live child start; never silently
substitute an unavailable role.

## Plan Document

When the selected direction and first concrete work unit become reusable, Root
assigns Writer the typed Plan document. It carries the intended result,
direction, scope and protected boundaries, ordered work, owners and targets,
dependencies, real verification, blockers, and stop or replan conditions.
Update only when one of those meanings changes; do not use it as an execution
progress log. Same-scope editorial corrections may update a finalized document;
a new direction or materially new scope needs a new Plan document.
