# Research Protocol

Use for evidence gathering that can affect implementation, spending, public claims, current APIs, or external recommendations.

## Modes

- `lookup`: one stable fact or source. Answer locally with citation. Skip Search Plan and source census.
- `research`: several sources, options, or unknowns. Write concise synthesis. Fan out queries; triage sources; label observed/inferred/claimed.
- `deep`: high-stakes, current, or multi-domain work. Use query fanout, source census, contradiction search, and coverage audit. Store overflow in artifacts.

Runtime diagnosis with repro, instrumentation, logs, browser state, or CI output
belongs to `teamwork-debug`; research frames unknown source/repro questions and
hands off when runtime evidence becomes decisive.

## Source Census (deep mode)

Build before broad reads: URL/path, source class, primary/secondary, freshness, relevance, read/reject reason. Use when candidates exceed 6, expected sources exceed 10, source classes exceed 3, or the result feeds a durable plan.

## Flow (research and deep)

1. Clarify the question when goals, constraints, timeframe, or output format are underspecified.
2. Write a Search Plan: source classes, expected primary sources, exclusion criteria, freshness needs.
3. Fan out queries by independent concepts, names, versions, failure modes, and dissent terms.
4. Triage sources: prefer official docs, specs, repos, papers, filings, changelogs, and direct data over summaries.
5. For current external library/API questions, use an approved docs MCP (e.g. Context7) when available; treat returned snippets as candidate/supporting evidence until corroborated with primary source, tests, or verified behavior.
6. Label evidence: observed, inferred, claimed.
7. Run contradiction search and note Sources Rejected with reasons.
8. Audit coverage: missing source classes, stale assumptions, language/region gaps.
9. Produce capped Citation Ledger, Confidence, artifact pointer when overflow exists, and route gaps back to research or plan.

## Public/Private Safety

Stage public web research separately from private files, MCP connectors, or credentials. Never send private repository facts, customer data, or secrets into public queries. Summarize private context locally, then search only public concepts.

## Output Fields

Queries Tried, Source Census (deep only), Sources Used, Sources Rejected, Contradictions, Coverage Gaps, Citation Ledger, Confidence, Artifact Pointer when overflow, Next Route.
