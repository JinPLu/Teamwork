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
   replanning. Persist the checkpoint under Persistence before closeout; a host
   plan or question UI does not complete it.

A Planner subagent is optional. Use Explorer when available; otherwise use
native local search. Its handoff contains the objective, owned scope, settled
user constraints, available evidence, and requested return. If unavailable,
Root continues without switching to Update or blocking the plan.

Return unresolved material choices to the user; do not hide them as assumptions.

## Persistence

Cross-chat memory lives in one Markdown document from `references/plan.md`
at `docs/teamwork/plans/<YYYY-MM-DD>-<slug>.md`. Same identity means the same
selected outcome and direction; reuse that path and name the document you read.
A different subject gets a new path.

Checkpoints: the direction and scope are accepted; the executable plan is first
settled; a material replan changes steps, dependencies, verification, or stop
conditions. Keep user quotes separate from the working understanding.

Prefer Writer, a helper role with its own writing contract, not a Skill. If
Writer is unavailable or returns a no-write, Root writes the same template to
the same path and marks Root fallback in the closeout. Planning never blocks on
Writer; silently skipping a fired checkpoint is a Skill violation.
