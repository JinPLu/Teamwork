---
name: teamwork-design
description: Use when the user asks to design, architect, choose an approach, resolve a material product, workflow, API, data-model, or system trade-off before implementation, or explicitly invokes Teamwork Design's adversarial strategy, and the direction is not yet settled; do not use for open-ended discussion-only brainstorming, external fact lookup alone, unknown-cause failures, an execution plan for an already chosen direction, clear implementation, or review.
---

# Teamwork Design

Settle one coherent direction before planning or implementation. Design is a
hard gate only for creative work, an unsettled direction, or a material
trade-off; it is one self-contained owner.

## Select The Search Strategy

Default Design uses the bounded comparison and exactly one challenge pass below.
Only Design-qualified explicit adversarial intent, such as
`$teamwork-design adversarial`, selects the stronger method. Bare brainstorming
language, risk, complexity, or Root preference never activates adversarial search.
When selected, load and follow `references/adversarial-search.md`; it replaces
the default challenge, not Design ownership, user-decision, persistence, or Plan
boundaries.

## Establish The Decision

Start with local constraints and evidence before requesting anything new.
Dispatch Explorer only when an
unresolved local constraint, owner, interface, test, or prior decision can change
the choice and Root cannot answer it from evidence in hand. Dispatch Researcher
only for a named external or current claim that can change the choice, using a
sanitized public question. Do not run both evidence tracks by default, expose
private material, ask the user to rediscover local facts, or investigate a claim
that cannot change the decision. Each invoked track gets one initial evidence
wave.

## Resolve Trade-offs

If constraints identify one clear direction, recommend it without manufacturing
alternatives. Otherwise:

1. Generate two or three meaningful alternatives, including a viable
   status quo; compare the same factors: outcome, compatibility, complexity,
   operability, reversibility, migration cost, and relevant risk.
2. Give the recommendation before asking a question: lead with its strongest
   reason, then its largest downside.
3. In the default strategy, after recommending, perform exactly one challenge pass:
   test its one to three key assumptions, strongest disconfirming evidence or
   failure, status quo, canonical ownership, migration, reversibility, and a
   simpler existing pattern.
4. Return `survives`, one revised recommendation, or a named evidence/user
   blocker. A direction-changing gap permits at most one targeted delta per
   already-justified evidence track and one integration revision; never reopen
   unrequested adversarial search.

## Finite Decision Frontier

Root converts only unresolved user-owned choices that can change the direction
into a finite frontier, normally at most three active items per level. Publish
the global map before details, ordered by `goal`, `boundary`, then `detail`, and
show the critical path. Ask one bounded independent batch at a time: one to three
choices whose answers cannot change each other's prompt, options,
recommendation, or closure signal. Dependent choices are serial. Before each
question, recommend an answer, give its largest downside, and state why the
answer is critical, what it blocks, its dependencies, and its observable closing
condition. Use `request_user_input` when callable; otherwise use the host's native
question surface or one concise numbered batch.

Answers close decisions; adjacent implementation preferences do not create new
ones. A new item requires direct direction-changing evidence and a frontier
delta. Permit one integration revision. If two consecutive rounds close no
decision, add no discriminating evidence, and leave the recommendation unchanged,
stop with a no-progress blocker. Never batch dependent questions or seek repeated
section approvals.

## Finish At The Design Boundary

For a major public/installable, release, permission, security, data, destructive,
or cross-platform direction, also open the Grill record through
inspect->schema->apply unless the user requested no files/off-record.

A conversational recommendation, including adversarial dual `PASS`, is not
durable or Plan-ready. Freeze one durable Design only after the user explicitly
accepts the direction and authorizes saving it. A Plan-ready handoff request
counts only when it explicitly accepts that direction and authorizes the save.
Its structured Design state records the outcome, rule, recommendation and
downside, rejected alternatives, key shape, boundaries, migration, acceptance
signals, challenge outcome, frontier delta, and uncertainty. For adversarial
Design also record the confirmed envelope, trials, taxonomy/coverage limit,
distinct critic and auditor identities, final verdicts, and rejected material
hypotheses; never store raw agent transcripts.

The package-level Design transaction is the sole durable Design writer. Every
durable Design lifecycle uses this public route, in order:

1. Run `discussion-transaction.py design-inspect --project-root <project>` and
   use its active state and returned revision; never infer either from files.
2. Run `discussion-transaction.py design-schema <create|update|supersede>` for
   the exact skeleton. Set its `expected_revision` from inspect and fill its
   structured state. Derive the destination only from `state.slug` and
   `state.updated`; never invent a filename.
3. Run `discussion-transaction.py design-apply --project-root <project>` with
   `--request <file>` or `--request-json <json>`. It atomically renders,
   validates, and writes the artifact plus `active.design`, returning its path,
   revision, and changed paths.

From a checkout use `<repo-root>/scripts/discussion-transaction.py`; from
Marketplace resolve the package root with `scripts/plugin-runtime-root.py` (two
levels up), then use that script.

`design-render` and `design-validate` are read-only helpers only; they never
replace the transaction. Never hand-author, redirect renderer output into, or
directly edit Design Markdown, its route map, or text fallback. If the controlled
route is unavailable or invalid, stop without claiming durable Design.

Design does not implement or silently enter Plan. Only after the controlled route returns
its path and revision may Planner produce a Plan. Independent Plan
Review runs only when the user requests it or a named material risk gate requires
it. Design or Plan approval does not grant implementation or release authority.
