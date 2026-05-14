---
description: Record review, verification, and evidence progress for the active teamwork goal
argument-hint: --plan-review-verdict <pass|pass-with-notes|revise|blocked> --execution-review-verdict <pass|pass-with-notes|revise|blocked> --verification-command <command> --verification-result <pass|fail> --evidence-delta <progress|no-progress>
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" checkpoint-raw <<'TEAMWORK_CHECKPOINT_ARGS'
$ARGUMENTS
TEAMWORK_CHECKPOINT_ARGS
```
