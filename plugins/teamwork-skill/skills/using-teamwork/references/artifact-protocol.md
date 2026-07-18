# Artifact Protocol

Research, plan, and report artifacts remain under
`docs/teamwork/` directories. A discussion record is supporting continuity only:
it is not a transcript or execution authority, and stays subordinate to canonical
project sources.

## Discussion Triggers

Create `docs/teamwork/discussion/YYYY-MM-DD-<slug>.md` only when at least one
observable condition holds:

- the user explicitly asks to save or resume later;
- a known handoff or context compaction is approaching;
- a material conclusion is settled and a distinct comparison, measurement, or
  decision remains open before the next action;
- one decision has at least three real branches.

Time, word count, and a short Grill never trigger persistence. These conditions
decide usefulness, never authority. Creation and later updates require authority;
a user-originated challenge or natural question-first request is explicit Grill
and grants only its supporting discussion-record lifecycle unless the user says
no files. Plan complexity and artifact usefulness never activate Grill or grant
discussion-record authority.

Do not wait for a second settled choice when the first conclusion already
determines an open next check. The record exists to preserve that conclusion,
its basis, and the unresolved discriminator—not to archive a long conversation.

## Content and Lifecycle

Keep privacy-safe summaries, never hidden reasoning, secrets, unnecessary
personal data, or a transcript. A recoverable record contains a title
and five sections: Goal, Settled (including reasons), Still open, Key evidence,
and Continue here. A Decision map is optional only when it clarifies at least
three branches.

Update only when the user's new input changes saved decisions, evidence, or the
continuation point, not merely because a turn resumed. Opening, recovering, or
reading an existing discussion is read-only: after `inspect`, do not run `schema`
or `apply`; ask the saved unresolved question. The user's stated
Grill scope defines closure; when every decision in it is settled, close without
adding an adjacent question. Closing as accepted clears active discussion state.
Superseding without replacement clears it. Replacement atomically supersedes the
old record, links it to the new record, and activates the new one; never close and
then create as separate transactions. Discussion authority remains supporting,
and confirmation or promotion does not authorize execution.

## Canonical Transaction

Resolve `scripts/discussion-transaction.py` from the already loaded
`using-teamwork` skill root. This helper is the sole runtime path for discussion
state:

1. From the project root, run `inspect`; the helper defaults its project root to
   the current directory. Its result is the only discovery and reading source for
   canonical discussion state, anchors, and artifacts; do not directly read
   `index.json`, `current.md`, `README.md`, or a discussion artifact.
2. Decide create, update, close, supersede, or replace from that state. Run
   `schema <operation>` and fill exactly its JSON shape; never inspect helper
   source. The helper derives the path, index entry, and rendered artifact.
3. Reuse the opaque `revision` unchanged in exactly one
   `apply --request-json <JSON>`, or `--request <file>` when quoting is unsafe.
   Never use stdin. `apply` is the only writer and performs replacement atomically;
   do not edit canonical files or substitute shell, validators, or another transaction.

Never manually repair or complete canonical state after a nonzero helper exit.
For unsafe, partial, `INDETERMINATE`, stale, malformed, or other helper failure,
stop the dependent question and any completion claim.

Before writing, absent discussion authority, `initialized: false`, a user
no-files request, or host read-only state uses a natural-language fallback: goal,
settled choices, open choice, key evidence, and continuation point. State once
that it was not saved and may be lost across sessions. Do not use this fallback
after an attempted `apply`.

After successful `apply`, ask or complete. In an ordinary reply, describe only
the continuity result: saved decisions, current resume context, or completed
discussion. A brief skill name or purpose is welcome when it helps explain a
capability, limit, or choice; omit paths, gates, checks, test/process inventory,
and invented labels.

## Other Artifacts

Research stores reusable or high-risk evidence; plans store accepted shared or
high-risk scope; reports store reusable results. Each uses a retrieval header
with type, status, last update, search keys, abstract, and linked artifacts.
Create or update them only when their owning stage and authority allow it.
External calibration alone is not a write trigger.
