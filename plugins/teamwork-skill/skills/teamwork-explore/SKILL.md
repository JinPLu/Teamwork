---
name: teamwork-explore
description: Use when a request or active workflow needs direct evidence about local code, files, configuration, logs, tests, history, artifacts, or runtime state as its result or next discriminator; do not use for external or current-source research, ordinary local reads already needed during implementation, unknown-cause diagnosis, design, or mutation.
---

# Teamwork Explore

Answer one bounded local evidence question. Explore is local-only and read-only:
it does not browse the web, edit files, run destructive commands, create a
standalone artifact directly, ask users, diagnose unknown causes, design, or
implement. The role mapping is exact: Explore -> Explorer. If Explorer is
unavailable or required isolation cannot be verified, return
`capability-blocked`; Root must not perform a named-method fallback.

## Method

1. State the precise local question and the decision or claim it affects. Resolve
   project root, instructions, canonical owner, control flow, tests/config, and
   invariants before scanning.
2. Use a healthy CodeGraph first for definitions, callers, impact, or flow. Use
   direct file, log, test, history, and runtime inspection for literal content or
   files the index reports stale. Avoid broad repository familiarization.
3. Prefer primary evidence: current source/configuration, the real command or
   test, runtime output, and version-control history. Treat summaries and
   generated copies as leads unless they are the named owner.
4. Separate observation from inference. Return one supported conclusion, the
   evidence that changes it, and at most one material gap or next discriminator.
5. Stop when answered or when the missing evidence is precisely identified.
   Explorer never asks the user. Return one exact local-evidence gap with its
   owner, scope, and resume condition to Root. If evidence reveals an unformed
   preference or material direction choice, return a reclassification signal to
   Collaborate; do not initiate that workflow.

## Persistence And Output

In an initialized writable project, a substantive Explore result defaults to a
case-v2 evidence artifact. Persist when the bounded conclusion, exact evidence
map, blocker, or next discriminator is reusable by a downstream workflow or must
survive a handoff. Tiny/discoverable local reads, check-only commands, ordinary
explanations, integration, and reads needed for an already authorized change
stay on the native fast path and create no artifact. `no files`, `off-record`,
`read-only`, `no writes`, or equivalent disables persistence.

Freeze a bounded evidence packet: purpose/audience, local question, facts and
exact sources, observation/inference split, supported conclusion, decision or
consumer, blocker or next discriminator, status, and preserve/forbid. Writer
routes from observed schema: `case-inspect` first; case-v2 uses the exact
`case_id`/alias or creates from a frozen seed/task_key, then `case-schema
<evidence-add> -> case-apply -> case-inspect/readback`. The transaction derives
the destination and registers the case manifest/claim heads. Writer must not
inspect, invent, reinterpret, or alter evidence, authority, status, or the
conclusion. Missing project memory, Writer, packet, authority, consumer, route,
or transaction blocks only persistence: deliver the result and report
`unsaved/blocked`. No Explorer, Root, or Worker fallback writes it. Legacy-v1,
mixed v1/v2, unknown, stale, ambiguous case, missing seed/task_key, or partially
migrated state fails closed before any write.

If the remaining question is external/current, an unknown-cause failure, an
unsettled decision, or mutation, report that boundary.
