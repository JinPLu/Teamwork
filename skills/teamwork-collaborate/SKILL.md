---
name: teamwork-collaborate
description: Use when the user wants dialogue, brainstorming, sustained questioning, grilling, stress-testing, or convergence on product, workflow, API, system, release, migration, permission, security, data, destructive, or cross-platform decisions before execution; activate aggressively from natural discussion or question-before-action intent, select dialogue/brainstorm/grill without asking, default-persist semantic checkpoints through Writer, and do not use for external research alone, unknown-cause debugging, implementation, review, or already accepted decisions.
---

# Teamwork Collaborate

Own one collaborative decision surface. Collaborate is the only public Teamwork
skill for natural dialogue, brainstorming, sustained questioning, grilling,
stress-testing, and decision convergence. It replaces the retired public
Discuss, Design, and Grill skill sources without aliases or compatibility public
surfaces. Internal Designer remains available only as a read-only leaf for
bounded challenge/audit; it never owns acceptance, persistence, questions,
planning, implementation, or release.

Root owns routing, questions, effect authority, integration, and final
acceptance. Writer is the only standalone document/artifact owner and sole
caller of managed artifact transactions. Collaborate does not authorize file
changes outside its checkpoint or effects/release/Plan/Review/implementation.

## Select Mode

Select the mode from user intent, current state, and evidence; do not ask the
user to name it.

- `dialogue`: synthesize, surface tensions, ask at most one open discriminator.
- `brainstorm`: widen options, compare meaningful choices, find the next
  discriminator.
- `grill`: pressure-test material user-owned decisions through a finite frontier
  with strict `global -> boundary -> detail` progression.

Mode changes are semantic Collaborate state, not separate owners. A settled
direction becomes Plan-ready only through accepted Collaborate state and the Plan
gate. Complexity alone does not require `grill`;
explicit sustained grilling, stress-testing, question-before-action, or major
public/installable/release/migration/permission/security/data/destructive/cross-platform
boundary normally does.

## Contribute Before Asking

Inspect supplied and discoverable evidence first. Before every question, give a
mode-appropriate contribution plus a provisional recommendation or next-best
judgment:

- dialogue: current synthesis, tension, and provisional next judgment;
- brainstorm: candidate space, constraints, tensions, and preferred/next-best
  option;
- grill: phase-appropriate decision map, risk boundary, or narrowed critique,
  plus the provisional recommendation and largest downside.

Ask only when unresolved user-owned feedback can change the next response,
persistence state, or execution boundary. Skip discoverable, safe-default,
reversible-detail, or answer-invariant questions.

Use one open prose question for sensemaking or clarification. Use host-native
bounded input only for genuine finite choices with two or three mutually
exclusive options. In Codex, call `request_user_input` when callable. A native
bounded batch contains at most three questions, all mutually independent:
no prompt, option, relevance, recommendation, or closing condition may depend on
another answer in the batch.

Dependent questions are serial: ask the question, wait for the answer, dispatch
Writer checkpoint when durable continuity is in scope, read back proof, then
continue. Never batch dependent questions or seek section approvals. Two rounds
with no closed decision, new discriminator, or changed recommendation are a
no-progress blocker.

## Grill Progression

Grill moves strictly `global -> boundary -> detail`.

1. Global: present the whole decision map, critical path, provisional
   recommendation, largest downside, and only boundary-setting choices.
2. Boundary: after the global answer and durable checkpoint when needed, test
   scope, permissions, data, migration, reversibility, public contract, rollout,
   and stop conditions.
3. Detail: after the boundary answer and checkpoint when needed, ask only detail
   decisions that still change the accepted outcome or downstream execution
   boundary.

For every bounded grill decision, state the recommendation, largest downside,
why the answer is critical, what it blocks, dependencies, and the observable
closing condition before asking. Frontier batches contain zero to three open
items and are replaced only by a semantic state update.

## Resolve Decisions

If evidence identifies one clear direction, recommend it and name the largest
downside. Otherwise compare two or three meaningful alternatives, including
status quo when relevant, by outcome, compatibility, complexity, operability,
reversibility, migration cost, risk, and canonical ownership.

Use internal Designer only for read-only challenge or audit when one of these is
true:

- the user explicitly requests adversarial search;
- at least two viable directions remain and costly or irreversible error or
  conflicting evidence makes ordinary challenge insufficient;
- a named risk gate requires isolated challenge before acceptance.

If adversarial search is selected, load `references/adversarial-search.md`. That
method replaces only the challenge method. It does not create a public Design
workflow, broaden authority, or permit persistence, Plan, implementation,
release, or acceptance without Collaborate transaction state.

Acceptance requires closure evidence: no current batch, open question, open
frontier, material frontier, unanswered current question, open items, or
blockers; `adversarial.status` is `not_run` or `pass`; `recommendation` is
nonempty; `acceptance_evidence` is nonempty. Pending or blocked Collaborate
records are durable but not Plan-ready.

