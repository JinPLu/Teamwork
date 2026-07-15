# Project Init

Separate audit, deterministic bootstrap, and semantic init results. Bootstrap
refreshes package-owned regions and loaders while preserving outside content;
only semantic init claims evidenced organization.

## Evidence And Project Model

Before proposing edits, proportionally inspect: instructions/imports/managed blocks/human docs;
canonical project docs; source/config/tests/required values; commands;
trackers/runbooks/plans/Teamwork pointers; and platform or scoped Cursor surfaces.
Prefer declared canonical order; verify names, defaults, and bootstrap claims.

When useful, form the smallest init-local project model needed: outcome,
mainline, owners/source order, platform entrypoints and real deltas, boundaries,
sourced values, verification, and unresolved conflicts. Give every rule or
fact one primary owner; other surfaces link to it or contain only a real delta.
Omit unknowns and scale to the request. Never persist this internal aid.

Optional internal classifications are `keep`, `merge`, `migrate`, `remove`,
`create`, and `unresolved`. Send only material unresolved conflicts through the
Ask Gate; preserve competing claims and pause dependent edits.

When changing an internal workflow or instruction rule, audit its canonical
owner, user effect, and verification. Give the user a plain-language summary of
what changes for them; do not substitute internal classifications or process
narration for that explanation.

## Ownership And Time Horizon

- Root `AGENTS.md` owns shared stable Codex and Cursor project instructions:
  identity/map, owners, checks, sourced values, boundaries, and preferences;
  nested files may own scoped facts.
- Ordinary root `CLAUDE.md` imports `@AGENTS.md`, keeps only nonduplicated
  Claude-specific deltas, and preserves unrelated human/project docs. Teamwork's
  own public `CLAUDE.md` guide stays intact; at most add a minimal loader. Claude
  Code expands the import when the session launches; package checks prove only
  that the loader and files were emitted, not that a live session loaded them.
- `.cursor/rules` holds only genuinely path-scoped rules that cannot safely live
  in the shared root. Cursor supports root `AGENTS.md` as its simple project-rule
  alternative. `CODEX.md` and `CURSOR.md` remain docs absent contrary evidence.
- Stable instructions keep durable facts, checks, invariants, boundaries, and
  preferences. Runtime
  environment, GPU allocation, checkpoint path/status, run progress, experiment numbers,
  summaries, blockers, and narrow narration are volatile; keep them in their
  canonical tracker or triggered memory, not stable instructions.

Reuse the canonical tracker/runbook. Create fallback `docs/teamwork/project.md` only
for durable cross-task need, no equivalent, and write authority; it remains a
runbook and grants no Git, publication, release, or protected-state authority.
A narrow plan, including a StateConflict-like local plan, stays subordinate to
the canonical tracker; record it as the current topic with that tracker as its
parent rather than promoting it to `active.mainline`.

An equivalent second semantic audit with no new evidence, classification, or
mainline change writes nothing and reports `no-change`.

## Safe Migration
For automatic migration, preserve unrelated content; validate schema, anchors,
uniqueness, and intent; then use a recoverable same-filesystem transaction.
Caught failures restore exact old bytes. A hard interruption may briefly leave
mixed bytes, but a durable marker blocks protocol reads and writes; the next
locked init rolls back before commit or finishes cleanup after it. Without a
safe migrator, preserve the legacy or custom content and report a candidate.

## Readiness, Capability, And Output

Profiles are install-time; ask only about unresolved material overrides. With
authority, run readiness and the accepted target. Teamwork skills and agents are
global-install surfaces. `init-project` refreshes them globally, then updates
only project instructions, memory, and optional CodeGraph context; it does not
install, refresh, or check project-local Teamwork skill or agent copies. Native
tools are not install requirements; installing tools or changing host config
needs separate authority.

Only an explicitly requested full bootstrap returns a Capability Matrix. Name
the state and next action for each requested capability. CodeGraph initialization
requires its CLI and bootstrap authority.

Ordinary output covers the selected surface, material ownership/mainline,
changes, conflicts, and verification. Do not force internal models,
classifications, or a Memory Delta into it. Legacy numeric index budgets remain
retrieval hints, not execution limits.
Never infer live Codex, Cursor, or Claude behavior from static
inspection, bootstrap checks, emitted loaders/files, or deterministic fixtures.
