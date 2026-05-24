---
description: Record review, verification, research reuse, routing, and rolling report row for the active teamwork goal
argument-hint: --plan-review-verdict <pass|pass-with-notes|revise|blocked> --execution-review-verdict <pass|pass-with-notes|revise|blocked> --verification-command <command> --verification-result <pass|fail> --evidence-delta <progress|no-progress> --research-disposition <none|reuse|update|new> --research-artifacts-read <text> --agent-routing-decision <text> [--attempt TEXT] [--changes TEXT] [--research-plan-decision TEXT] [--next-step TEXT]
---

Compatibility alias for `/teamwork:checkpoint`.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" checkpoint-raw <<'RAO_CHECKPOINT_ARGS'
$ARGUMENTS
RAO_CHECKPOINT_ARGS
```
