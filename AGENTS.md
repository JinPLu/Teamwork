# Repository Guidelines

## Project Structure & Module Organization

This repository packages Teamwork as a **Codex + Cursor + Claude Code skill package** for personalized research and engineering collaboration. The source of truth is under `skills/`: `using-teamwork` is the lightweight router, `teamwork-research` gathers evidence, `teamwork-debug` diagnoses reproducible failures, `teamwork-plan` shapes reviewable plans, `teamwork-execute` runs accepted scope, `teamwork-review` checks evidence and quality, `teamwork-goal` supports long-running convergence, `teamwork-init` sets up project instructions, and `teamwork-update` handles refresh and release hygiene. Native platform tools still execute the work; Teamwork adds evidence discipline, artifact memory, bounded delegation, review, and failure iteration policy.

Platform metadata lives in `.codex-plugin/` and `.claude-plugin/`. User-facing docs live in `README.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md`. Artifacts live in `docs/teamwork/research/` for investigations, `docs/teamwork/plans/` for accepted plans, and `docs/teamwork/reports/` for conclusions or goal rolling attempt tables. `teamwork-update` owns maintainer release hygiene plus user-facing install refresh via `./scripts/check-update.sh`.

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
- `./install.sh cursor-policy-copy`: copies the Cursor User Rules block to the clipboard.
- `./install.sh claude-policy`: prints the Teamwork Claude global policy block.
- `./install.sh --link`: installs symlinks for local development (combine with any target).

## Coding Style & Naming Conventions

Keep shell scripts Bash-compatible with `set -euo pipefail`, quoted variables, and explicit arrays for skill lists. Skill directories use kebab-case names matching their `name:` frontmatter. Each `SKILL.md` frontmatter must contain only `name` and `description`, and descriptions must start with `Use when`.

## Testing Guidelines

There is no separate test suite directory; `scripts/validate.sh` is the required verification entrypoint. Add focused smoke coverage there when changing installer logic, manifests, skill topology, goal proposal behavior, artifact policy, or platform native capability mapping. Run validation before opening a pull request.

## Commit & Pull Request Guidelines

Keep commits scoped to one logical change. Pull requests should describe workflow impact, changed skill or runtime entrypoints, validation output, and any compatibility risk for existing Codex, Cursor, or Claude Code installs.

Stay on the current branch unless the user explicitly requests a branch or pull
request, repository protection requires one, or the user accepts isolation for
the task. Being on the default branch alone is not a reason to create an
`agent/*` branch. A Teamwork maintainer release is owned end to end by
`teamwork-update`; a generic GitHub publish/PR workflow does not replace version,
changelog, tag, or GitHub Release work.

## Agent-Specific Instructions

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first and keep public docs focused on user value and usage. Use `teamwork-init` for project instruction setup, slimming, MCP policy, or appendix guidance. Preserve the role separation between research, debug, plan, execute, review, and goal stages, but do not add a separate debug role or force subagents or durable artifacts for simple native platform work. Prefer direct evidence from files, logs, tests, diffs, and artifacts before changing instructions.

## Teamwork Memory

Runtime memory lives under `docs/teamwork/`. Read `docs/teamwork/index.json`
first, then use `docs/teamwork/README.md` for the retrieval protocol and follow
the active pointers. Do not inline volatile progress or experiment state here.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project identity: `Teamwork` - Teamwork
- Teamwork memory: read `docs/teamwork/index.json` first, then `docs/teamwork/README.md` when durable memory is relevant.
- CodeGraph: use `codegraph_*` tools for structural code questions when available. If `.codegraph/` is missing and the `codegraph` CLI is available, initialize with `codegraph init -i` from the project root.
- Docs MCP: use Context7/docs MCP for current external library, framework, SDK, or API docs when already available. Send only sanitized package names, versions, and topic queries; do not send private source.
- Keep volatile task progress, chat summaries, and experiment numbers out of `AGENTS.md`; use `docs/teamwork/current.md` or dated artifacts only when durable triggers apply.
- Required values, credentials, paths, ports, model names, hyperparameters, configs, and execution modes must come from project files, environment, or the user; do not invent fallbacks.
<!-- TEAMWORK_PROJECT_END -->
