---
name: teamwork-goal
description: Use when the user explicitly asks to persist until a verifiable result, fix until green, monitor through completion, or stay within a stated budget; do not infer persistence from difficulty.
---

# Teamwork Goal

Goal adds persistence to the underlying task; it does not add a second workflow.

## Method

1. State the concrete objective, success signal, applicable scope, and any user
   budget.
2. Perform the next useful action and observe the result.
3. Continue until the success signal is directly observed, the user interrupts,
   or a genuine external blocker prevents further progress.
4. Change approach when evidence invalidates the current one. Do not repeat a
   failed action without a new reason.
5. Report success with the observed evidence, or report the exact blocker and
   what would unblock it.

Use subagents only when they provide useful independent or parallel work. Pass
the objective, scope, settled constraints, current evidence, and requested
return. Missing optional agents, installation freshness, document formats, and
report writing never block the underlying authorized task.

Tests support the goal but do not replace the real success signal when that
signal is available.

When the outcome is worth reusing or a report is requested, Root may ask Writer
to maintain one Markdown report for the continuing objective from
`references/report.md`. The report records requested versus
observed outcome, decisive evidence, resulting state or changes, remaining
action or blocker, and dated history; it is not an activity log and never
claims an unobserved completion. Every wake-up supplies the document kind and
path, stable subject identity, authoritative goal owner, owner-certified
semantic delta, read-only context, and expected base. Writer only compresses
literally, locates, deduplicates the current synthesis and pending delta,
updates the current synthesis, and appends history. Existing history is
immutable. It cannot change completion, evidence meaning, authority, next action,
or mainline. Writer failure never blocks the underlying goal; if the report was
explicitly requested, only report delivery remains incomplete.
