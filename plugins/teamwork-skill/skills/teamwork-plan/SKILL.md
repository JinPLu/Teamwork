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

A Planner or Explorer subagent is optional. Its handoff contains the objective,
scope, settled constraints, evidence, and requested return. If unavailable,
Root continues without switching to Update or blocking the plan.

Return unresolved material choices to the user; do not hide them as assumptions.
