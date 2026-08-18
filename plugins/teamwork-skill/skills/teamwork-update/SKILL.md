---
name: teamwork-update
description: Use when the user asks to inspect, install, or refresh Teamwork-owned global surfaces; do not use as a prerequisite for another skill or to migrate project documents.
---

# Teamwork Update

Update is a small install and refresh operation. It is never an automatic detour
from another task.

## Method

1. Resolve a trustworthy Teamwork package source.
2. For a check-only request, run `./scripts/check-update.sh --readiness`. Treat
   the output as diagnostic information, not permission to continue other work.
3. For an authorized refresh, update only the requested host. The default
   `update` target refreshes Codex; Cursor or Claude adapters require explicit
   targets.
   When refreshing an intentionally revised Agent profile, keep
   `performance-first` and `cost-first` distinct and compare task success,
   elapsed time, and cost together instead of maximizing model or effort.
   For a Codex profile refresh, update both the role profiles and the
   top-level main-thread default while preserving other user configuration:
   `performance-first` uses Terra/xhigh and `cost-first` uses Luna/high.
4. Preserve unknown and user-owned files. Replace only recognizable
   Teamwork-owned surfaces.
5. Re-run the same focused check and report what changed or the observed no-op,
   and any manual restart still needed.

Do not inspect or migrate project documents, compare project schemas, fetch
release state, modify unrelated plugins or credentials, or require any agent to
perform a readiness check. A missing specialized agent never makes Update a
precondition for native work. When Update observes no change, report the
observed no-op. Create or update a durable report only when that result is
reusable or the user explicitly requests it.

## Persistence

Persistence is optional. Write a report only when the observed result is reusable
across sessions or the user explicitly requests it. When that optional
checkpoint fires, write the document in the same response cycle from
`references/report.md` at
`docs/teamwork/reports/<YYYY-MM-DD>-<slug>.md` (reuse the existing path for the
same operation identity). Optional triggers: an authorized refresh completes
with observed surface changes worth reusing; Update stops on a real blocker
worth reusing; or a no-op result is reusable or explicitly requested.

Every Writer wake-up supplies the document kind and path, stable operation
identity, authoritative Update owner, owner-certified semantic delta, read-only
context, and expected base. The report preserves requested versus observed
outcome, decisive evidence, resulting state or changes, remaining action or
blocker, and dated history; it is not an activity log and does not claim
unobserved completion. Writer only compresses literally, locates, deduplicates
the current synthesis and pending delta, updates the current synthesis, and
appends history. Existing history is immutable. It cannot change authority,
completion, next action, or mainline.

Writer is a helper role, not a Skill. There is no `teamwork-writer` Skill.
Host interaction surfaces, ephemeral host plan files, the conversation body,
and experiment logs do not satisfy persistence. Root owns document delivery.
Root may write the same template directly or delegate to Writer only when that
does not delay the current checkpoint write. Update never blocks on a report.
