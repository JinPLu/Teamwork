# Project Init

Use with `teamwork-init` for instruction setup, cleanup, or migration.

## Project Rule Layering

- Codex App Personalization: optional; paste only `./install.sh codex-policy`.
- Global `~/.codex/AGENTS.md`: installer-managed bootstrap.
- Root `AGENTS.md`: boundaries, repo map, required values, protected actions,
  and tool arbitration.
- Repo-local `AGENTS.md`: facts, evidence, commands, danger zones, acceptance.
- Platform files `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, `GEMINI.md`: deltas only.
- Appendix docs: long paths, commands, environment matrices, and history.
- `docs/teamwork/README.md`: runtime memory entrypoint; point to it, do not inline it.
- `docs/teamwork/{research,plans,reports}/`: durable memory when triggered; retrieval aids, not completion evidence.

## Content Classification

- Bootstrap policy: authorization, question-first efficiency, model profile,
  no-silent-defaults safety, remote baseline.
- Portable workflow: evidence labels, artifact triggers, route selection,
  verification, handoff, and slimming policy.
- Project facts: repo roles, paths, execution model, required environment variables, red lines.
- Current state: active results, progress, summaries, or run status.
- Appendix navigation: long trees, path tables, command catalogs, and environment matrices.

## Collaboration Backbone Audit

Audit reusable human-agent habits. Mark `keep` for project-specific acceptance,
`migrate` for generic workflow duplicated from Teamwork, or `add` when missing:

- Context first: structure, entry points, commands, files, unknowns before edits.
- Plan gate: non-trivial, unfamiliar, research, or experiment work has scope,
  modules, steps, verification, risks.
- Research gate: papers, repos, APIs, results, and practice use primary-source evidence.
- Execution shape: edits stay in small producer-side steps tied to accepted scope.
- Completion evidence: final replies name changed files, why, verification, gaps.
- Handoff hygiene: check whether task switches need a one-sentence handoff.

## Teamwork Initialization Mode
Codex model profile is chosen at install time. `performance-first` is Pro/20x
default; `cost-first` downshifts routine roles. Project init asks only for
global-policy overrides. Model overrides require `install.sh --profile` agents.

## Full Feature Capability Matrix
For full setup/full features/memory/docs graph requests, return compact matrix rows:
Core Teamwork workflow; Platform profile; Project instruction layer;
Artifact memory; CodeGraph policy; Subagent policy/install state;
Teamwork role workflow contracts; Validation; Optional docs graph; Optional external memory; Blockers.
Statuses: `enabled`, `missing`, `blocked`, `optional`, `deferred`. Every
non-enabled row names one next action. Core local rows may initialize in scope;
Optional docs graph/external memory stay `optional` or `deferred` until user approval and the optional-skills gate pass.

## Rule Persistence Decision

Use `./install.sh codex` for managed `~/.codex/AGENTS.md` and
`./install.sh codex-policy` for Codex App Personalization. Project instructions
record concrete values, exceptions, opt-outs, or protected boundaries. Missing
host/path/command/port/credential/model/hyperparameter/execution mode asks first
when user-supplied; hard-block only if unavailable, unsafe, or declined; never
invent fallback.

## MCP And Search Policy

- CodeGraph owns structural code lookup: symbols, architecture, call paths,
  impact radius, and indexed files.
- Approved docs MCPs such as Context7 cover library/framework/SDK/API docs as
  candidate/supporting evidence; never replace source, tests, configs, lockfiles, or behavior.
- Use native search and direct reads for literal text, logs, generated
  artifacts, LaTeX, result tables, images, PDFs, and non-code content.
- If CodeGraph is not initialized, ask before running initialization. If stale,
  trust fresh reads for pending files and CodeGraph for files not reported stale.
- Do not dispatch subagents to rebuild structural code context that CodeGraph
  can answer directly. Use subagents for independent evidence, implementation,
  or fresh review tracks.

## Context-Cache Discipline
- Keep always-loaded rules short, stable, and rarely edited to improve
  context-cache reuse.
- Prefer references and appendix files for detailed but conditional guidance.
- Use artifact retrieval headers, `Search Keys`, and abstracts to find durable
  memory before reading large reports.
- Do not paste raw logs, transcripts, or full external docs into instructions.
- Remove duplicated workflow prose from project files when the installed
  Teamwork skill already owns the policy.

## Output Shape
Return compact files, `keep`/`migrate`/`add` decisions, remaining local rules,
Capability Matrix when requested, verification, and human decisions.

## Teamwork Memory Bootstrap

For non-lightweight workflows, initialize missing `index.json`, `README.md`,
and `current.md` only when memory bootstrap is in scope. Add one project-rule
pointer; stay compatible with `artifact-protocol.md` and lightweight native flow.
