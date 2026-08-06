# Teamwork for Cursor

Teamwork 7.1 does not officially support or release-qualify Cursor. This retained source adapter exists for compatibility maintenance and local development only; Codex is the supported install and release-evidence path.

The adapter still adds focused collaboration methods while leaving clear local inspection and implementation on Cursor's native path when you choose to test or maintain it.

## Compatibility Setup

```bash
./install.sh cursor
./install.sh cursor --profile cost-first
```

Run `./install.sh cursor-policy-copy`, review the canonical policy, and paste it
into Cursor User Rules. Teamwork cannot observe that setting, so readiness stays
`manual action required` / partial even when Skills and Agents are current.
Cursor controls models, permissions, MCP, and Agent execution.

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

Writer is the sole semantic writer for Discussion, Research, Debug, Plan,
Review, and Report documents, all discovered through `docs/teamwork/index.json`.
It writes only material reusable content and keeps storage mechanics out of
model-facing prose. Update migrates all Teamwork documents when given an exact
project root; otherwise it reports project migration as pending.

Older project documents migrate only through Update. Writer performs semantic
reorganization, scripts do mechanics, and an independent Reviewer accepts the
actual migrated corpus. After migration, Cursor uses only schema v4 and has no
legacy runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Readiness cannot verify the manually pasted User Rules, deterministic model
routing, or live external authentication. Cursor results are compatibility and
development signals only; they are not Teamwork 7.1 support claims or release
blockers.
