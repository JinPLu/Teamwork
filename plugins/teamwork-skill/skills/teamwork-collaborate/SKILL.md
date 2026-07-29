---
name: teamwork-collaborate
description: Use when the user wants dialogue, brainstorming, sustained questioning, grilling, stress-testing, or convergence on a product, workflow, API, system, release, migration, permission, security, data, destructive, or cross-platform decision before execution; activate aggressively from natural discussion or question-before-action intent, select dialogue, brainstorm, or grill without asking for a mode, default-persist semantic checkpoints through Writer in initialized writable projects, and do not use for external research alone, unknown-cause debugging, implementation, review, or a plan after the decision is already accepted.
---

# Teamwork Collaborate

Own one collaborative decision surface. Collaborate is the only public Teamwork
skill for natural dialogue, brainstorming, sustained questioning, grilling,
stress-testing, and decision convergence. It replaces the retired public
Discuss, Design, and Grill skill sources without aliases or compatibility public
surfaces. Internal Designer remains available only as a read-only leaf for
bounded challenge or audit work; it is not a public workflow and never owns
acceptance, persistence, questions, planning, implementation, or release.

Root owns routing, user questions, effect authority, integration, and final
acceptance. Writer is the only standalone document/artifact owner and the sole
caller of managed artifact transactions. Collaborate does not authorize file
changes outside its checkpoint, external effects, publication, release, Plan,
Review, implementation, or acceptance by another workflow.

## Select Mode

Select the mode from user intent, current state, and evidence; do not ask the
user to name it.

- `dialogue`: build shared understanding through synthesis, tensions, and at
  most one open prose discriminator.
- `brainstorm`: widen the candidate space, compare meaningful options, and
  identify the next steering discriminator.
- `grill`: pressure-test material user-owned decisions through a finite frontier.
  Use strict `global -> boundary -> detail` progression.

Mode changes are semantic Collaborate state changes, not separate workflow
owners. A settled direction becomes Plan-ready only through an accepted
Collaborate state and the Plan gate. Complexity alone does not require `grill`,
but explicit sustained grilling, stress-testing, question-before-action, or a
major public, installable, release, migration, permission, security, data,
destructive, or cross-platform boundary normally does.

## Contribute Before Asking

Inspect supplied and discoverable evidence first. Before every question, give a
mode-appropriate contribution plus a provisional recommendation or next-best
judgment:

- dialogue: current synthesis, central tension, and a provisional next judgment;
- brainstorm: candidate space, constraints, tensions, and the current preferred
  option or next-best option;
- grill: phase-appropriate decision map, risk boundary, or narrowed critique,
  plus the provisional recommendation and largest downside.

Ask only when unresolved user-owned feedback can materially change the next
response, persistence state, or execution boundary. Skip questions whose answer
is discoverable from available evidence, has a safe default, is reversible
implementation detail, or would not affect the outcome.

Use one open prose question for sensemaking, clarification, or exploratory
answers. Use host-native bounded input only for genuine finite choices with two
or three mutually exclusive options. In Codex, call `request_user_input` when it
is callable. A native bounded batch contains at most three questions, and every
question in the batch must be mutually independent: no prompt, option,
relevance, recommendation, or closing condition may depend on another answer in
the same batch.

Dependent questions are serial. Ask the question, wait for the answer, dispatch
Writer checkpoint after a semantic answer when durable continuity is in scope,
read back transaction proof, then proceed to the next dependent question. Never
batch dependent questions or seek repeated section approvals. Two consecutive
rounds that close no decision, add no discriminating evidence, and leave the
recommendation unchanged are a no-progress blocker.

## Grill Progression

Grill moves strictly `global -> boundary -> detail`.

1. Global: present the whole decision map, critical path, provisional
   recommendation, largest downside, and only the global decisions needed to
   choose the boundary.
2. Boundary: after the relevant global answer is received and checkpointed when
   durable, test scope, permissions, data, migration, reversibility, public
   contract, rollout, and stop conditions.
3. Detail: after the relevant boundary answer is received and checkpointed when
   durable, ask only detail decisions that still change the accepted outcome or
   downstream execution boundary.

For every bounded grill decision, state the recommendation, largest downside,
why the answer is critical, what it blocks, dependencies, and the observable
closing condition before asking. Current frontier batches contain zero to three
open items and are replaced only by a semantic state update.

## Resolve Decisions

If evidence identifies one clear direction, recommend it directly and name the
largest downside. Otherwise compare two or three meaningful alternatives,
including a viable status quo when relevant. Evaluate outcome, compatibility,
complexity, operability, reversibility, migration cost, risk, and canonical
ownership.

