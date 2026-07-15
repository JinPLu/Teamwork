# Teamwork Runtime Index README

## Purpose

This local runtime README is a short human entrypoint for ordinary,
non-discussion memory aligned with `docs/teamwork/index.json`.
Project instructions may point here, but should not inline this runtime
narrative.

## Read Order

1. For Grill/discussion continuation, load `grill-me`, resolve the installed
   `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill,
   and run `inspect` from the project root first.
   Its result is the sole discussion read path.
   For that continuation, do not directly read `index.json`,
   `current.md`, this README, or a discussion artifact.
2. For ordinary non-discussion memory, read `docs/teamwork/index.json` first,
   then this README.
3. Follow `active.current` and other non-discussion `active` pointers before
   any broad scan.
4. Prefer headers before full artifact bodies and use the stage-specific
   profiles from the index.

Legacy numeric budgets are compatibility retrieval hints, not execution limits
or hard stops. New indexes use header-first retrieval without numeric defaults.

## Stage Notes

- `research`: read topic headers first, then selective bodies.
- `discussion`: use the helper's `inspect` result; never open
  `active.discussion` or its artifact directly.
- `plan`: read active design/plan before adding or replacing plan state.
- `execute`: read active plan/progress before implementation updates.
- `review`: verify active claims against commands/logs/results.

## Current Anchors

- Active state: `docs/teamwork/current.md`
- The discussion anchor below is helper-managed metadata; never open it
  directly.
- Active discussion route: `none` or the exact `active.discussion` path from
  `index.json`

## Bounds

Keep this file concise and operational:

- max 120 lines
- max 1200 words
