# Teamwork Runtime Index README

## Purpose

This local runtime README is a short human entrypoint aligned with
`docs/teamwork/index.json`.
Project instructions may point here, but should not inline this runtime
narrative.

## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the
   other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.

## Stage Notes

- `research`: read topic headers first, then selective bodies.
- `discussion`: read the active discussion before continuing dependent work.
- `plan`: read active design/plan before adding or replacing plan state.
- `execute`: read active plan/progress before implementation updates.
- `review`: verify active claims against commands/logs/results.

## Memory Delta Reminder

At non-lightweight stage exit, report one disposition:
`none | current | plan | research | decision | supersede | compact | deferred`.

## Bounds

Keep this file concise and operational:

- max 120 lines
- max 1200 words
