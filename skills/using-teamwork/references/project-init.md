# Project Init

Use with `teamwork-init` for instruction setup, cleanup, or migration.

## Project Rule Layering

- Global bootstrap: installer-managed blocks in `~/.codex/AGENTS.md` (Codex),
  `~/.claude/CLAUDE.md` (Claude Code), and Cursor User Rules via
  `./install.sh cursor-policy-copy`.
- Root `AGENTS.md`: boundaries, repo map, required values, protected actions, and tool arbitration.
- Repo-local `AGENTS.md`: facts, evidence, commands, danger zones, acceptance.
- Platform files `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, `GEMINI.md`: deltas only.
- Appendix docs: long paths, commands, environment matrices, and history.
- `docs/teamwork/README.md`: runtime memory entrypoint; point to it, do not inline it.
- `docs/teamwork/{research,plans,reports}/`: durable memory when triggered; retrieval aids, not completion evidence.

## Content Classification

- Bootstrap policy: authorization, act-by-default posture, model profile, no-silent-defaults safety, remote baseline.
- Portable workflow: evidence labels, artifact triggers, route selection, verification, handoff, and slimming policy.
- Project facts: repo roles, paths, execution model, required environment variables, red lines.
- Current state: active results, progress, summaries, or run status.
- Appendix navigation: long trees, path tables, command catalogs, and environment matrices.

## Collaboration Backbone Audit

Audit reusable human-agent habits. Mark `keep` for project-specific acceptance, `migrate` for generic workflow duplicated from Teamwork, or `add` when missing:

- Context first: structure, entry points, commands, files, unknowns before edits.
- Plan gate: non-trivial, unfamiliar, research, or experiment work has scope, modules, steps, verification, risks.
- Research gate: papers, repos, APIs, results, and practice use primary-source evidence.
- Execution shape: edits stay in small producer-side steps tied to accepted scope.
- Completion evidence: final replies name changed files, why, verification, gaps.
- Handoff hygiene: task switches include a one-sentence handoff when state matters.

## Teamwork Initialization Mode

Model profile is chosen at install time on all platforms. `performance-first` is
default; `cost-first` downshifts routine roles. Project init asks only for
global-policy overrides. Model overrides require `./install.sh --profile`.

## Full Feature Capability Matrix

For full setup requests, run `./scripts/check-update.sh --readiness --project
"<root>"` first, then return compact matrix rows: Core Teamwork workflow;
Platform profile; Project instruction layer; Artifact memory; CodeGraph policy;
Subagent policy/install state; Teamwork role workflow contracts; Validation;
Optional docs graph; Optional external memory; Blockers.

Statuses: `enabled`, `missing`, `blocked`, `optional`, `deferred`. Every non-enabled row names one next action. Optional docs graph and external memory stay `optional` or `deferred` until user approval and the optional-skills gate pass.

## Rule Persistence Decision

Use `./install.sh codex` for managed `~/.codex/AGENTS.md`, `./install.sh claude`
for managed `~/.claude/CLAUDE.md`, and `./install.sh cursor-policy-copy` for
Cursor User Rules paste. Project instructions record concrete values,
exceptions, opt-outs, or protected boundaries. Ask first when host/path/command/
credential/model values are user-supplied; block only when unavailable, unsafe,
or declined; never invent fallback.

## Output Shape

Return compact files, `keep`/`migrate`/`add` decisions, remaining local rules, Capability Matrix when requested, verification, and human decisions.
