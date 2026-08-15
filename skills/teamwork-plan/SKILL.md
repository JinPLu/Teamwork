---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff and the outcome and direction are already selected; do not use to choose the direction or execute changes.
---

# Teamwork Plan

Turn one selected direction into executable work. Do not require a previous
discussion artifact.

## Method

1. Confirm the intended result, selected direction, scope, settled constraints,
   and observable acceptance signal.
2. Inspect the actual owners, interfaces, dependencies, and nearest useful
   verification.
3. Organize outcome-sized work in dependency order. Name exact targets and what
   each step produces.
4. Use parallel tracks only when they are independent and non-overlapping.
5. Include migration, rollback, compatibility, or risk work only when the chosen
   direction actually requires it.
6. End with dependencies, verification, and the conditions that require
   replanning.

A Planner subagent is optional. Use Explorer when available; otherwise use
native local search. Its handoff contains the objective, owned scope, settled
user constraints, available evidence, and requested return. If unavailable,
Root continues without switching to Update or blocking the plan.

Return unresolved material choices to the user; do not hide them as assumptions.

## Persistence

At each semantic checkpoint, Root asks Writer to maintain one Markdown plan for
the selected outcome and direction from `references/plan.md` at
`docs/teamwork/plans/<YYYY-MM-DD>-<slug>.md` (reuse the existing path for the
same subject identity). Checkpoints: the direction and scope are accepted; the
executable plan is first settled; a material replan changes steps, dependencies,
verification, or stop conditions.

This hook does not turn the plan into a discussion history or execution log.
Every Writer wake-up explicitly supplies the document kind and path, stable
subject identity, authoritative planning owner, owner-certified semantic delta,
read-only context, and expected base. Writer may only compress literally,
locate, deduplicate the current synthesis and pending delta, refresh the
current plan synthesis, and append dated plan-revision history. Existing
history is immutable. It cannot choose or change the direction, requirements,
recommendation, authority, dependencies, verification, next action, or
mainline. Missing state or a conflicting base produces a no-write exact gap.
Writer unavailability or conflict does not block planning; when a checkpoint
fired, report incomplete document delivery.
