---
description: Record review, verification, evidence progress, and rolling report row for the active teamwork goal
argument-hint: --plan-review-verdict <pass|pass-with-notes|revise|blocked> --execution-review-verdict <pass|pass-with-notes|revise|blocked> --verification-command <command> --verification-result <pass|fail> --evidence-delta <progress|no-progress> [--attempt TEXT] [--changes TEXT] [--research-plan-decision TEXT] [--next-step TEXT]
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" checkpoint-raw <<'TEAMWORK_CHECKPOINT_ARGS'
$ARGUMENTS
TEAMWORK_CHECKPOINT_ARGS
```
