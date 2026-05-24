---
description: Start a Stop-hook-backed teamwork goal
argument-hint: 达成 <目标>，用 <可验证证据> 验收，保持 <限制条件> 不破坏，只允许使用 <输入/工具/文件边界>
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/raoctl.py" goal-raw <<'RAO_GOAL_ARGS'
$ARGUMENTS
RAO_GOAL_ARGS
```

Compatibility alias for `/teamwork:goal`.

Use the `teamwork-goal` skill with `mode: goal` now. Work autonomously until verified success, budget exhaustion, or a hard blocker. Recommended shape: `/teamwork:goal 达成 <目标>，用 <可验证证据> 验收，保持 <限制条件> 不破坏，只允许使用 <输入/工具/文件边界>，每轮根据 <下一步判断规则> 决策。` Treat angle brackets as prompt guidance only; do not leave them in artifacts. Before execution, create or read the durable plan artifact and record it with `/teamwork:plan` or `/rao:plan`. After every verification/review cycle, checkpoint and update the rolling report. Failed verification or failed review must refresh research and check plan adequacy before retry. Do not ask the user during iteration unless blocked by destructive risk, auth/credentials, missing required external resources, sacred-boundary conflict, or an ambiguity that changes public behavior/contracts.
