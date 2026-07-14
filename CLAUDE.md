@AGENTS.md

# Claude Code Usage

Teamwork for Claude Code adapts the same evidence-first skill package used by
Codex and Cursor. Claude Code native capabilities—editing, shell execution,
MCP, permissions, `Task` subagents, planning, and verification—remain the
execution layer.

`VERSION` is the package version source of truth and should match both plugin
manifests.

## Install

User-level setup:

```bash
./install.sh claude
./install.sh claude --profile cost-first
./install.sh claude --profile cost-first --notifications
./install.sh claude --no-notifications
./install.sh claude-agents
./install.sh claude-policy
./install.sh all
```

These commands make Teamwork available to the current user; they do not
initialize every repository. Configure one selected repository with:

```bash
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project init-project
```

User-level skills install to `~/.claude/skills/` and agents to
`~/.claude/agents/`. Project setup installs them under `.claude/skills/` and
`.claude/agents/` in the selected repository. A direct Claude install also
maintains the Teamwork-owned block in `~/.claude/CLAUDE.md`; `claude-policy`
prints that block for manual review. Use `--link` only for local development.

Notifications are opt-in for direct installs and enabled by default for `all`
and `init-project`. They cover main-turn completion and permission requests;
subagents remain silent. Installation is tested in isolation, but live Claude
event delivery has not been verified, and plugin activation remains subject to
Claude Code's hook trust controls.

Claude Code agents use the current `haiku`, `sonnet`, and `opus` aliases rather
than pinned historical model IDs. `performance-first` maps routine roles to
Sonnet and review roles to Opus; `cost-first` maps routine roles to Haiku. These
are configurable Claude adapter mappings, not guarantees about future runtime
behavior.

## How To Use

Ask for research, debugging, a plan, execution of accepted scope, strict review,
or a verified long-running outcome. Small questions and tiny edits remain on
Claude Code's native path. Explicitly ask to be questioned, challenged, or
grilled to activate `grill-me`; otherwise Teamwork asks only for required input
or a material user-owned decision that it cannot discover safely.

For planning, Teamwork grounds scope, required values, and verification in
evidence. Confirming a plan does not authorize implementation.

## Subagents

Teamwork may use Claude Code `Task` subagents for independent work that benefits
from separation or fresh context. Installed roles include `explore`, `designer`,
`judge`, `worker`, `code-reviewer`, plus `deep-judge` and `deep-reviewer` for
higher-risk review. The main agent keeps responsibility for scope, integration,
user communication, verification, and the final response. Shared dispatch
behavior is documented in
`skills/using-teamwork/references/subagent-dispatch.md`.

## Goal Mode

Claude Code has no native Codex `create_goal` equivalent. When cross-turn
durability is needed, Teamwork can keep a rolling report under
`docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` in a repository where the user
has authorized writes. Repeated failures should return to evidence gathering or
debugging before another implementation attempt.

## Evidence, Limits, And Updates

Paths, ports, models, credentials, commands, and execution modes must come from
the user, repository, configuration, tests, or an accepted plan. Teamwork does
not take over Claude Code permissions, MCP, or test settings, and it does not
emulate structured question tools that the current runtime does not expose.

Use `teamwork-init` to configure one selected repository. Use
`teamwork-update` or `./scripts/check-update.sh --project /path/to/project` to
refresh or inspect installed surfaces. Refreshing an installation is not a
maintainer version release.
