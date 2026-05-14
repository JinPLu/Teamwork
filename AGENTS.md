# Repository Guidelines

## Project Structure & Module Organization

This repository packages the Teamwork workflow for Claude Code, Codex, and Cursor. The source of truth for behavior is under `skills/`: `using-teamwork` is the automatic entrypoint, `teamwork` is the router, `teamwork-goal` owns autonomous convergence, and `teamwork-design`, `teamwork-execute`, and `teamwork-review` define stage-specific workflows. Claude slash commands live in `commands/teamwork/*.md`, with `commands/rao/*.md` retained as compatibility aliases. Stop-hook configuration is in `hooks/hooks.json`, and the runtime controller is `bin/raoctl.py`. Platform metadata lives in `.claude-plugin/`, `.codex-plugin/`, and `.cursor/rules/`. Use `README.md`, `CODEX.md`, `CLAUDE.md`, and `CURSOR.md` for user-facing runtime notes.

## Build, Test, and Development Commands

- `./scripts/validate.sh`: runs the main repository validation, including skill topology, frontmatter rules, manifest JSON checks, hook smoke tests, and temporary install smoke tests.
- `./install.sh claude`: installs the six Teamwork skills into `~/.claude/skills`.
- `./install.sh codex`: installs the six Teamwork skills into `~/.codex/skills`.
- `./install.sh cursor /path/to/project`: installs the thin Cursor rule into a target project.
- `./install.sh all /path/to/project`: installs Claude, Codex, and Cursor entries.

## Coding Style & Naming Conventions

Keep shell scripts Bash-compatible with `set -euo pipefail`, quoted variables, and explicit arrays for skill lists. Keep Python runtime code in `bin/raoctl.py` standard-library only unless a dependency is deliberately introduced and documented. Skill directories use kebab-case names matching their `name:` frontmatter. Each `SKILL.md` frontmatter must contain only `name` and `description`, and descriptions must start with `Use when`.

## Testing Guidelines

There is no separate test suite directory; `scripts/validate.sh` is the required verification entrypoint. Add focused smoke coverage there when changing command files, hook behavior, installer logic, manifests, or skill topology. Run validation before opening a pull request.

## Commit & Pull Request Guidelines

Recent commits use concise imperative summaries, for example `Refactor Teamwork router subskills`. Keep commits scoped to one logical change. Pull requests should describe the workflow impact, list changed skill or runtime entrypoints, include validation output, and call out any compatibility risk for Claude, Codex, or Cursor installs.

## Agent-Specific Instructions

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first and avoid duplicating full skill bodies in platform-specific docs. Preserve the role separation between design, execute, review, and goal stages, and prefer direct evidence from files, logs, tests, and diffs before changing instructions.
