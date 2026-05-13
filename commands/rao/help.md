---
description: Show run-analyze-optimize goal command help
---

Run-analyze-optimize goal commands:

- `/rao:goal <objective> [--max-iterations N] [--completion-promise TEXT]` starts a Stop-hook-backed autonomous goal.
- `/rao:status` shows the active goal.
- `/rao:pause` pauses continuation.
- `/rao:resume` resumes continuation.
- `/rao:stop` stops continuation without deleting state.
- `/rao:complete` marks the goal complete.
- `/rao:clear` deletes the active goal state.
- `/rao:note <note>` appends context to the goal file.

State is stored under `.claude/run-analyze-optimize-goals/` in the current project.
