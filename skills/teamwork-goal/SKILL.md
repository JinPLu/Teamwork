---
name: teamwork-goal
description: Use when the user explicitly asks the host to keep working until a verifiable result, fix until green, converge without stopping, monitor through completion, or operate within a stated budget; do not use for ordinary one-shot work or infer persistence from task difficulty.
---

# Teamwork Goal

Apply persistence around the user's actual task. Goal is a modifier, not a
separate research, design, planning, debugging, implementation, or review stage.
It never broadens scope or effect authority.

## Establish State

Record objective, direct success signal, scope, protected boundaries, invariants,
supplied budget, and hard stops. Inspect discoverable state first; ask only for a
missing user-owned value that prevents progress. Do not invent iteration, time,
or token budget.
If the user says `no files`, `off-record`, `read-only`, `no writes`, or equivalent
and no host-native durable state satisfies it, Goal fails closed before promising
persistence; deliver no continuity claim.

Create durable Goal state at entry, before attempt one, through the host-native
mechanism or, for an initialized project, Writer calling the Goal artifact
transaction. Writer runs `discussion-transaction.py goal-inspect --project-root
<project>` and retains its revision, runs `discussion-transaction.py goal-schema
<start|attempt|close>`, then runs `discussion-transaction.py goal-apply
--project-root <project> --request <file>` with that revision and reads back. The transaction derives
`docs/teamwork/reports/YYYY-MM-DD-<slug>-goal.md`; never invent or hand-author it.
Writer is only the caller, and the transaction is the sole filesystem writer.
Record objective, success signal, invariants, scope, budget, hard stops, status,
and attempts. If state is unavailable, stop and report the continuity gap.
Preserve an exact user-supplied token budget; never invent one.

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
attempt needs a strategy delta grounded in new evidence or relevant change. Use
planning only when scope or criteria change; use review only when requested or
required by a named risk gate.

Mark the durable goal complete only when the real success signal passes and every
named protected boundary is satisfied. Continue after an ordinary failure while
a safe, evidence-backed different action remains. Stop for missing authority or
required input, destructive or security risk, exhausted user budget,
protected-boundary conflict, unavailable resources, or genuine no-progress.
Follow the host's status semantics when recording completion or blockage, and
never report success from a proxy check. Goal completion notifications are available
only on Codex (hooks) and Claude Code; on Cursor the user polls manually.

Every durable Goal entry, attempt, or standalone report uses a bounded brief/packet:
purpose/audience, facts/sources, frozen decision/status, style/structure, exact
path/consumer, preserve/forbid, objective, attempts, evidence, blocker, and next
strategy. Writer handles standalone prose and may only call the native mechanism
or Goal transaction for managed artifacts. Missing Writer, brief, authority,
path, consumer, or registration blocks; no Root, Worker, or other role fallback
writes it.
