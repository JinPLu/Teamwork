---
name: teamwork-goal
description: Use when the user explicitly asks the host to keep working until a verifiable result, fix until green, converge without stopping, monitor through completion, or operate within a stated budget; do not use for ordinary one-shot work or infer persistence from task difficulty.
---

# Teamwork Goal

Persist around the user's actual task. Goal is an explicit modifier, not a
research, collaboration, planning, debugging, implementation, or review stage. It
never broadens scope or effect authority. Goal is Root-owned and may dispatch
only the exact role matching the current blocker; unavailable mandatory roles or
unverified isolation are `capability-blocked`, with no named-method fallback.

## Establish

Record objective, real success signal, scope, protected boundaries, invariants,
user budget, hard stops, and authority. Inspect discoverable state first; ask
only for one exact missing user-owned value that prevents safe progress. Root
alone asks once, records one active gap, and resumes the same Goal when the value
returns; independent safe work continues. Leaf roles return the exact gap and
never ask. An unformed objective or material preference is reclassified to
Collaborate before Goal commitment. Answers do not expand authority, and budgets
are never invented.

If `no files`, `off-record`, `read-only`, `no writes`, or equivalent conflicts
with every available durable mechanism, fail closed before promising continuity.

Create durable Goal state at entry, before attempt one, through host-native state
or an initialized project's case-v2 Goal transaction route. Writer runs
`discussion-transaction.py case-inspect --project-root <project>` first, then in
case-v2 uses exact `case_id`/alias or creates only from a frozen seed/task_key:
`case-schema <goal-acquire|goal-update|goal-transfer|goal-close> -> case-apply
-> case-inspect/readback`. Goal acquire/update are permitted only while the case
is `executing`; transfer/close follow their transaction rules. Legacy-v1,
unknown, hybrid, mixed v1/v2, stale, ambiguous case, missing seed/task_key, or
partial migration fails closed before any write, and one request never touches
both memory trees.

Writer is disposable; the transaction owns destination, compare-and-swap,
journal recovery, atomic apply, and readback. Record objective, signal, scope,
invariants, budget, hard stops, status, attempt, failure, evidence_delta, and
strategy_delta. Interruption before apply gives no durable claim.

## Iterate

For each attempt:

1. Observe the current direct failure or unmet success signal.
2. Preserve accepted scope and invariants.
3. Choose the smallest authorized next action supported by evidence.
4. Run the nearest real success path.
5. Persist attempt number, unmet claim, evidence, blocker, strategy delta, and
   next strategy before continuing when the next round depends on continuity.

Maintain visible monotonic Goal state: `objective`, `signal`, `attempt`,
`failure`, `evidence_delta`, `strategy_delta`, and `status`. Do not repeat an
unchanged command, hypothesis, fix, or review loop; a new attempt needs new
evidence or a strategy delta. Use planning only when scope or criteria change;
use review only on request or named risk gate.

Complete only when the real success signal passes and protected boundaries are
satisfied. Continue after ordinary failure while a safe different action remains.
Stop for missing authority/input, destructive/security risk, exhausted budget,
boundary conflict, unavailable resources, or no-progress.

## Output And Persistence

Method progress and persistence are separate. If terminal/completion companion
persistence fails after the core result is complete, return it and state
`unsaved`; do not mask actual task success or failure. Wait for
checkpoint/readback only when the next Goal round or continuity depends on it.

Every durable Goal entry, attempt, or standalone report uses a frozen bounded
packet: purpose/audience, facts/sources, decision/status, consumer/path,
preserve/forbid, objective, attempts, evidence, blocker, and next strategy.
Writer may only call host-native state or the Goal transaction. Missing
Writer, packet, authority, path, consumer, route, or registration blocks durable
claims; no Root, Worker, or other role fallback writes it. Goal completion
notifications exist only where the host provides them.
