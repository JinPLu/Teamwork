# Teamwork Runtime Index README

Optional durable project memory supplements direct inspection; it is not a
mandatory state machine.

## Read order

1. Read `docs/teamwork/index.json` when durable memory is relevant.
2. Follow the applicable active pointer, then linked artifact headers.
3. Read full artifact bodies only when their summaries are insufficient.

## Current anchors

- Active state: `docs/teamwork/current.md`
- Active Collaborate route: none
- Active Design route: none
- Active Plan route: none
- Active Goal progress: none

Initialized writable named workflows persist reusable checkpoints/results by
default; `no files`, off-record, read-only, or no-write overrides. One-shot
explanations, tiny native work, and clear code changes add no artifact. Writer
turns frozen briefs into managed artifacts without changing facts, citations,
decisions, status, authority, or acceptance.

Collaborate, Discuss, Design, and Goal use specialized transactions.
Collaborate is the unified public dialogue/brainstorm/grill and decision route;
it can consume legacy Discuss and Design state exactly once through its source
ledger. Discuss remains readable during migration, but new public checkpoints
use Collaborate. Design v3 records
`acceptance: pending`, `accepted`, or `blocked`; persistence is not acceptance,
and only `accepted` is Plan-ready. Legacy v1/v2 is read as `accepted`. Research,
Debug, Plan, Plan Review, Review, and mutating Init/Update use the generic
artifact transaction. A native execution may add one terminal `execution`
handoff only with a real consumer and no active Goal. `active.progress` is the
sole current pointer for Goal attempts and suppresses a separate execution
artifact. Explore creates no standalone report; its evidence is folded into the
consuming artifact. `conclusion` is reserved for a distinct user-requested
synthesis.

## Update rules

- Keep paths project-relative and inside `docs/teamwork/`.
- Replace the root digest when material project state changes; do not append a
  turn-by-turn log.
- Record only reusable conclusions, boundaries, evidence, and handoff state.
- Keep transient progress out of durable memory unless continuity needs it.

The index aids retrieval; it grants no execution authority or extra workflow.
