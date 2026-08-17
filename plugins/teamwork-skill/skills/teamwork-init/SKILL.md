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
4. Re-read the resulting `AGENTS.md` and report the exact changed surface or
   the observed no-op.

The command is idempotent: an existing Teamwork block is refreshed in place.
Ambiguous duplicate markers or an unreadable target are real file-ownership
conflicts; version, schema, readiness, and agent availability are not Init
preconditions.

Init never creates an empty `docs/teamwork` tree. Document directories appear only
when a Skill checkpoint asks Writer to write a file there. When Init observes
no change, report the observed no-op. Create or update a durable report only
when that result is reusable or the user explicitly requests it.

## Persistence

Persistence is optional. Write a report only when the observed result is reusable
across sessions or the user explicitly requests it. When that optional
checkpoint fires, prefer Writer from `references/report.md` at
`docs/teamwork/reports/<YYYY-MM-DD>-<slug>.md` (reuse the existing path for the
same project-operation identity). Optional triggers: Init completes with an
observed `AGENTS.md` change worth reusing; Init stops on a real file-ownership
conflict worth reusing; or a no-op result is reusable or explicitly requested.

Every Writer wake-up supplies the document kind and path, stable
project-operation identity, authoritative Init owner, owner-certified semantic
delta, read-only context, and expected base. Writer records requested versus
observed outcome, decisive evidence, resulting state or changes, remaining
action or blocker, and dated history; it does not infer completion or change
authority, next action, or mainline. Existing history is immutable.

Writer is a helper role, not a Skill. There is no `teamwork-writer` Skill.
Host interaction surfaces, ephemeral host plan files, the conversation body,
and experiment logs do not satisfy persistence. Prefer Writer when writing;
if Writer is unavailable, Root may write the same template and mark Root
fallback in the closeout. Init never blocks on a report. Silently skipping after
choosing to persist is a Skill violation.
