# Teamwork for Cursor

Teamwork adds focused collaboration methods while leaving clear local inspection and implementation on Cursor's native path.

## Setup

```bash
./install.sh cursor
./install.sh cursor --profile cost-first
```

If readiness reports a manual policy step, run `./install.sh cursor-policy-copy` and paste the result into Cursor User Rules. Cursor controls models, permissions, MCP, and agent execution.

Initialize a new project's current-format context with `./install.sh --project-root /path/to/project init-project`.

## Routing

- Local project evidence: native Cursor or internal Explorer.
- Discussion and unformed preference: `teamwork-collaborate`.
- Deep external research: `teamwork-research`.
- Unknown-cause failure: `teamwork-debug`.
- Selected direction: `teamwork-plan`.
- Stable implementation, document, or plan: `teamwork-review`.
- Explicit persistence: `teamwork-goal`.
- Project-local setup: `teamwork-init`.
- Global Teamwork refresh: `teamwork-update`.

The installed roles are Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer. Teamwork defines no fixed dispatch count. Use healthy `codegraph_*` MCP tools for structural questions when available.

Collaborate helps select an acceptable direction; Plan begins once that direction is selected. Neither step authorizes implementation.

Writer maintains one live document per task and keeps storage mechanics out of model-facing prose. Update migrates all Teamwork documents when given an exact project root; otherwise it reports project migration as pending.

Pre-7 project documents migrate only through Update. After migration, Cursor uses only the new format and has no legacy runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Readiness cannot verify the manually pasted User Rules, deterministic model routing, or live external authentication.
