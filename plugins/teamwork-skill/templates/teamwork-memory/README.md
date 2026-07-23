# Teamwork Runtime Index README

This directory stores optional durable project memory. It is not a mandatory
state machine and does not replace direct inspection of the current project.

## Read order

1. Read `docs/teamwork/index.json` when durable memory is relevant.
2. Follow the applicable active pointer, then linked artifact headers.
3. Read full artifact bodies only when their summaries are insufficient.

## Current anchors

- Active state: `docs/teamwork/current.md`
- Active Design route: none
- Active Plan route: none
- Active Goal progress: none

Named workflows in initialized writable projects persist by default; `no files`,
off-record, read-only, or no-write overrides that. Ordinary clarification or
chat, one-off native work, and clear code implementation requests do not force an
extra workflow artifact. Writer turns frozen bounded briefs into indexed
artifacts without researching, inventing, or changing facts, citations,
decisions, status, authority, or acceptance.

Grill, Design, and Goal use specialized transactions. Design v3 records
`acceptance: pending`, `accepted`, or `blocked`; persistence is not acceptance,
and only `accepted` is Plan-ready. Legacy v1/v2 is read as `accepted`. Research,
Debug, Plan, Review, and mutating
Init/Update use the generic artifact transaction. `active.progress` is the sole
current pointer for durable Goal attempts. Explore creates no standalone report;
its evidence is folded into the consuming artifact.

## Update rules

- Keep paths project-relative and inside `docs/teamwork/`.
- Replace the root digest when material project state changes; do not append a
  turn-by-turn log.
- Record only reusable conclusions, boundaries, evidence, and handoff state.
- Keep transient progress out of durable memory unless continuity needs it.

The index is a retrieval aid. It does not grant execution authority or impose
an additional workflow on simple work.
