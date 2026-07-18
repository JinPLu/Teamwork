# Repository Guidelines

## Project Structure & Module Organization

This repository packages Teamwork as a **Codex + Cursor + Claude Code skill package** for personalized research and engineering collaboration. The source of truth is under `skills/`: `using-teamwork` is the lightweight router, `teamwork-research` gathers evidence, `teamwork-debug` diagnoses unknown-cause failures, `teamwork-plan` resolves material choices, `teamwork-execute` runs authorized scoped work, `teamwork-review` checks evidence and quality, `teamwork-goal` supports long-running convergence, `teamwork-init` sets up project instructions, and `teamwork-update` refreshes user installations. Native platform tools still execute the work; Teamwork adds outcome-first execution, evidence discipline, artifact memory, bounded delegation, review, and failure iteration policy.

Platform metadata lives in `.codex-plugin/` and `.claude-plugin/`. User-facing docs live in `README.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md`. Artifacts live in `docs/teamwork/research/` for investigations, `docs/teamwork/discussion/` for long-discussion route checkpoints, `docs/teamwork/plans/` for accepted plans, and `docs/teamwork/reports/` for conclusions or goal rolling attempt tables. `teamwork-update` owns user-facing global-install refresh via `./scripts/check-update.sh`; this file owns maintainer release policy.

## Build, Test, and Development Commands

- `./scripts/check-update.sh`: reports global Teamwork install freshness (skills, agents, policy, upstream VERSION drift); use `--readiness` for the init gate.
- `./scripts/validate.sh`: required repository verification for skill topology, frontmatter, Codex and Claude Code manifests, artifact ignore rules, installer smoke, and platform contract checks.
- `./install.sh codex`: installs Codex skills, Teamwork Codex agents, and the Teamwork-managed global block in `~/.codex/AGENTS.md`.
- `./install.sh cursor`: installs Cursor skills, Teamwork Cursor agents under `~/.cursor/agents/`.
- `./install.sh claude`: installs Claude Code skills, Teamwork Claude agents, and the Teamwork-managed global block in `~/.claude/CLAUDE.md`.
- `./install.sh all`: installs skills and agents for codex, cursor, and claude, plus Codex and Claude global policy.
- `./install.sh --project-root PATH init-project`: refreshes global Teamwork surfaces and initializes the selected project's instructions, runtime memory, and optional CodeGraph context; it never installs Teamwork skill or agent copies into the project.
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

Keep commits scoped to one logical change. By default, complete a Teamwork
change as a direct mainline release: work on `main`, update `VERSION`, and
complete the corresponding release unit. Create a branch or pull request only
when the user explicitly requests it or repository protection requires it.
When requested, pull requests should describe workflow impact, changed skill or
runtime entrypoints, validation output, and any compatibility risk for existing
Codex, Cursor, or Claude Code installs. A Teamwork maintainer release is owned
end to end by this root `AGENTS.md`; a generic GitHub publish/PR workflow does
not replace version, changelog, tag, GitHub Release, or installed-surface
refresh work.

## Maintainer Release & Changelog

Unless the user narrows scope, a user-requested Teamwork change uses the direct
mainline release default above. `VERSION` is canonical. One release unit
contains `VERSION`, both plugin manifests, both changelogs,
required public docs, verification, an intentional commit, `v<VERSION>` tag,
GitHub Release, global skills/agents/policy refresh, applicable project-context
initialization, and a final freshness check. Until the tag and GitHub Release
exist, report `release-ready`, not `released`.

Write changelogs for users, not maintainers. Lead with the problem and outcome;
give each important change a short, natural headline that names the experience
users will notice. For behavior, installation, or workflow changes state at
least one explicit Before -> After difference and why it matters, then name the
primary subskill or user-facing workflow responsible so readers can tell what
actually changed. State the exact upgrade action or that no action is needed,
plus an important limit in plain language. Chinese and English must communicate
the same change naturally rather than translating engineering labels literally.
Move internal contract names,
mutation details, schemas, and test counts to commits, ledgers, validation, or a
separate Release verification section. A technically accurate changelog that
reads like an engineering report is not release-ready.

Apply the same audience-first standard to every public document and plugin
listing. Start with what users can accomplish, keep the shortest complete setup
and usage path easy to find, and retain internal architecture or process only
when it changes a user action, boundary, or expectation. README and platform
guides should link to one canonical explanation instead of repeating it.

Use patch for non-behavioral fixes, minor for compatible features, and major for
incompatible public contracts. Inspect remote/tag/Release state before edits;
update metadata and changelogs together; run relevant dev eval, full validation,
non-empty release eval, and fresh release review; refresh global installs and
applicable project context; verify credentials and target commit; then push the
accepted mainline commit, tag, and GitHub Release. Rerun
`./scripts/check-update.sh`; source, installations, remote tag, and GitHub
Release must all be current.

## Agent-Specific Instructions

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first and keep public docs focused on user value and usage. Use `teamwork-init` for project instruction setup, slimming, MCP policy, or appendix guidance. Preserve the role separation between research, debug, plan, execute, review, and goal stages, but do not add a separate debug role or force subagents or durable artifacts for simple native platform work. Prefer direct evidence from files, logs, tests, diffs, and artifacts before changing instructions.

## Teamwork Memory

Runtime memory lives under `docs/teamwork/`. For Grill/discussion continuation,
load `grill-me`, resolve the installed `scripts/discussion-transaction.py` from
the loaded `using-teamwork` skill, and run `inspect` from the project root first; its
result is the sole discussion read path. Do not directly read `index.json`,
`current.md`, `README.md`, or a discussion artifact for that continuation. For
ordinary non-discussion memory, read `docs/teamwork/index.json` first, then use
`docs/teamwork/README.md` for the retrieval protocol. Do not inline volatile
progress or experiment state here.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label (local routing only): `Teamwork`.
- For Grill/discussion continuation, load `grill-me`, resolve the installed `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill, and run `inspect` from the project root first; its result is the sole discussion read path, so do not directly read `index.json`, `current.md`, `README.md`, or a discussion artifact for that continuation.
- Ordinary non-discussion memory reads `docs/teamwork/index.json` first, then `docs/teamwork/README.md` when durable memory is relevant.
- CodeGraph: this project has a local `.codegraph/` index.
<!-- TEAMWORK_PROJECT_END -->
