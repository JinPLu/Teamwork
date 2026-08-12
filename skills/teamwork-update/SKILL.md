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
4. Preserve unknown and user-owned files. Replace only recognizable
   Teamwork-owned surfaces.
5. Re-run the same focused check and report what changed and any manual restart
   still needed.

Do not inspect or migrate project documents, compare project schemas, fetch
release state, modify unrelated plugins or credentials, or require any agent to
perform a readiness check. A missing specialized agent never makes Update a
precondition for native work.
