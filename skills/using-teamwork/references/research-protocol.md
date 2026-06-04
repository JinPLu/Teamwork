# Research Protocol

Use this for evidence gathering that can affect implementation, spending,
public claims, current APIs, or external recommendations.

## Modes

- `lookup`: one stable fact or source; answer locally with citation.
- `research`: several sources, options, or unknowns; write concise synthesis.
- `deep-research`: high-stakes/current/multi-domain work; use query fanout,
  contradiction search, and coverage audit.
- `source-audit`: verify whether research missed primary sources, dissent,
  version changes, or disconfirming evidence.

## Flow

1. Clarify or rewrite the question when goals, constraints, timeframe,
   audience, source class, or output format are underspecified.
2. Write a Search Plan: source classes, expected primary sources, exclusion
   criteria, and freshness needs.
3. Fan out queries by independent concepts, names, versions, failure modes,
   and dissent terms; do not rely on one broad query.
4. Triage sources: prefer official docs, specs, repos, papers, filings,
   changelogs, issue threads, and direct data over summaries.
5. Read enough primary text to extract evidence; label observed, inferred, and
   claimed.
6. Run contradiction search and note Sources Rejected with reasons.
7. Audit coverage: missing source classes, stale assumptions, language/region
   gaps, and whether web-search context size limited recall.
8. Produce Citation Ledger and Confidence; route gaps back to research or plan.

## Public/Private Safety

Stage public web research separately from private files, MCP, connectors, or
credentials. Never send private repository facts, customer data, secrets, or
non-public business details into public web queries. Summarize private context
locally, then search only for public concepts.

## Output Fields

Search Plan, Queries Tried, Source Classes, Sources Used, Sources Rejected,
Contradictions, Coverage Gaps, Citation Ledger, Confidence, Next Route.
