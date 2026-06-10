# Repository Guidelines

## Project Structure & Module Organization

This repository packages Teamwork as a **Codex + Cursor + Claude Code skill package**. The source of truth is under `skills/`: `using-teamwork` is the automatic entrypoint and router, `teamwork-init` owns project instruction setup and slimming, `teamwork-goal` owns native-goal collaboration and convergence, `teamwork-research` owns evidence gathering, `teamwork-plan` owns executable planning, `teamwork-execute` plus `teamwork-review` define execution and review workflows, and `teamwork-update` owns version and package update hygiene. Native platform capabilities remain the execution substrate; Teamwork adds evidence discipline, artifact memory, subagent routing, review gates, and failure iteration policy.

Platform metadata lives in `.codex-plugin/` and `.claude-plugin/`. User-facing runtime notes live in `README.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md`. Artifact roles are `docs/teamwork/research/` for investigation, `docs/teamwork/plans/` for execution memos, and `docs/teamwork/reports/` for task conclusions plus goal rolling attempt tables. `teamwork-update` owns version metadata plus installed skills, agents, and global-policy refresh.

## Build, Test, and Development Commands

- `./scripts/validate.sh`: required repository verification for skill topology, frontmatter, Codex and Claude Code manifests, artifact ignore rules, installer smoke, and platform contract checks.
- `./install.sh codex`: installs Codex skills, Teamwork Codex agents, and the Teamwork-managed global block in `~/.codex/AGENTS.md`.
- `./install.sh cursor`: installs the Teamwork skill set into `~/.cursor/skills`.
- `./install.sh claude`: installs the Teamwork skill set into `~/.claude/skills`.
- `./install.sh all`: installs skills to codex, cursor, and claude home directories, plus Codex and Claude agent templates.
- `./install.sh project`: installs project `.cursor/skills/`, `.codex/agents/`, and `.claude/agents/`.
- `./install.sh codex-agents`: installs Teamwork custom agents into `~/.codex/agents/`.
- `./install.sh claude-agents`: installs Teamwork subagents into `~/.claude/agents/`.
- `./install.sh --link`: installs symlinks for local development (combine with any target).

## Coding Style & Naming Conventions

Keep shell scripts Bash-compatible with `set -euo pipefail`, quoted variables, and explicit arrays for skill lists. Skill directories use kebab-case names matching their `name:` frontmatter. Each `SKILL.md` frontmatter must contain only `name` and `description`, and descriptions must start with `Use when`.

## Testing Guidelines

There is no separate test suite directory; `scripts/validate.sh` is the required verification entrypoint. Add focused smoke coverage there when changing installer logic, manifests, skill topology, goal proposal behavior, artifact policy, or platform native capability mapping. Run validation before opening a pull request.

## Commit & Pull Request Guidelines

Keep commits scoped to one logical change. Pull requests should describe workflow impact, changed skill or runtime entrypoints, validation output, and any compatibility risk for existing Codex, Cursor, or Claude Code installs.

## Agent-Specific Instructions

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first and avoid duplicating full skill bodies in README-style docs. Use `teamwork-init` for project instruction setup, slimming, MCP policy, or appendix guidance. Preserve the role separation between research, plan, execute, review, and goal stages, but do not force subagents or durable artifacts for simple native platform work. Prefer direct evidence from files, logs, tests, diffs, and artifacts before changing instructions.
