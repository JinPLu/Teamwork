---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff, when an accepted Collaborate decision is ready to become executable work, or when a host requires that plan; do not use to brainstorm, stress-test, settle product/architecture choices, research external facts, diagnose failures, review a candidate, or execute changes.
---

# Teamwork Plan

Translate an already selected direction into executable work. The role mapping
is exact: Plan -> Planner, and Plan Review -> Plan Reviewer only for user request
or named material risk gate. Plan defaults to a durable case-v2 Plan in an
initialized writable project unless `no files`, `off-record`, `read-only`, `no
writes`, or equivalent applies. Planner produces the execution-ready packet;
Writer saves it. Do not redesign or implement. If mandatory roles or required
isolation are unavailable, return `capability-blocked`; Root must not perform a
named-method fallback.

## Readiness

Confirm outcome, chosen direction, scope, protected boundaries, and acceptance
signals are settled. Inspect local owners, control flow, interfaces,
tests/configuration, commands, and invariants needed for concrete steps. Do not
ask for discoverable facts or turn safe implementation details into user
decisions. Planner never asks users. It returns one exact missing required value
to Root with owner, scope, and resume condition. A material open direction,
latent preference, or unformed intent is a reclassification signal to
Collaborate, not a Plan assumption. Root alone asks, and answers do not expand
authority.

When that accepted decision is claimed, require controlled case-v2
Collaborate readback. The handoff must freeze schema, case path, accepted
decision identity, decision revision, manifest revision, digests, and acceptance
evidence. In case-v2, run `case-inspect`, read the selected case manifest, and
confirm the accepted decision artifact, manifest revision, decision revision,
case path, no open blockers/frontier, and acceptance evidence match. Legacy-v1,
pending, or blocked Collaborate records are durable/migration inputs but never
Plan-ready. Legacy Design, Discussion, recommendations, audits, hand-written
files, generic artifacts, and failed transactions are not Plan-ready.

If an open choice changes behavior, architecture, public contract, data,
permissions, migration, or scope, stop and return the exact decision to the
decision owner. Do not compare options or hide it as an assumption.

## Plan Shape

Lead with result and scope. Produce owned ordered actions with dependencies and
direct proof. Each work unit names owner/target surface, concrete change,
preserved invariant, source-derived dependencies, nearest real success check,
and required public-boundary, migration, rollout, or rollback proof. Keep steps
outcome-sized and verifiable; name parallel tracks only when independent and
non-overlapping. Put required execution before optional cleanup, and use tests to
prove rather than replace an available real path.

Maintain visible monotonic Plan state: `decision_revision`, `dependencies`,
`proof_targets`, `blockers`, and `stops`. A revision advances only when the
selected decision revision is unchanged or a new accepted decision readback is
supplied, dependencies are evidence-derived, and proof targets/stops remain
observable. End with stop or replan conditions: changed direction/criteria,
missing authority or source values, unverifiable protected boundary, or wrong
owner.

Independent Plan Review runs only on user request or a named risk gate. It
freezes direction, scope, criteria, protected boundaries, candidate Plan, and
direct evidence; returns stable `PR-*` findings and `ACCEPT`, `REVISE`, or
`BLOCKED`; permits one repair batch and at most one bounded delta recheck. A
reviewed Plan cannot pass with placeholders, ellipses, guessed values,
unresolved alternatives, `or its replacement`, vague "handle edge cases" work,
or redesign disguised as a step.

## Persistence

Plan content and persistence are separate. Return the Plan even if completion
artifact persistence fails, and state `unsaved/blocked`. Wait for Writer
readback only before claiming saved/durable or before dependent work requires
durable continuity.

Freeze a bounded Plan packet: purpose/audience, facts/sources, decision/status,
style/structure, artifact kind/consumer, preserve/forbid, direction, scope,
steps, dependencies, proof targets, blockers, and stops. Writer routes from
observed schema: `case-inspect` first; in case-v2 projects, use exact
`case_id`/alias or create from a frozen seed/task_key, then `case-schema
<plan-upsert> -> case-apply -> case-inspect/readback`. The transaction derives
destination and registers manifest/claim heads. Writer may polish expression but
must not research, invent, or alter facts, authority, status, proof, decisions,
or acceptance. Missing project memory, Writer, packet, authority, consumer,
route, or transaction blocks only persistence. No Planner, Root, or Worker
fallback writes it. Plan approval does not authorize implementation, release,
external effects, or destructive action. Legacy-v1, mixed v1/v2, unknown, stale,
ambiguous case, missing seed/task_key, or partially migrated state fails closed
before any write.
