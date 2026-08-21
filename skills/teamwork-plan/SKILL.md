---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff and the outcome and direction are already selected; do not use to choose the direction or execute changes.
---

# Teamwork Plan

Turn one selected direction into executable work. Do not require a previous
discussion artifact.

## Method

1. Verify the settled direction against project facts, the full set of goals,
   and observable acceptance. If a remaining unknown would change the goal,
   direction, or acceptance, return that gap instead of a partial plan.
2. Inspect the actual owners, interfaces, dependencies, and nearest useful
   verification.
3. Organize outcome-sized work in dependency order. Name exact targets and what
   each step produces. The first executable step must change the target
   artifact or remove an observed mechanical blocker. The critical path holds
   only actions that produce the result and their real mechanical
   dependencies. Benchmarks, appendices, probes, and extra documents are not
   prerequisites just because they help explain.
4. Use parallel tracks only when they are independent and non-overlapping.
5. Include migration, rollback, compatibility, or risk work only when the chosen
   direction actually requires it.
6. End with dependencies, verification, and the conditions that require
   replanning. When editing any existing plan surface, including a host plan,
   keep the stable identity and unaffected content. Default to a local patch.
   Rearrange the whole plan only when the user changes the goal or direction.
   Do not open a new plan because of added acceptance checks or parallel
   concerns.

Return unresolved material choices to the user; do not hide them as assumptions.
Return the executable plan.

## Persistence

When a listed checkpoint fires, write in the same response cycle. If separate
stable identities each cross a checkpoint, write each to its own path.

Cross-chat memory lives in one Markdown document from `references/plan.md`
at `docs/teamwork/plans/<slug>.md`. Same identity means the same
selected outcome; reuse that path and name the document you read.
A different subject gets a new path. Later edits reuse that path; do not open
a new plan because of added acceptance checks or parallel concerns.

Checkpoints: the direction and scope are accepted (this settles direction
only; it does not create a document for an unaccepted draft); the executable
plan is first settled when that first executable plan is accepted by the
user; a material replan changes steps, dependencies, verification, or stop
conditions only after the user accepts that replan.
