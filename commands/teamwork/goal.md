---
description: Start a Stop-hook-backed teamwork goal
argument-hint: <objective> [--max-iterations N] [--completion-promise TEXT]
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" goal-raw <<'TEAMWORK_GOAL_ARGS'
$ARGUMENTS
TEAMWORK_GOAL_ARGS
```

Use the `teamwork-goal` skill with `mode: goal` now. Work autonomously until verified success, budget exhaustion, or a hard blocker. Before execution, create or read the durable plan artifact and record it with `/teamwork:plan`. Do not ask the user during iteration unless blocked by destructive risk, auth/credentials, missing required external resources, sacred-boundary conflict, or an ambiguity that changes public behavior/contracts.
