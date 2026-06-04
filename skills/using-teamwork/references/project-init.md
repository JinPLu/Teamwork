# Project Init

Use with `teamwork-init` for agent instruction setup, cleanup, or migration.

## Project Rule Layering

- Codex App Personalization: optional app-wide bootstrap; paste `./install.sh codex-policy` output only.
- Global `~/.codex/AGENTS.md`: installer-managed bootstrap: subagents, efficiency, model profile, fail-fast safety, remote baseline.
- Root `AGENTS.md`: project boundaries, repo map, required values, protected actions, and tool arbitration.
- Repo-local `AGENTS.md`: facts, evidence sources, commands, danger zones, and acceptance expectations.
- Platform files such as `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, or `GEMINI.md`: platform deltas only.
- Appendix docs: long paths, commands, environment matrices, and history. Read on demand.
- `docs/teamwork/README.md`: runtime memory entrypoint; point to it, do not inline it.
- `docs/teamwork/{research,plans,reports}/`: durable memory when triggered; retrieval aids, not completion evidence.

## Content Classification

- Bootstrap policy: authorization, efficiency, model profile, fail-fast safety, and remote baseline before skills.
- Portable workflow: evidence labels, artifact triggers, route selection, verification, handoff, and slimming policy.
- Project facts: repo roles, source paths, server paths, execution model, required environment variables, commands, ports, protected boundaries, and red lines.
- Current state: active results, progress, summaries, or run status. Move to artifacts when warranted.
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
default; `cost-first` downshifts routine roles. Project init asks only when
overriding global policy. Model overrides require agents from
`install.sh --profile`.

## Rule Persistence Decision

Use `./install.sh codex` for managed `~/.codex/AGENTS.md`; use
`./install.sh codex-policy` for Codex App Personalization. Keep both copies
identical. Project instructions record concrete values, exceptions, opt-outs,
or protected boundaries. Missing required host, path, command, port, credential,
model, hyperparameter, or execution mode is a blocker, not a fallback rule.

## MCP And Search Policy

- CodeGraph is the structural code source for symbol lookup, architecture
  context, call paths, impact radius, and indexed file lists.
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
Return a compact recommendation or plan covering files, portable migrations,
`keep` / `migrate` / `add` decisions, remaining local rules, verification, and
human decisions.

## Teamwork Memory Bootstrap

For non-lightweight Teamwork workflows, initialize missing `index.json`,
`README.md`, and `current.md` when bootstrap is in scope. Add only a short
project-instruction pointer to the runtime README. Keep it minimal and
compatible with `artifact-protocol.md`; do not force artifacts for lightweight
native flow.
