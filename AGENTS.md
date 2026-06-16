# Repository Guidelines

## Project Structure & Module Organization

This repository packages Teamwork as a **Codex + Cursor + Claude Code skill package**. The source of truth is under `skills/`: `using-teamwork` is the automatic entrypoint and router, `teamwork-init` owns project instruction setup and slimming, `teamwork-goal` owns native-goal collaboration and convergence, `teamwork-research` owns evidence gathering, `teamwork-plan` owns executable planning, `teamwork-execute` plus `teamwork-review` define execution and review workflows, and `teamwork-update` owns version and package update hygiene. Native platform capabilities remain the execution substrate; Teamwork adds evidence discipline, artifact memory, subagent routing, review and acceptance, and failure iteration policy.

Platform metadata lives in `.codex-plugin/` and `.claude-plugin/`. User-facing runtime notes live in `README.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md`. Artifact roles are `docs/teamwork/research/` for investigation, `docs/teamwork/plans/` for execution memos, and `docs/teamwork/reports/` for task conclusions plus goal rolling attempt tables. `teamwork-update` owns maintainer release hygiene plus user-facing install refresh via `./scripts/check-update.sh`.

## Build, Test, and Development Commands

- `./scripts/check-update.sh`: reports Teamwork install freshness (global/project skills, agents, policy, upstream VERSION drift); use `--readiness` for init gate.
- `./scripts/validate.sh`: required repository verification for skill topology, frontmatter, Codex and Claude Code manifests, artifact ignore rules, installer smoke, and platform contract checks.
- `./install.sh codex`: installs Codex skills, Teamwork Codex agents, and the Teamwork-managed global block in `~/.codex/AGENTS.md`.
- `./install.sh cursor`: installs Cursor skills, Teamwork Cursor agents under `~/.cursor/agents/`.
- `./install.sh claude`: installs Claude Code skills, Teamwork Claude agents, and the Teamwork-managed global block in `~/.claude/CLAUDE.md`.
- `./install.sh all`: installs skills and agents for codex, cursor, and claude, plus Codex and Claude global policy.
- `./install.sh project`: installs project `.cursor/skills/`, `.cursor/agents/`, `.codex/agents/`, and `.claude/agents/` (this checkout by default).
- `./install.sh --project-root PATH project`: installs the same project surfaces into another repository.
- `./install.sh codex-agents`: installs Teamwork custom agents into `~/.codex/agents/`.
- `./install.sh cursor-agents`: installs Teamwork Cursor subagents into `~/.cursor/agents/`.
- `./install.sh claude-agents`: installs Teamwork subagents into `~/.claude/agents/`.
- `./install.sh codex-policy`: prints the Teamwork Codex global policy block.
- `./install.sh cursor-policy`: prints the Teamwork Cursor global policy block for User Rules.
- `./install.sh claude-policy`: prints the Teamwork Claude global policy block.
- `./install.sh --link`: installs symlinks for local development (combine with any target).

## Coding Style & Naming Conventions

Keep shell scripts Bash-compatible with `set -euo pipefail`, quoted variables, and explicit arrays for skill lists. Skill directories use kebab-case names matching their `name:` frontmatter. Each `SKILL.md` frontmatter must contain only `name` and `description`, and descriptions must start with `Use when`.

## Testing Guidelines

There is no separate test suite directory; `scripts/validate.sh` is the required verification entrypoint. Add focused smoke coverage there when changing installer logic, manifests, skill topology, goal proposal behavior, artifact policy, or platform native capability mapping. Run validation before opening a pull request.

## Commit & Pull Request Guidelines

Keep commits scoped to one logical change. Pull requests should describe workflow impact, changed skill or runtime entrypoints, validation output, and any compatibility risk for existing Codex, Cursor, or Claude Code installs.

## Agent-Specific Instructions

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first and avoid duplicating full skill bodies in README-style docs. Use `teamwork-init` for project instruction setup, slimming, MCP policy, or appendix guidance. Preserve the role separation between research, plan, execute, review, and goal stages, but do not force subagents or durable artifacts for simple native platform work. Prefer direct evidence from files, logs, tests, diffs, and artifacts before changing instructions.

## Teamwork Memory

Runtime memory lives under `docs/teamwork/`. Read `docs/teamwork/README.md` first,
then follow `index.json` active pointers. Do not inline volatile progress or
experiment state here.
