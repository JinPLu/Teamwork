---
description: Start a Stop-hook-backed teamwork goal
argument-hint: <objective> [--max-iterations N] [--completion-promise TEXT]
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" goal-raw <<'RAO_GOAL_ARGS'
$ARGUMENTS
RAO_GOAL_ARGS
```

Use the `teamwork` skill with `mode: goal` now. Work autonomously until verified success, budget exhaustion, or a hard blocker. Do not ask the user during iteration unless blocked by destructive risk, auth/credentials, missing required external resources, sacred-boundary conflict, or an ambiguity that changes public behavior/contracts.
