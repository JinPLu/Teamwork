---
name: teamwork-goal
description: Use when the user explicitly asks the host to keep working until a verifiable result, fix until green, converge without stopping, monitor through completion, or operate within a stated budget; do not use for ordinary one-shot work or infer persistence from task difficulty.
---

# Teamwork Goal

Apply persistence around the user's actual task. Goal is a modifier, not a
separate research, design, planning, debugging, implementation, or review stage.
It never broadens scope or effect authority.

## Establish State

Record the objective, direct success signal, scope, protected boundaries,
invariants, supplied budget, and hard stops. Inspect discoverable state first;
ask only for a missing user-owned value that prevents progress. Do not invent an
iteration, time, or token budget.

Create durable Goal state at entry, before the first attempt, using the host's
native goal mechanism or, when the project is initialized, the Goal artifact at
`docs/teamwork/goals/YYYY-MM-DD-<slug>.md`. Record objective, direct success signal,
invariants, scope, budget, hard stops, status, and attempt history. If durable state
is unavailable, stop and report the continuity gap rather than claiming persistence. If the user
supplied a token budget, preserve that exact budget; never invent one.

## Iterate

For each attempt, identify the single current unmet claim and use only the role
whose method matches that blocker:

1. Observe the current direct failure or unmet success signal.
2. Preserve the accepted scope and invariants.
3. Choose the smallest authorized next action supported by the evidence.
4. Run the nearest real success path.
5. Persist the attempt number, unmet claim, direct evidence, blocker, strategy
   delta, and next strategy before continuing or yielding.

Do not repeat an unchanged command, hypothesis, fix, or review loop. A new
attempt needs a strategy delta grounded in new evidence or a relevant change.
Use planning only when accepted scope or criteria genuinely change; use review
only when the user or a named risk gate requires it.

Mark the durable goal complete only when the real success signal passes and every
named protected boundary is satisfied. Continue after an ordinary failure while
a safe, evidence-backed different action remains. Stop for missing authority or
required input, destructive or security risk, exhausted user budget,
protected-boundary conflict, unavailable resources, or genuine no-progress.
Follow the host's status semantics when recording completion or blockage, and
never report success from a proxy check. Goal completion notifications are available
only on Codex (hooks) and Claude Code; on Cursor the user polls manually.
