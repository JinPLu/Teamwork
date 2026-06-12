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
- `workflow-class research`: many candidates or sources; use source census,
  Explorer waves, and artifact-backed synthesis outside the main thread.

## Context Budget

Broad research stays broad, but raw search logs, source transcripts, large
matrices, and long citation ledgers stay out of chat. Use source census when
candidates exceed 6, expected sources exceed 10, source classes exceed 3, or
the result feeds a durable plan. Store overflow in artifacts and return only
decision-relevant compressed evidence.

## Flow

1. Clarify or rewrite the question when goals, constraints, timeframe,
   audience, source class, or output format are underspecified.
2. Write a Search Plan: source classes, expected primary sources, exclusion
   criteria, and freshness needs.
3. Fan out queries by independent concepts, names, versions, failure modes,
   and dissent terms; do not rely on one broad query.
4. Build source census before deep reads when broad: URL/path, source class,
   primary/secondary, freshness, relevance, and read/reject reason.
5. Triage sources: prefer official docs, specs, repos, papers, filings,
   changelogs, issue threads, and direct data over summaries.
6. Read enough selected primary text to extract evidence; label observed, inferred, and
   claimed.
7. Run contradiction search and note Sources Rejected with reasons.
8. Audit coverage: missing source classes, stale assumptions, language/region
   gaps, and whether web-search context size limited recall.
9. Produce capped Citation Ledger, Confidence, artifact pointer when overflow
   exists, and route gaps back to research or plan.

## Public/Private Safety

Stage public web research separately from private files, MCP, connectors, or
credentials. Never send private repository facts, customer data, secrets, or
non-public business details into public web queries. Summarize private context
locally, then search only for public concepts.

## Output Fields

Search Plan, Queries Tried, Source Census when broad, Source Classes, Sources
Used, Sources Rejected, Contradictions, Coverage Gaps, Citation Ledger,
Confidence, Artifact Pointer when overflow exists, Next Route.
