# Project Init

Keep their results separate: `teamwork-init` audit, deterministic bootstrap, and
semantic init. Bootstrap refreshes Teamwork-owned managed blocks/entries and the exact loader,
preserves content outside managed regions, and reports semantic audit pending;
content inside Teamwork markers is package-owned. Only semantic init claims
evidenced organization.

## Evidence And Project Model

Before proposing edits, proportionally inspect: instructions/imports/managed blocks/human docs;
canonical project docs; source/config/tests/required values; commands;
trackers/runbooks/plans/Teamwork pointers; and platform or scoped Cursor surfaces.
Prefer declared canonical order; verify names, defaults, and bootstrap claims.

Form the smallest init-local Project Model needed: audience/outcome/success;
mainline, workstreams, current topic parent; owners/source order; each platform's instruction/loading entrypoint plus only its
platform-specific deltas; stable boundaries, sourced values, protected actions,
verification entrypoints; and unresolved material conflicts. Give every rule or
fact one primary owner; other surfaces link to it or contain only a real delta.
Omit unknowns and scale to the request. Never persist this
model as an object, template, file, skill, stage, route, mode, artifact, or state
machine.

Classify every relevant rule: `keep` accurate stable ownership; `merge` overlapping
truth; `migrate` truth in the wrong owner/surface; `remove` stale,
contradicted, duplicate, or package-owned workflow; `create` missing evidenced
stable guidance; `unresolved` material conflict. Continue reversible work. Send only unresolved conflict affecting behavior, public outcome, acceptance, authority, or protection to the root Ask Gate; preserve both claims and pause only dependent edits.

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
For automatic migration: transform a same-filesystem temporary copy; preserve
unrelated/custom content; validate schema, anchors, uniqueness, and intent; then
atomically replace. Failure must leave destination bytes unchanged. Without a safe
migrator, preserve the legacy or custom key/content and report a candidate.

## Readiness, Capability, And Output

Profiles are install-time; ask only about unresolved material overrides. With
authority, run readiness and the accepted target. Skill roots are Codex
`.agents/skills/`, Cursor `.cursor/skills/`, and Claude `.claude/skills/`; agents
stay in host roots. Native tools are not install requirements; installing tools
or changing host config needs separate authority.

Full bootstrap returns a Capability Matrix: Core workflow; profile; instruction
layer; memory; CodeGraph; subagents; role contracts; validation; optional docs
graph/external memory; blockers. Use `enabled`, `missing`, `blocked`, `optional`,
or `deferred`; non-enabled rows name a next action. CodeGraph initialization requires existing CLI plus bootstrap authority.

Semantic output includes selected surface; separate bootstrap/semantic results;
Project Model; six classifications; mainline; files; migration; conflicts/decisions;
verification tier. Never infer live Codex, Cursor, or Claude behavior from static
inspection, bootstrap checks, emitted loaders/files, or deterministic fixtures.
