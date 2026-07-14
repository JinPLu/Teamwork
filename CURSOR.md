# Cursor Usage

Teamwork for Cursor adapts the same evidence-first skill package used by Codex
and Claude Code. Cursor's editor, shell, MCP, permissions, browser tools, `Task`
subagents, custom agents, and verification remain the execution layer.

## Install

User-level setup:

```bash
./install.sh cursor
./install.sh cursor --profile cost-first
./install.sh cursor-agents
./install.sh cursor-policy-copy
./install.sh cursor-policy
./install.sh all
```

These commands make Teamwork skills and agents available to the current user;
they do not initialize every repository. Configure one selected repository
with:

```bash
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project init-project
```

User-level skills install to `~/.cursor/skills/` and custom agents to
`~/.cursor/agents/`. Project setup installs skills to `.cursor/skills/` and
agents to `.cursor/agents/` in the selected repository. Use `--link` only when
the installation should track this checkout during development.

Cursor stores User Rules outside a normal project file. Run
`./install.sh cursor-policy-copy` (or print the block with `cursor-policy`), then
paste it manually into Cursor Settings -> Rules -> User Rules. The installer
cannot verify that this manual step was completed.

The `performance-first` profile currently maps routine roles to Sonnet 4.6 or
Composer 2.5 Fast and review roles to Opus 4.8 Thinking High. `cost-first` uses
base Composer 2.5 for routine roles. These are configurable current Cursor
adapter mappings, not cross-platform or future-runtime guarantees.

Teamwork does not install Cursor notification sounds because the local hook path
has not been live-verified.

## How To Use

Ask naturally for research, debugging, a plan, execution, strict review, or a
verified long-running outcome. Tiny edits and one-line questions remain on
Cursor's native path. Explicitly ask to be questioned, challenged, or grilled
to activate `grill-me`; otherwise Teamwork asks only for required input or a
material user-owned decision that it cannot discover safely.

For planning, Teamwork grounds scope, required values, and verification in
evidence. Confirming a plan does not authorize implementation.

## Subagents

Teamwork may use Cursor `Task` subagents or installed custom agents for
independent work that benefits from separation or fresh context. The main agent
keeps responsibility for scope, integration, user communication, verification,
and the final response. Shared dispatch behavior is documented in
`skills/using-teamwork/references/subagent-dispatch.md`.

## Goal Mode

Cursor has no native Codex `create_goal` equivalent. When cross-turn durability
is needed, Teamwork can keep a rolling goal report under
`docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` in a repository where the user
has authorized writes. Repeated failures should return to evidence gathering or
debugging before another implementation attempt.

## Evidence, Limits, And Updates

Paths, ports, models, credentials, commands, and execution modes must come from
the user, repository, configuration, tests, or an accepted plan. Teamwork does
not take over Cursor permissions, MCP, browser, or test settings, and it does
not emulate structured question tools that the current runtime does not expose.

Use `teamwork-init` to configure one selected repository. Use
`teamwork-update` or `./scripts/check-update.sh --project /path/to/project` to
refresh or inspect installed surfaces. Refreshing an installation is not a
maintainer version release.
