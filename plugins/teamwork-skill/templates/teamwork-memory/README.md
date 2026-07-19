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

Design, Plan, Goal progress, Research, and the ordinary current digest keep
separate paths and index ownership. `active.progress` is the sole current
pointer for durable Goal attempts. Grill discussions are intentionally absent
from this ordinary-memory index.

## Update rules

- Keep paths project-relative and inside `docs/teamwork/`.
- Replace the root digest when material project state changes; do not append a
  turn-by-turn log.
- Record only reusable conclusions, boundaries, evidence, and handoff state.
- Keep transient progress out of durable memory unless continuity needs it.

The index is a retrieval aid. It does not grant execution authority or impose
an additional workflow on simple work.
