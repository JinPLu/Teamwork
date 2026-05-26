# Project Init

Use this reference with `teamwork-init` when a project needs agent instruction
setup, cleanup, or migration into Teamwork.

## Project Rule Layering

- Root `AGENTS.md`: long-lived project boundaries, repo map, local/remote
  execution policy, protected actions, and the minimum tool arbitration needed
  before reading deeper files.
- Repo-local `AGENTS.md`: repository facts, evidence sources, commands,
  danger zones, and repo-specific acceptance expectations.
- Platform files such as `CODEX.md`, `CLAUDE.md`, or `GEMINI.md`: only
  platform-specific deltas. Link back to `AGENTS.md` and shared workflow
  files instead of copying them.
- Appendix docs: long path maps, command inventories, environment matrices, and
  historical navigation. Read them only when navigation details are needed.
- `docs/teamwork/{research,plans,reports}/`: durable Teamwork memory only when
  artifact triggers apply. These files are retrieval aids, not completion
  evidence or project truth by themselves.

## Content Classification

- Portable workflow: evidence labels, artifact triggers, route selection,
  verification-before-completion, `/new` handoff discipline, and instruction
  slimming policy. Prefer Teamwork skills or references.
- Project facts: repo roles, source-of-truth paths, server paths, local/remote
  execution model, protected boundaries, and domain-specific red lines. Keep in
  project instructions.
- Current state: active results, temporary progress, task summaries, current
  leaderboards, or run status. Move to reviewed project evidence docs or
  Teamwork reports when warranted.
- Appendix navigation: long directory trees, path tables, command catalogs, and
  environment matrices. Keep out of always-loaded instructions.

## Collaboration Backbone Audit

Audit project instructions for these reusable human-agent work habits. For each
item, mark `keep` for project-specific acceptance details, `migrate` for generic
workflow duplicated from Teamwork, or `add` when the habit is missing:

- Context first: check whether agents must identify structure, entry points,
  commands, relevant files, and unknowns before edits.
- Plan gate: check whether non-trivial, multi-file, unfamiliar, research, or
  experiment work requires scope confirmation, affected modules, 3-7 steps,
  verification, and likely failure points.
- Research gate: check whether papers, repos, APIs, results, and current
  practice require primary-source evidence and risk listing before claims or
  implementation.
- Execution shape: check whether edits stay in small producer-side steps tied
  to accepted scope.
- Completion evidence: check whether final replies name changed files, why they
  changed, verification run, unverified gaps, and human confirmations needed.
- Handoff hygiene: check whether long sessions or task switches require a
  one-sentence `/new` handoff with task, changed files, state, and cautions.

## MCP And Search Policy

- CodeGraph is the structural code source for symbol lookup, architecture
  context, call paths, impact radius, and indexed file lists.
- Use native search and direct reads for literal text, logs, generated
  artifacts, LaTeX, result tables, images, PDFs, and non-code content.
- If CodeGraph is not initialized, ask before running initialization. If it is
  stale after edits, trust fresh reads for pending files and CodeGraph for files
  not reported stale.
- Do not dispatch subagents to rebuild structural code context that CodeGraph
  can answer directly. Use subagents for independent evidence, implementation,
  or fresh review tracks.

## Context-Cache Discipline

- Keep always-loaded rules short, stable, and rarely edited to improve
  context-cache reuse.
- Prefer references and appendix files for detailed but conditional guidance.
- Use artifact retrieval headers, `Search Keys`, and abstracts to find durable
  memory before reading large reports.
- Do not paste raw logs, long transcripts, or full external docs into
  instructions. Summarize evidence and link concrete paths or commands.
- Remove duplicated workflow prose from project files when the installed
  Teamwork skill already owns the policy.

## Output Shape

Return either a compact chat recommendation or a plan:

- files to keep slim;
- files to move into appendix or Teamwork artifacts;
- portable rules to migrate into Teamwork;
- collaboration backbone `keep` / `migrate` / `add` decisions;
- project-local rules that must remain;
- verification commands and expected scope checks;
- unresolved decisions that require human confirmation.
