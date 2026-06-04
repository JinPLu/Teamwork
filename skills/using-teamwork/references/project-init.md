# Project Init

Use with `teamwork-init` for agent instruction setup, cleanup, or migration.

## Project Rule Layering

- Global `~/.codex/AGENTS.md`: portable defaults installed by `./install.sh
  codex`, including Codex subagent authorization and remote assumptions.
- Root `AGENTS.md`: project boundaries, repo map, local/remote policy,
  protected actions, and minimal tool arbitration before deeper files.
- Repo-local `AGENTS.md`: repository facts, evidence sources, commands,
  danger zones, and repo-specific acceptance expectations.
- Platform files such as `CODEX.md`, `CURSOR.md`, `CLAUDE.md`, or `GEMINI.md`:
  platform deltas only; link instead of copying shared workflow.
- Appendix docs: long path maps, command inventories, environment matrices, and
  history. Read on demand.
- `docs/teamwork/README.md`: runtime memory entrypoint; project AGENTS/README
  may point here, but should not inline it.
- `docs/teamwork/{research,plans,reports}/`: durable memory only when artifact
  triggers apply; retrieval aids, not completion evidence.

## Content Classification

- Portable workflow: evidence labels, artifact triggers, route selection,
  verification, `/new` handoff discipline, and instruction slimming policy.
- Project facts: repo roles, source-of-truth paths, server paths, execution
  model, protected boundaries, and domain-specific red lines.
- Current state: active results, temporary progress, summaries, leaderboards,
  or run status. Move to evidence docs or reports when warranted.
- Appendix navigation: long directory trees, path tables, command catalogs, and
  environment matrices. Keep out of always-loaded instructions.

## Collaboration Backbone Audit

Audit project instructions for these reusable human-agent work habits. For each
item, mark `keep` for project-specific acceptance details, `migrate` for generic
workflow duplicated from Teamwork, or `add` when the habit is missing:

- Context first: check whether agents must identify structure, entry points,
  commands, relevant files, and unknowns before edits.
- Plan gate: check whether non-trivial, multi-file, unfamiliar, research, or
  experiment work requires scope, affected modules, steps, verification, risks.
- Research gate: check whether papers, repos, APIs, results, and practice need
  primary-source evidence and risks before claims or implementation.
- Execution shape: check whether edits stay in small producer-side steps tied
  to accepted scope.
- Completion evidence: check final replies name changed files, why, verification,
  gaps, and human confirmations needed.
- Handoff hygiene: check whether task switches need a one-sentence handoff.

## Teamwork Initialization Mode
Codex model profile is chosen at install time. `performance-first` is the
Pro/20x default: `gpt-5.5` medium routine roles, high review roles, xhigh Deep
Judge/Reviewer. `cost-first` downshifts routine roles. Project init asks only
when overriding the global policy. Model overrides require generated agents via
`install.sh --profile`.

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