## Persist Checkpoints

In an initialized writable project, sustained semantic Collaborate state
defaults to a managed Collaborate checkpoint: first substantive dialogue,
brainstorm, grill, stress-test, question-before-action state, decision update,
accepted decision, blocker, close, or supersede. Use aggressive persistence:
dispatch Writer before a dependent question and before handing an accepted
decision to Plan.

Route schema first from transaction evidence. Writer runs
`discussion-transaction.py case-inspect --project-root <project>` before routing.
If `schema_mode == legacy-v1`, use legacy Collaborate route below. If
`schema_mode == case-v2`, choose the supplied
`case_id`/alias from `active_cases`; when none exists, create one only from a
frozen seed/task_key, title, and aliases. Ambiguous selection, missing case
seed, mixed v1/v2, unknown, stale, or partial migration
fails closed before any write. One request never touches both memory trees.
v2 case-bundle writes only derived live collaborate/decision slots, never
legacy workflow dirs.

Negative overrides disable persistence: `no files`, `off-record`, `read-only`,
`no writes`, private/no-persistence equivalents, or explicit no-write
instruction. Continue collaboration and report unsaved state when it matters.
Missing memory, Writer, route, authority, consumer, or transaction
blocks durable claims; there is no Root, Designer, Worker, Reviewer, or direct
file-edit fallback.

Root freezes the bounded Collaborate packet and dispatches Writer. Writer calls
only the controlled transaction route and reads back proof before any durable
claim; it must not paraphrase, reinterpret, fill gaps, change, or summarize away
the frozen semantic packet. Missing packet state fails closed.

If legacy-v1, Writer uses:

1. `discussion-transaction.py collaborate-inspect --project-root <project>`;
2. `discussion-transaction.py collaborate-schema <create|update|accept|block|close|supersede>`;
3. `discussion-transaction.py collaborate-apply --project-root <project> --request <file>`.

In case-v2, Writer instead uses `case-inspect -> case-schema
<create|collaborate-upsert|accept-decision> -> case-apply ->
case-inspect/readback`. Map sustained checkpoints to `collaborate-upsert`,
accepted decisions to `accept-decision`, `update` only to phase/meta, and
`create` only with non-guessed case identity. The transaction derives paths,
manifest updates, `active_cases`, claim heads.

Read-only helpers `collaborate-render` and `collaborate-validate` verify
legacy-v1 state but never replace apply. Only legacy-v1 uses canonical current
path `docs/teamwork/collaborate/current.md`, archives, active pointer
`active.collaborate`, and the `collaborate-inspect` revision immediately before
legacy apply. In v2, derive `live/collaborate.md` + `decision.md`, manifest,
`active_cases`, and claim heads. Claim v2 durable state after case
apply/readback returns case path, manifest revision, and changed paths; claim
legacy after apply/readback returns path, decision id, Collaborate-scoped
revision, semantic digest, lineage digest, and changed paths.
Safe transaction failure grants no manual retry by editing Markdown, index,
fallback text, journals, or markers. `INDETERMINATE` pauses for recovery.

Legacy Discussion and Design artifacts are read-only migration inputs only.
Collaborate may import them through `collaborate-inspect` and
`collaborate-apply` with the consumed-source ledger. Legacy write lifecycle
commands are retired, and legacy mutation paths must not be treated as aliases,
fallbacks, or compatibility writes. Do not promote a conversational
recommendation, adversarial audit, hand-written file, failed transaction, or
legacy artifact alone into accepted Collaborate state.

## Plan Gate

Planner may proceed only from schema-specific accepted readback. For v2, Planner
runs `case-inspect`, reads the selected case manifest, and confirms the accepted
decision artifact plus manifest revision match the handoff. For legacy-v1,
Planner runs
`discussion-transaction.py collaborate-inspect --project-root <project>` and
confirms:

- `active.path == docs/teamwork/collaborate/current.md`;
- `active.acceptance == accepted`;
- the accepted path, decision id, revision, Collaborate-scoped revision,
  semantic digest, and lineage digest exactly match the handoff;
- `current_batch == []`;
- there are no open items, blockers, open questions, or open frontier records;
- `adversarial.status` is `not_run` or `pass`.

Generic Plan, Review, result registration, or legacy Design changes must not
substitute for this gate. Any Collaborate mutation changing pointer, bytes,
pointer/file consistency, semantic digest, lineage digest, closure state, or
decision identity must produce a new revision or fail validation.

## Handoff

Collaborate returns Root a compact typed handoff: goal, mode, synthesis,
evidence, settled items, candidate space, recommendation, largest downside,
decision rule, closure evidence, checkpoint path/revision/digests, open
questions/frontier, blockers, return path, and preserve/forbid boundaries. Root
chooses the next workflow. Complete the Collaborate checkpoint before dependent
work claims continuity.
