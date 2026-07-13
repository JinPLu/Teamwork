# Check Update

Use with `teamwork-init` (readiness gate) and `teamwork-update` (user refresh).

## Script

`./scripts/check-update.sh` reports Teamwork-controlled surfaces only:

- checkout `VERSION` vs upstream GitHub `VERSION`
- global skills/agents under `~/.codex`, `~/.cursor`, `~/.claude`
- skill file content drift against this checkout
- bounded Codex custom-agent routing readiness in `~/.codex/config.toml` (9 total threads: one main plus eight subagents)
- bootstrap policy markers (Codex/Claude managed files; Cursor UI paste)
- optional `--project PATH` for repo-local `.cursor/.codex/.claude`
- best-effort Cursor model slug sample and CodeGraph MCP detection

Flags:

- `--readiness` — compact init output (`INSTALL_READY`, `MISSING`, `NEXT`)
- `--project PATH` — include project-local install rows
- `--no-fetch` — skip git fetch and remote VERSION lookup

Normal report mode exits `0` when current and `1` when surfaces need action;
readiness reports convergence through `INSTALL_READY`.

## Init Readiness

Before project instruction work, run:

```bash
./scripts/check-update.sh --readiness --project "$PWD"
```

When `INSTALL_READY=no`, run `NEXT`, then continue local instructions, memory,
skills/agents, and any available CodeGraph index.

Only a user-level Codex install repairs `codex-routing`. Native interaction
tools belong to the current host/runtime; use them when callable and never
handwrite config to expose them. Restart Codex after a routing change.

Run `./install.sh cursor-policy-copy` when possible; report the unverifiable
manual Cursor User Rules paste.

Do not install external MCP/memory tools during the gate without user approval.

## User Update Mode

When the user asks to update or refresh Teamwork (not release a new version):

1. Run `./scripts/check-update.sh --project "$PWD"` (or without `--project`).
2. If checkout is behind upstream, `git pull` in the Teamwork repo with approval.
3. Run `./install.sh all --profile <profile>`; when project surfaces are stale,
   add `./install.sh --project-root "<project-path>" project`.
4. Use `./install.sh cursor-policy-copy` for Cursor User Rules paste when needed.
5. Restart Codex after routing changes; rerun the check and report gaps.

Do not bump `VERSION` or edit plugin manifests in user mode.

## Maintainer Update Mode

Use when changing Teamwork itself: semver bump, manifests, validation, release.
Follow `teamwork-update` maintainer workflow; run `./scripts/check-update.sh`
after `./install.sh all` to confirm surfaces match the new `VERSION`.

## Out of Scope

Project package managers, non-Teamwork MCP plugins, and live platform catalogs
are not checked; route them to native tooling or `teamwork-research` on request.
