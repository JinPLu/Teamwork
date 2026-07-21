---
name: teamwork-design
description: Use when the user asks to design, architect, brainstorm, choose an approach, or resolve a material product, workflow, API, data-model, or system trade-off before implementation and the direction is not yet settled; do not use for external fact lookup alone, unknown-cause failures, an execution plan for an already chosen direction, clear implementation, or review.
---

# Teamwork Design

Settle a coherent direction before planning or implementation. Design is a hard
gate only for creative work, an unsettled direction, or a genuine material
trade-off. It is one self-contained owner, not a chain of Skills.

## Establish The Decision

Start with known local constraints and evidence before requesting any new
investigation. Use only the evidence required to resolve the decision. Dispatch Explorer only
when an unresolved local constraint, owner, interface, test, or prior decision
can change the choice and Root cannot answer it from evidence already in hand.
Dispatch Researcher only for a named external or current claim that can change
the choice, using a sanitized public question. Do not run both evidence tracks by
default, expose private project material, ask the user to rediscover local facts,
or request evidence without a decision-changing claim. Each invoked track gets
one initial evidence wave.

## Resolve Trade-offs

First decide whether a genuine material trade-off exists. If constraints point
to one clear direction, recommend it directly and do not manufacture alternatives
or ceremony.

For a genuine trade-off, generate two or three meaningful alternatives:

1. Generate two or three meaningfully different options, including the status
   quo when it is viable. Do not present cosmetic variations as alternatives.
2. Compare them against the same decision factors: user outcome, compatibility,
   complexity, operability, reversibility, migration cost, and relevant risk.
3. Lead with the recommended option and the strongest reason. State the main
   downside honestly. Give the recommendation before asking a question.
4. After recommending, perform exactly one challenge pass: identify the one to
   three assumptions it depends on; name the strongest disconfirming evidence or
   failure scenario; recheck status quo, canonical ownership, migration and
   reversibility; and ask whether a simpler existing pattern meets the outcome.
5. The challenge result is `survives`, one revised recommendation, or a named
   evidence or user-decision blocker. A direction-changing gap may trigger at
   most one targeted delta for each evidence track already justified by the gap
   and one integration revision; never reopen general brainstorming.

## Finite Decision Frontier

Root converts only unresolved user-owned choices that can change the direction
into a finite frontier, normally no more than three active unresolved items per
level. Publish the global map before details, ordered by `goal`, `boundary`, and
`detail`, and show the current critical path. Ask one bounded independent batch
at a time: one to three current choices whose answers cannot change each other's
prompt, options, recommendation, or closure signal. Dependent choices are
serial. Before each question, give the recommendation and largest downside, and
state why the answer is critical, what it blocks, its dependencies, and the
observable closing condition. In Codex, use `request_user_input` when callable
for the batch; otherwise use the host's native question surface or one concise
numbered batch. Answers close decisions; adjacent implementation preferences do
not create new ones. A new item requires new direct evidence that changes the
direction and must be recorded as a frontier delta.

Permit one integration revision after answers. If two consecutive rounds close
no decision, add no discriminating evidence, and do not change the recommendation,
stop with a no-progress blocker. Never batch dependent questions, send a
questionnaire, or seek repeated section approvals.

## Finish At The Design Boundary

If the direction is a major change (public/installable, release, permission,
security, data, destructive, cross-platform), also open the Grill record via
inspect->schema->apply unless no-files/off-the-record.

Freeze one durable Design before planning. Its structured Design state records the
outcome, decision rule, recommendation and largest downside, rejected alternatives,
key shape, boundaries, migration consequences, acceptance signals, challenge
outcome, frontier delta, and residual uncertainty or dissent.

The package-level Design transaction is the sole durable Design writer. Every
durable Design lifecycle uses this public route, in order:

1. Run `discussion-transaction.py design-inspect --project-root <project>` and
   use its active state and returned revision; never infer a revision or artifact
   path from files.
2. Run `discussion-transaction.py design-schema <create|update|supersede>` for
   the exact request skeleton. Set its `expected_revision` from inspect and fill
   its structured state. The destination is derived only from `state.slug` and
   `state.updated`; do not choose or invent a Design filename.
3. Run `discussion-transaction.py design-apply --project-root <project>` with its
   `--request <file>` or `--request-json <json>` input. It atomically renders,
   validates, and writes the artifact plus `active.design`, then returns its path,
   revision, and changed paths.

From a checkout use `<repo-root>/scripts/discussion-transaction.py`; from
Marketplace resolve the package root with `scripts/plugin-runtime-root.py` (two
levels up) first, then use that script.

`design-render` and `design-validate` are read-only helpers only; they never
replace the transaction. Never hand-author, redirect renderer output into, or
directly edit Design Markdown, its route map, or its text fallback. If the
controlled route is unavailable or fails validation, stop without claiming a
durable Design or substituting a hand-written artifact.

Design does not implement or silently enter Plan. Only after the controlled route returns
its path and revision may Planner produce a Plan. Independent Plan Review
runs only when the user requests it or a named material risk gate requires it.
Any Design or Plan approval still does not grant implementation or release
authority unless the user explicitly does so.
