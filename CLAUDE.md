# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teamwork packages an evidence-first agent collaboration workflow for Claude Code, Codex, and Cursor. It splits larger coding-agent work into research, durable planning, scoped execution, fresh-context review, and verified completion.

The behavioral source of truth is the skill set under `skills/`. Keep detailed workflow instructions in the relevant `SKILL.md` files; do not duplicate full skill bodies into platform docs or rules.

## Common Commands

- `./scripts/validate.sh`: main validation entrypoint. It checks skill topology, skill frontmatter, plugin manifests, command files, hooks, durable-plan requirements, runtime smoke behavior, and temporary install flows.
- `./install.sh claude`: copy the seven Teamwork skills into `~/.claude/skills`.
- `./install.sh codex`: copy the seven Teamwork skills into `~/.codex/skills`.
- `./install.sh cursor /path/to/project`: install the thin Cursor rule into a target project.
- `./install.sh all /path/to/cursor-project`: install Claude, Codex, and Cursor entries.
- `./install.sh --link claude` or `./install.sh --link codex`: symlink installed skills to this checkout for local development.

There is no separate package-manager build or test suite in this repository. Use `./scripts/validate.sh` as the required focused verification command after changing skills, commands, hooks, manifests, installer logic, or `bin/raoctl.py`.

For runtime-controller focused checks, the relevant smoke tests are embedded in `scripts/validate.sh`; run the full script rather than inventing an ad hoc single-test command.

## Architecture

- `skills/using-teamwork/SKILL.md` is the automatic entry skill for ordinary coding, research, planning, implementation, or review work.
- `skills/teamwork/SKILL.md` is the public router. It maps user intent to the narrowest stage skill and defines shared evidence, subagent, routing, and durable-plan contracts.
- `skills/teamwork-goal/SKILL.md` owns autonomous convergence mode (`mode: goal`) for bounded iteration until verified success, budget exhaustion, repeated no-progress, or blocker.
- `skills/teamwork-research/SKILL.md` handles evidence gathering, external research, options, research artifacts under `docs/teamwork/research/YYYY-MM-DD-<slug>.md`, and research refresh.
- `skills/teamwork-plan/SKILL.md` converts a selected direction or research artifact into a lightweight or durable execution plan. Durable Markdown artifacts under `docs/teamwork/plans/YYYY-MM-DD-<slug>.md` are required for goal-mode, high-risk, cross-agent, cross-turn, ambiguous, or explicitly requested repository plans.
- `skills/teamwork-execute/SKILL.md` executes an accepted durable plan with minimal edits and focused verification; it should not reopen product behavior or architecture decisions.
- `skills/teamwork-review/SKILL.md` handles plan review (`mode: plan`) and execution review (`mode: execution`) against direct evidence.
- `commands/teamwork/*.md` provides Claude `/teamwork:*` slash commands. `commands/rao/*.md` preserves compatibility aliases.
- `.claude-plugin/plugin.json` registers Claude skills, commands, and `hooks/hooks.json`; `.codex-plugin/plugin.json` registers the Codex skill package; `.cursor/rules/teamwork.mdc` is a thin Cursor entrypoint.
- `bin/raoctl.py` is the standard-library Python runtime controller for Claude goal state and hooks. Runtime state is project-local under `.claude/teamwork-goals/` and may record `active_plan_artifact` plus its SHA-256.
- `install.sh` installs or symlinks the current skill set and cleans retired skill names from prior installs.

## Workflow Contracts

- For Claude Code, native flow is the default. Use Teamwork as a preference layer for evidence discipline, planning, review, and autonomous convergence when those add value. Do not force durable plan artifacts or subagents for simple local work.
- Prefer direct local evidence: source, diffs, config, logs, command output, tests, and artifacts. Treat README prose, names, comments, summaries, and version labels as claims until corroborated.
- Important findings should distinguish `observed`, `inferred`, and `claimed` evidence, matching the router and review skill contracts.
- Main agent owns scope, synthesis, conflict resolution, verification, and final acceptance. Subagents provide bounded evidence, implementation, or review products and do not automatically pass their own work.
- Default research/review fan-out is at most 3 parallel subagents unless the user gives a larger budget.
- For Teamwork plans, `update_plan` or task widgets are transient progress only. Use concise chat/native checklists for bounded low-risk work; use durable Markdown plan artifacts for goal-mode, high-risk, cross-agent, cross-turn, ambiguous, or explicitly requested repository plans. Use durable research artifacts under `docs/teamwork/research/` when later plan, execute, review, or goal iterations will depend on research findings.
- Claude goal auto-completion requires the configured completion promise such as `<promise>RAO_GOAL_COMPLETE</promise>` and a structured `<completion_audit>` in the same final assistant message. The audit must include a `plan_artifact` and SHA matching runtime state. `/teamwork:complete` and `/rao:complete` are manual overrides and are logged as not automatically verified.

## Platform Notes

- Claude Code plugin installs use checked-in plugin metadata for commands and hooks; `install.sh` installs skills but does not modify global settings.
- Codex plans should record conceptual Teamwork role, scope, model tier, context strategy, ordering, and rationale. Derive native Codex dispatch fields from `skills/teamwork/SKILL.md` at dispatch time unless a non-default native override is itself part of the decision.
- Cursor consumes only `.cursor/rules/teamwork.mdc`, which should remain a short pointer to the canonical skills rather than a copy of their instructions.

## Plan Artifact Format

Durable plan artifacts live under `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`. The `raoctl.py plan` command validates that the artifact exists under `docs/teamwork/plans/` (paths outside this directory are rejected) and contains all of the following H2 sections:

`Goal`, `Requirements Mapping`, `Evidence Read`, `Scope`, `Implementation Steps`, `Verification`, `Risks`, `Stop Rules`, `Worker Handoff`, `Review Handoff`, `Subagent Routing`

Missing any section causes `raoctl.py plan` to reject the artifact.

## Style and Maintenance

- Shell scripts should remain Bash-compatible with `set -euo pipefail` and quoted variables.
- Keep `bin/raoctl.py` standard-library only unless a new dependency is deliberately introduced and documented.
- Skill directories use kebab-case names matching their `name:` frontmatter.
- Each `SKILL.md` frontmatter must contain only `name` and `description`, and descriptions must start with `Use when`.
- New `SKILL.md` files must be git-committed before `./scripts/validate.sh` passes — it runs `git ls-files --error-unmatch` on each skill.
- `.cursor/rules/teamwork.mdc` must be ≤120 lines; `README.md` must be ≤180 lines (both enforced by `validate.sh`).
- `hooks/hooks.json` registers five hook types via `raoctl.py`: `SessionStart`, `UserPromptSubmit`, `Stop`, `PostCompact`, `SessionEnd`.
- When changing workflow behavior, update the relevant `skills/*/SKILL.md` first, then update platform docs or validation checks only as needed.