Use internal Designer only for read-only challenge or audit when one of these is
true:

- the user explicitly requests adversarial search;
- at least two viable directions remain and costly or irreversible error or
  conflicting evidence makes ordinary challenge insufficient;
- a named risk gate requires isolated challenge before acceptance.

If adversarial search is selected, load and follow
`references/adversarial-search.md`. That method replaces only the challenge
method. It does not create a public Design workflow, broaden authority, or
permit persistence, Plan, implementation, release, or acceptance without the
Collaborate transaction state.

Acceptance requires closure evidence: no current batch, no open question, no
open frontier, no material frontier, no unanswered current question, no open
items, no blockers, `adversarial.status` is `not_run` or `pass`,
`recommendation` is nonempty, and `acceptance_evidence` is nonempty. Pending or
blocked Collaborate records are durable but not Plan-ready.

## Persist Checkpoints

In an initialized writable project, sustained semantic Collaborate state
defaults to a managed Collaborate checkpoint. This includes the first
substantive dialogue, brainstorm, grill, stress-test, question-before-action
state, material decision update, accepted decision, blocker, close, or supersede.
Use aggressive persistence for durable continuity: dispatch Writer before asking
a dependent question and before handing an accepted decision to Plan.

Negative overrides disable persistence: `no files`, `off-record`, `read-only`,
`no writes`, private/no-persistence equivalents, or an explicit instruction that
this conversation must not be written. With a negative override, continue the
collaboration and report unsaved state when it matters. Missing initialized
memory, Writer, route, authority, consumer, or transaction blocks durable claims;
there is no Root, Designer, Worker, Reviewer, or direct file-edit fallback.

Root freezes the bounded Collaborate packet and dispatches Writer. Writer calls
only the controlled transaction route and reads back proof before any saved or
durable claim. Writer must not paraphrase, reinterpret, fill gaps in, change, or
summarize away the frozen semantic packet before apply; missing required packet
state fails closed instead of guessing:

1. `discussion-transaction.py collaborate-inspect --project-root <project>`;
2. `discussion-transaction.py collaborate-schema <create|update|accept|block|close|supersede>`;
3. `discussion-transaction.py collaborate-apply --project-root <project> --request <file>`.

Read-only helpers `collaborate-render` and `collaborate-validate` may verify
state but never replace apply. The canonical current path is
`docs/teamwork/collaborate/current.md`; archives use
`docs/teamwork/collaborate/YYYY-MM-DD-slug.md` with numeric collision suffixes;
the active pointer is `active.collaborate` in `docs/teamwork/index.json`.
Writer must use the `collaborate-inspect` revision immediately preceding apply.
Only claim durable state after apply/readback return path, decision id,
Collaborate-scoped revision, semantic digest, lineage digest, and changed paths.
Safe transaction failure grants no manual retry by editing Markdown, index,
Mermaid, fallback text, journal files, or transaction markers. An
`INDETERMINATE` result pauses for recovery.

Legacy Discussion and Design artifacts are read-only migration inputs only.
Collaborate may import them through `collaborate-inspect` and
`collaborate-apply` with the consumed-source ledger. Legacy write lifecycle
commands are retired, and legacy mutation paths must not be treated as aliases,
fallbacks, or compatibility writes. Do not promote a conversational
recommendation, adversarial audit, hand-written file, failed transaction, or
legacy artifact alone into an accepted Collaborate state.

## Plan Gate

Planner may proceed from a prior Collaborate decision only when the handoff
freezes path, decision id, Collaborate-scoped revision, semantic digest, and
lineage digest from an accepted readback. Planner must run
`discussion-transaction.py collaborate-inspect --project-root <project>` and
confirm:

- `active.path == docs/teamwork/collaborate/current.md`;
- `active.acceptance == accepted`;
- the accepted path, decision id, revision, semantic digest, and lineage digest
  exactly match the handoff;
- `current_batch == []`;
- there are no open items, blockers, open questions, or open frontier records;
- `adversarial.status` is `not_run` or `pass`.

Generic Plan, Review, result registration, or legacy Design changes must not
substitute for this gate. Any Collaborate mutation that changes the pointer,
current artifact bytes, pointer/file consistency, semantic digest, lineage
digest, closure state, or decision identity must produce a new revision or fail
validation.

## Handoff

Collaborate returns Root a compact typed handoff: goal, mode, synthesis,
evidence, settled items, candidate space, recommendation, largest downside,
decision rule, closure evidence, checkpoint path/revision/digests, open
questions or frontier, blockers, return path, and preserve/forbid boundaries.
Root chooses the next workflow. Complete the Collaborate checkpoint before
dependent work claims continuity.
