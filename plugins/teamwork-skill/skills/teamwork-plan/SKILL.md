---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff and the goal and direction are already selected; do not use to brainstorm or choose the direction, research external facts, diagnose a failure, review a candidate, or execute changes.
---

# Teamwork Plan

Use Planner to turn a selected direction into executable, verifiable work. Do
not require a prior Collaborate artifact or reopen settled choices. Do not
implement the plan.

## Prepare

Confirm the outcome, direction, scope, constraints, protected boundaries, and
acceptance signals. Inspect local owners, dependencies, interfaces, tests,
configuration, and commands needed to make the steps concrete. Resolve
discoverable details directly. Return a material unresolved direction to the
decision owner rather than hiding it as an implementation assumption.

## Write The Plan

Lead with the intended result and scope. Order the work by dependency and name
parallel tracks only when they are independent and non-overlapping. For each
work unit, state:

- the owner and target surface;
- the concrete outcome, including what must remain unchanged;
- upstream and downstream dependencies;
- the nearest real verification and any required boundary proof;
- material risk, rollback, migration, or rollout work when applicable.

Keep steps outcome-sized and handoff-ready. Replace placeholders, unresolved
alternatives, guessed values, and vague instructions such as “handle edge
cases” with a named action or blocker. Put required execution before optional
cleanup. Tests support the result; they do not replace an available real path.

Review the plan with Reviewer when the user requests it or a release, security,
permission, data, destructive-risk, or public-contract gate requires an
independent check. Planner does not review its own plan.

End with dependencies, verification matrix, blockers, and explicit stop or
replan conditions such as a changed direction, wrong owner, missing required
input or authority, or an unverifiable protected boundary.

## Live Document

When Writer is used, include the goal, selected direction, scope, ordered work
units, owners, dependencies, verification, risks, blockers, and replan
conditions. Writer may improve organization but must not invent facts, change
the direction, or mark the plan accepted.
