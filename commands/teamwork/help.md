---
description: Show teamwork goal command help
---

Teamwork goal commands:

- `/teamwork:goal 达成 <目标>，用 <可验证证据> 验收...` starts a Stop-hook-backed autonomous goal.
- `/teamwork:plan <docs/teamwork/plans/...md>` records the active durable plan artifact.
- `/teamwork:checkpoint --plan-review-verdict <pass|pass-with-notes|revise|blocked> --execution-review-verdict <pass|pass-with-notes|revise|blocked> --verification-command <command> --verification-result <pass|fail> --evidence-delta <progress|no-progress> [--attempt TEXT] [--changes TEXT] [--research-plan-decision TEXT] [--next-step TEXT]` records review, verification, and rolling report state for the active plan SHA.
- `/teamwork:status` shows the active goal.
- `/teamwork:pause` pauses continuation.
- `/teamwork:resume` resumes continuation.
- `/teamwork:stop` stops continuation without deleting state.
- `/teamwork:complete` marks the goal complete as a manual override, not as automatically verified.
- `/teamwork:clear` deletes the active goal state.
- `/teamwork:note <note>` appends context to the goal file.

`/rao:*` remains available as a compatibility prefix. State is stored under `.claude/teamwork-goals/` in the current project.
