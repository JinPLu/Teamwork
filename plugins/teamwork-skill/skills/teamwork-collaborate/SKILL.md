---
name: teamwork-collaborate
description: Use when the user wants dialogue, brainstorming, sustained questioning, stress-testing, or convergence on product, workflow, API, system, release, migration, permission, security, data, destructive, or cross-platform decisions before execution; activate aggressively from natural discussion or question-before-action intent, select dialogue or brainstorm without asking, default-persist semantic checkpoints through Writer, and do not use for external research alone, unknown-cause debugging, implementation, review, or already accepted decisions.
---

# Teamwork Collaborate

Own one collaborative decision surface. Collaborate is the only public Teamwork
skill for natural dialogue, brainstorming, sustained questioning, stress-testing,
and decision convergence. It replaces the retired public Discuss, Design, and
Grill skill sources without aliases or compatibility public surfaces.
Stress-testing is a challenge method inside dialogue or brainstorm, not a third runtime mode.
Internal Designer is read-only challenge/audit only; it never owns
questions, acceptance, persistence, planning, implementation, or release. This
skill does not authorize file changes outside its checkpoint or implementation.

Collaborate exclusively owns latent preferences and unformed intent that can
materially change the outcome. Only Root may activate it or present its
questions. A leaf instead returns an explicit reclassification signal with the
decision boundary it found; it never starts Collaborate or asks the user.

## Mode And Questions

Select the mode from intent and evidence; do not ask the user to name it.

- `dialogue`: synthesize the current decision, tension, and next judgment.
- `brainstorm`: widen two or three meaningful alternatives, constraints, and a
  preferred or next-best option.

Before every question, contribute first and include a provisional
recommendation. Ask only when user-owned feedback can change the next response,
durable state, or execution boundary. Skip discoverable, safe-default,
reversible-detail, and answer-invariant questions. Use one open prose question
for sensemaking. A native bounded batch contains at most three questions, and
every question in that batch must be mutually independent.

Dependent questions are serial: ask the question, wait for the answer, dispatch
Writer checkpoint only when durable continuity is in scope, read back proof, and
then continue. Completion or terminal companion persistence is separate from the
method result: if it fails after the core answer is ready, return the core answer
and state `unsaved`. Two rounds with no closed decision, new discriminator, or
changed recommendation are a no-progress blocker.

## Challenge

Challenge moves strictly `global -> boundary -> detail`.

1. Global: whole decision map, current critical path, recommendation, largest
   downside, and only boundary-setting choices.
2. Boundary: after the global answer and any needed readback, test scope,
   permissions, data, migration, reversibility, public contract, rollout, and
   stop conditions.
3. Detail: after the boundary answer and any needed readback, ask only remaining
   decisions that change the accepted outcome or downstream boundary.

For each bounded challenge question, state why the answer is critical, what it
blocks, dependencies, recommendation, largest downside, and observable closing
condition before asking.

Use `references/adversarial-search.md` only when the user explicitly requests adversarial search,
when at least two viable directions remain and costly or
irreversible error or conflicting evidence makes ordinary challenge insufficient,
or when a named risk gate requires isolation. The method replaces only the
challenge method and does not create a public Design workflow. If required fresh
Designer isolation is unavailable, return `capability-blocked`; Root must not perform a named-method fallback.

## Acceptance

Recommend one clear direction when supported; otherwise compare two or three
meaningful alternatives by outcome, compatibility, complexity, operability,
reversibility, migration cost, risk, and ownership.

Acceptance requires closure evidence: no current batch, unanswered question,
open frontier, material blocker, or pending/failed adversarial state;
`active.acceptance == accepted`; `recommendation` is nonempty; and
`acceptance_evidence` is nonempty. Pending or blocked Collaborate records are
durable but not Plan-ready.

## Persistence

In an initialized writable project, sustained semantic Collaborate state defaults
to a managed case-v2 Collaborate checkpoint at the first substantive dialogue,
brainstorm, challenge, question-before-action state, decision update, accepted
decision, blocker, close, or supersede. Persist before a dependent question only
when continuity depends on it, and before handing an accepted decision to Plan.

Negative overrides win: `no files`, `off-record`, `read-only`, `no writes`, and
private/no-persistence equivalents disable persistence. Continue collaboration
and report unsaved state when it matters.

Root freezes a bounded Collaborate packet: synthesis, evidence, candidate space,
recommendation, downside, decision rule, closure evidence, open
questions/frontier, blockers, return path, and preserve/forbid.
Writer calls only the controlled transaction route;
it must not research, invent, reinterpret, or alter facts, authority, status, or
acceptance. Missing memory, Writer, route, authority, consumer, packet, or
transaction blocks only durable claims unless the next step depends on durable
continuity; there is no Root, Designer, Worker, Reviewer, direct/manual file, or
fallback write route.

Writer runs `discussion-transaction.py case-inspect --project-root <project>`.
If schema is case-v2, use the exact `case_id`/alias from `active_cases` or create
only from a frozen seed/task_key, title, and aliases; legacy-v1, mixed v1/v2,
unknown, stale, ambiguous, missing seed, or partial migration fails closed before
any write. In case-v2, Writer uses `case-inspect -> case-schema
<create|collaborate-upsert|accept-decision> -> case-apply ->
case-inspect/readback`. Map checkpoints to `collaborate-upsert`, accepted
decisions to `accept-decision`, and phase/meta only to `update`. Claim durable
state only after readback returns case path, manifest revision, semantic digest
or decision digest, lineage digest, and changed paths. Safe
transaction failure grants no Markdown, index, journal, marker, legacy, or
manual retry; `INDETERMINATE` pauses.

The transaction-derived checkpoint content is `live/collaborate.md`; accepted
decisions use `decision.md`.

Legacy Discussion, Design, Collaborate, artifact, and Goal files are read-only
migration inputs only. Legacy write lifecycle commands are retired.

## Plan Gate And Handoff

A settled direction becomes Plan-ready only through accepted Collaborate state.
Planner may proceed only from case-v2 accepted readback: it confirms the selected
case manifest, accepted decision artifact, case path, manifest revision,
decision revision, semantic digest, lineage digest if present, digests,
acceptance evidence, and no open blockers/frontier. Generic Plan, Review,
result registration, legacy Design, conversational recommendation, adversarial
audit, hand-written file, or failed transaction cannot substitute.

Return a compact typed handoff with the packet fields, checkpoint
path/revision/digests, persistence disposition, blockers, and next workflow.
