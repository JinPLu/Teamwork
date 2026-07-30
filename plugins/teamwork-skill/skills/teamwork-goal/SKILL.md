---
name: teamwork-goal
description: Use when the user explicitly asks the host to keep working until a verifiable result, fix until green, converge without stopping, monitor through completion, or operate within a stated budget; do not use for ordinary one-shot work or infer persistence from task difficulty.
---

# Teamwork Goal

Apply persistence around the user's actual task. Goal is a modifier, not a
separate research, collaboration, planning, debugging, implementation, or review
stage. It never broadens scope or effect authority. Collaborate owns
conversational continuity and decision convergence; Goal activates only when the
user explicitly asks to keep pursuing a verifiable outcome, budget, or monitor
contract. Goal is Root-owned. It may dispatch the exact role matching the
current blocker, but a mandatory role unavailable or not verifiably isolated is
`capability-blocked`; Root must not perform a named-method fallback.

## Establish State

Record objective, direct success signal, scope, protected boundaries, invariants,
supplied budget, and hard stops. Inspect discoverable state first; ask only for a
missing user-owned objective, success, scope, or authority value that prevents
safe progress. Root alone asks users through the current host's native surface;
leaf roles return proposed questions or blockers to Root. Answers do not expand
authority. Do not invent iteration, time, or token budget.
If the user says `no files`, `off-record`, `read-only`, `no writes`, or equivalent
and no host-native durable state satisfies it, Goal fails closed before promising
persistence; deliver no continuity claim.

Create durable Goal state at entry, before attempt one, through the host-native
mechanism or, for an initialized project, Writer calling the case-v2 Goal
transaction route selected from observed schema. Writer runs
`discussion-transaction.py case-inspect --project-root <project>` first. In
case-v2, it uses exact `case_id`/alias or creates from a frozen seed/task_key,
then `case-schema <goal-acquire|goal-update|goal-transfer|goal-close> ->
case-apply -> case-inspect/readback`; Goal is permitted only while the case is
`executing` except transfer/close. Legacy-v1, unknown, hybrid, mixed v1/v2,
stale, ambiguous case, missing seed/task_key, or partial migration fails closed
before any write, and one request must never touch both trees.
Writer is disposable compute and only the caller; the transaction is the sole
filesystem writer and owns destination, compare-and-swap, journal recovery,
atomic apply, and readback. Record objective, success signal, invariants, scope,
budget, hard stops, status, attempts, failure, evidence delta, and strategy
delta. If interrupted before apply begins or state is otherwise unavailable,
stop and report the continuity gap without a durable claim. Recover only from
surviving workflow evidence. Preserve an exact user-supplied token budget; never
invent one.

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

Maintain visible monotonic Goal state: `objective`, `signal`, `attempt`,
`failure`, `evidence_delta`, `strategy_delta`, and `status`. Every attempt must
move at least one of failure understanding, evidence, or strategy; otherwise
stop for no-progress instead of consuming budget.

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
