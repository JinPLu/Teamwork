---
name: teamwork-init
description: Use when the user asks to add or refresh concise project-local Teamwork instructions in one named project; do not use to install global tools or create workflow records.
---

# Teamwork Init

Init adds one small managed block to the project's `AGENTS.md`. It creates no
document database, schema, case directory, runtime state, or migration path.

## Method

1. Resolve the authorized project root and read its instruction hierarchy.
2. Preserve all user-owned content outside the Teamwork managed markers.
3. Run `./install.sh --project-root <root> init-project` from a trustworthy
   Teamwork package source.
4. Re-read the resulting `AGENTS.md` and report the exact changed surface.

The command is idempotent: an existing Teamwork block is refreshed in place.
Ambiguous duplicate markers or an unreadable target are real file-ownership
conflicts; version, schema, readiness, and agent availability are not Init
preconditions.

Init never creates `docs/teamwork` automatically. When its observed result is
worth reusing or the user explicitly requests a report, Root may ask Writer to
maintain one Markdown report from `references/report.md` at an
explicitly authorized path. Every wake-up supplies the document kind and path,
stable project-operation identity, authoritative Init owner, owner-certified
semantic delta, read-only context, and expected base. Writer records requested
versus observed outcome, decisive evidence, resulting state or changes,
remaining action or blocker, and dated history; it does not infer completion or
change authority, next action, or mainline. Existing history is immutable.
Writer failure does not block Init;
if the report was explicitly requested, only report delivery remains incomplete.
