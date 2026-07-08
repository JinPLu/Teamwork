# Check Update

Use with `teamwork-init` (readiness gate) and `teamwork-update` (user refresh).

## Script

`./scripts/check-update.sh` reports Teamwork-controlled surfaces only:

- checkout `VERSION` vs upstream GitHub `VERSION`
- global skills/agents under `~/.codex`, `~/.cursor`, `~/.claude`
- skill file content drift against this checkout
- bootstrap policy markers (Codex/Claude managed files; Cursor UI paste)
- optional `--project PATH` for repo-local `.cursor/.codex/.claude`
- best-effort Cursor model slug sample and CodeGraph MCP detection

Flags:

- `--readiness` — compact output for init (`INSTALL_READY`, `MISSING`, `NEXT`)
- `--project PATH` — include project-local install rows
- `--no-fetch` — skip git fetch and remote VERSION lookup

Exit `0` when current; `1` when stale/missing surfaces need action.

## Init Readiness

Before project instruction work, run:

```bash
./scripts/check-update.sh --readiness --project "$PWD"
```

When `INSTALL_READY=no`, run the printed `NEXT` equivalent directly during
init, then continue local project initialization. Do not stop before creating or
updating `AGENTS.md`, `docs/teamwork/`, project skills/agents, and repo-local
CodeGraph when the CLI is available.

Run `./install.sh cursor-policy-copy` when clipboard tooling exists; report the
remaining manual Cursor User Rules paste because Cursor UI state cannot be
reliably written by the installer.

Do not install external MCP/memory tools during the gate unless the user
approves via `optional-skills.md`.

## User Update Mode

When the user asks to update or refresh Teamwork (not release a new version):

1. Run `./scripts/check-update.sh --project "$PWD"` (or without `--project`).
2. If checkout is behind upstream, `git pull` in the Teamwork repo with approval.
3. Run `./install.sh all --profile <profile>`; add
   `./install.sh --project-root "<project-path>" project` when project-local
   surfaces are stale.
4. Use `./install.sh cursor-policy-copy` for Cursor User Rules paste when needed.
5. Re-run `./scripts/check-update.sh` and report remaining gaps.

Do not bump `VERSION` or edit plugin manifests in user mode.

## Maintainer Update Mode

Use when changing Teamwork itself: semver bump, manifests, validation, release.
Follow `teamwork-update` maintainer workflow; run `./scripts/check-update.sh`
after `./install.sh all` to confirm surfaces match the new `VERSION`.

## Out of Scope

Project package managers (npm, pip, cargo), non-Teamwork MCP plugins, and live
platform model catalogs are not checked. Route those to native tooling or
`teamwork-research` when the user asks explicitly.
