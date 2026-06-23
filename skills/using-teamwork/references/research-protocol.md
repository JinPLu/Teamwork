# Research Protocol

Use for evidence gathering that affects implementation, spending, public claims, current APIs, or recommendations.

## Modes

- `lookup`: one stable fact or source. Answer locally with citation. Skip Search Plan and source census.
- `research`: several sources, options, or unknowns. Synthesize concisely. Fan out queries; triage sources; label observed/inferred/claimed.
- `deep`: high-stakes, current, or multi-domain work. Use fanout, source census, contradiction search, and coverage audit. Store overflow in artifacts.

Runtime diagnosis with repro, instrumentation, logs, browser state, or CI output belongs to `teamwork-debug`; research frames unknown source/repro questions and hands off when runtime evidence becomes decisive.

## Seed Expansion

When a user gives an article/paper/URL/repo/report and asks for a field, area,
tool, or current-state survey, treat it as seed evidence. Extract concepts,
methods, authors, systems, claims, evals, dissent, adjacent terms; build
perspective/query axes: overview, primary sources, implementations, benchmarks,
critiques, failures, related concepts. Search public web only with sanitized
concepts, not private text.

## Source Census (deep mode)

Build before broad reads: URL/path, class, primary/secondary, freshness, relevance, read/reject reason; flag UGC/summaries for cross-check. Use for >6 candidates, >10 expected sources, >3 source classes, or durable plans.

## Flow (research and deep)

1. Clarify underspecified goals, constraints, timeframe, or output format.
2. Write a Search Plan: source classes, primary sources, exclusions, freshness.
3. For seeded research, run Seed Expansion before reading deeply.
4. Fan out queries by perspectives, concepts, names, versions, failures, and dissent.
5. Triage: prefer official docs, specs, repos, papers, filings, changelogs, and direct data over summaries.
6. For current library/API questions, use an approved docs MCP when available; treat snippets as supporting until corroborated with primary source, tests, or verified behavior.
7. Label evidence: observed, inferred, claimed.
8. Run contradiction search and note Sources Rejected with reasons.
9. Audit coverage: missing source classes, stale assumptions, language/region gaps.
10. Produce capped Citation Ledger, Confidence, overflow artifact pointer, and route gaps to research or plan.

## Public/Private Safety

Stage public web apart from private files, MCP connectors, or credentials. Never send private repo facts, customer data, or secrets into public queries. Summarize private context locally, then search public concepts.

## Structured Output

Use tables by default for multi-source or multi-option research:

- Source Census: `Source | Class | Freshness | Relevance | Use / Reject`.
- Evidence Matrix: `Claim | Evidence | Status | Confidence`.
- Option Matrix: `Option | Evidence | Tradeoff | Recommendation`.

Output fields: Seed Expansion when used, Queries Tried, Sources Used/Rejected,
Contradictions, Coverage Gaps, Citation Ledger, Confidence, Artifact Pointer
when overflow, Next Route.
