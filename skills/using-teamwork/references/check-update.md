# Check Update

Use with `teamwork-init` (readiness gate) and `teamwork-update` (user refresh).

## Script

`./scripts/check-update.sh` reports Teamwork-controlled surfaces only:

- checkout `VERSION` vs upstream GitHub `VERSION`
- best-effort remote semver tag and latest GitHub Release vs checkout `VERSION`
- global skills/agents under `~/.codex`, `~/.cursor`, `~/.claude`
- skill file content drift against this checkout
- bounded Codex custom-agent routing readiness in `~/.codex/config.toml` (9 total threads: one main plus eight subagents)
- bootstrap policy markers (Codex/Claude managed files; Cursor UI paste)
- optional `--project PATH` for repo-local Codex `.agents/skills/`, Cursor
  `.cursor/skills/`, Claude Code `.claude/skills/`, and each platform's agents
- best-effort Cursor model slug sample and CodeGraph MCP detection
- Codex notification installation and runtime trust (`review-required` until both exact hooks are trusted)

Flags:

- `--readiness` — compact init output (`INSTALL_READY`, `MISSING`, `NEXT`)
- `--project PATH` — include project-local install rows
- `--no-fetch` — skip git fetch and remote VERSION lookup

Normal report mode exits `0` when current and `1` when surfaces need action;
readiness reports convergence through `INSTALL_READY`.
Project readiness uses host-specific `project-codex-*`, `project-cursor-*`, and
`project-claude-*` entries for missing skills, content drift, and version drift.

## Init Readiness

Before project instruction work, run:

```bash
./scripts/check-update.sh --readiness --project "$PWD"
```

When `INSTALL_READY=no`, run `NEXT`, then continue local instructions, memory, skills/agents, and any available CodeGraph index.

Only a user-level Codex install repairs `codex-routing`. Native interaction
tools belong to the current host/runtime; use them when callable and never
handwrite config to expose them. Restart Codex after a routing change.

Run `./install.sh cursor-policy-copy` when possible; report the unverifiable manual Cursor User Rules paste.

Do not install external MCP/memory tools during the gate without user approval.

## User Update Mode

When the user asks to update or refresh Teamwork (not release a new version):

1. Run `./scripts/check-update.sh --project "$PWD"` (or without `--project`).
2. If checkout is behind upstream, `git pull` in the Teamwork repo with approval.
3. Run `./install.sh all --profile <profile>`; it installs Codex/Claude notifications unless explicitly opted out. Add project install when stale.
4. Use `./install.sh cursor-policy-copy` for Cursor User Rules paste when needed.
5. Restart Codex after routing changes; rerun the check. For `review-required`, verify the exact command in `/hooks` and trust only `Stop` and `PermissionRequest`.

Do not bump `VERSION` or edit plugin manifests in user mode.

## Maintainer Update Mode

For Teamwork semver, manifests, validation, or release, follow `teamwork-update`; run `check-update.sh` before and after publication to verify installs, tag, and Release.

## Out of Scope

Project package managers, non-Teamwork MCP plugins, and live platform catalogs
are not checked; route them to native tooling or `teamwork-research` on request.
