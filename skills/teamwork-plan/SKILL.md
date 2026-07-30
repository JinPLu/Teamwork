---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff, when an accepted Collaborate decision is ready to become executable work, or when a host requires that plan; do not use to brainstorm, grill, settle product/architecture choices, research external facts, diagnose failures, review a candidate, or execute changes.
---

# Teamwork Plan

Translate an already selected direction into work that can be executed without
redesign. Every Plan invocation defaults to a durable Plan in an initialized
writable project unless the user says `no files`, `off-record`, `read-only`, `no
writes`, or equivalent. Planner produces an execution-ready Plan packet only;
Writer saves or rewrites it. Do not redesign or implement. Collaborate owns
dialogue, brainstorming, grilling, and decision convergence; Plan activates only
after the material direction has been selected and, when required, accepted
through Collaborate.

## Readiness

Confirm outcome, chosen direction, scope, protected boundaries, and acceptance
signals are settled. Inspect local owners, flow, interfaces, tests,
configuration, and commands needed for concrete steps. Do not ask for
discoverable facts or turn safe implementation details into user decisions.
Root alone asks users through the current host's native surface; Planner and
other leaf roles return proposed questions or blockers to Root. Answers do not
expand authority.

When a prior Teamwork Collaborate decision is claimed, require the controlled
schema-specific Collaborate readback returned by its transaction. The handoff
must freeze schema, path, accepted decision identity, revision, and acceptance
evidence. First inspect schema. In case-v2, run `case-inspect`, read the
selected case manifest, and confirm the accepted decision artifact, case path,
manifest revision, no open blockers/frontier, and acceptance evidence match the
handoff. In legacy-v1, run
`discussion-transaction.py collaborate-inspect --project-root <project>` and
confirm `active.path == docs/teamwork/collaborate/current.md`,
`active.acceptance == accepted`, the exact accepted path, decision id, revision,
Collaborate-scoped revision, semantic digest, lineage digest, `current_batch ==
[]`, no open items/blockers/question/frontier, and `adversarial.status` is
`not_run` or `pass`. Pending or blocked Collaborate records are durable but
never Plan-ready. Legacy Design, Discussion, conversational recommendations,
adversarial audit results, hand-written files, generic artifacts, or failed
transactions are not Plan-ready and must not be promoted by Planner.

If an open choice would change behavior, architecture, public contracts, data,
permissions, migration, or scope, stop and state the exact decision needed. Do
not compare options or hide it as an assumption. Return unresolved material
direction to Collaborate. If a genuinely user-owned plan boundary remains after
evidence, propose it to Root. Missing implementation details may remain
prerequisites that block only dependent steps.

## Plan Shape

Lead with result and scope. Produce owned, ordered actions with dependencies and
direct proof. Each work unit identifies:

- the owner or target surface;
- the concrete change and preserved invariant;
- dependencies and values that must come from source rather than invention;
- the nearest direct success check;
- any public-boundary, migration, rollout, or rollback proof that is actually
  required.

Keep steps outcome-sized: meaningful and verifiable. Name parallel tracks only
when truly independent and give each non-overlapping ownership. Put real
execution before optional cleanup. Use tests to prove the result, not replace an
available real run.

End with explicit stop or replan conditions: new evidence changes the selected
direction or criteria; required authority or source values are absent; a
protected boundary cannot be verified; or the planned owner is not the real
owner. Do not add a confirmation turn when no decision remains.

Independent Plan Review runs only when the user requests it or a named material
risk gate requires it. When invoked, the reviewer freezes the selected direction,
scope, criteria, protected boundaries, candidate Plan, and direct local evidence;
it returns stable `PR-*` findings and `ACCEPT`, `REVISE`, or `BLOCKED`. Combine
its findings into one repair batch. The same reviewer may perform at most one
bounded delta recheck for that Plan; materially expanded scope requires a fresh
review decision. A reviewed Plan cannot pass with placeholders, ellipses, guessed
values, unresolved alternatives, `or its replacement`, vague “handle edge cases”
work, or redesign disguised as a step. An unreviewed Plan must not be described
as independently accepted.

Every Plan is a completion artifact. Freeze a bounded Plan packet:
purpose/audience, facts/sources, frozen decision/status, style/structure,
artifact kind/consumer, preserve/forbid, direction, scope, steps, dependencies,
proof, and stops. Dispatch one low-cost Writer; Root may do only
answer-invariant handoff work while Writer runs and must join and read back
before claiming the Plan is saved or durable. Writer routes from observed schema:
`case-inspect` first; in v2 case-bundle projects, case-v2 uses exact
`case_id`/alias or creates from a frozen seed/task_key, then
`case-schema <plan-upsert> -> case-apply -> case-inspect/readback`; legacy-v1
uses `artifact-inspect -> artifact-schema <create|update|supersede> ->
artifact-apply`. The transaction derives the destination and registers the
ordinary index or case manifest/claim heads.
Writer is disposable compute and the transaction owns destination,
compare-and-swap, journal recovery, atomic apply, and readback. If interrupted
before generic artifact apply or case apply begins, there is no durable claim;
recover only from surviving workflow evidence or report unsaved. Writer may polish expression but not
research, invent, or alter facts, authority, status, proof, decisions, or
acceptance. Missing project memory, Writer, brief, authority, consumer, route,
or transaction blocks only persistence: return the Plan and report it
unsaved/blocked. No Planner, Root, or Worker fallback writes it. Plan approval
does not authorize implementation, release, external effects, or destructive
action. Mixed v1/v2, unknown, stale, ambiguous case, missing seed/task_key, or
partially migrated state fails closed before any write.
