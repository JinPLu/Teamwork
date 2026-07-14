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
- best-effort Cursor model slug sample and CodeGraph MCP detection
- Codex notification installation and runtime trust (`review-required` until both exact hooks are trusted)

Project instructions, memory, and CodeGraph context are initialized through
`./install.sh --project-root "<project-root>" init-project`; they are not
project-local Teamwork package freshness surfaces.

Flags:

- `--readiness` — compact init output (`INSTALL_READY`, `MISSING`, `NEXT`)
- `--no-fetch` — skip git fetch and remote VERSION lookup

Normal report mode exits `0` when current and `1` when surfaces need action;
readiness reports convergence through `INSTALL_READY`.
There are no project-local Teamwork package readiness rows.

## Init Readiness

Before project instruction work, run `./scripts/check-update.sh --readiness`.

When `INSTALL_READY=no`, run `NEXT`, then continue project instructions, memory,
and any available CodeGraph index. `init-project` refreshes global Teamwork first and does not create project-local Teamwork skills or agents.

Only a user-level Codex install repairs `codex-routing`. Native interaction tools belong to the current host/runtime; use them when callable and never handwrite config to expose them. Restart Codex after a routing change.

Run `./install.sh cursor-policy-copy` when possible; report the unverifiable manual Cursor User Rules paste.

Do not install external MCP/memory tools during the gate without user approval.

## User Update Mode

When the user asks to update or refresh Teamwork (not release a new version):

1. Run `./scripts/check-update.sh`.
2. If checkout is behind upstream, `git pull` in the Teamwork repo with approval.
3. For a global-only refresh, run `./install.sh all --profile <profile>`; it
   installs Codex/Claude notifications unless explicitly opted out. For requested
   project context, run `./install.sh --project-root "$PWD" init-project`
   instead; it refreshes global Teamwork before updating project instructions,
   memory, and CodeGraph context.
4. Use `./install.sh cursor-policy-copy` for Cursor User Rules paste when needed.
5. Restart Codex after routing changes; rerun the check. For `review-required`, verify the exact command in `/hooks` and trust only `Stop` and `PermissionRequest`.

Do not bump `VERSION` or edit plugin manifests in user mode.

## Release Boundary

Package versioning, changelogs, tags, and GitHub Releases are repository
maintainer work governed by the Teamwork repository's root `AGENTS.md`, not by
the installed user-refresh skill. This reference only checks freshness before and after an authorized local refresh.

## Out of Scope

Project package managers, non-Teamwork MCP plugins, and live platform catalogs
are not checked; route them to native tooling or `teamwork-research` on request.
