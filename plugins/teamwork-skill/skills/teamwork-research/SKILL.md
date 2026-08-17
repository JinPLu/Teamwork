---
name: teamwork-research
description: Use when a broad or deep external investigation needs multiple source classes, claim-level evidence synthesis, or contradiction resolution; do not use for a narrow lookup or local code inspection.
---

# Teamwork Research

Keep narrow lookups native. When Research is activated, investigate the complete
question rather than creating a lightweight ritual around a few searches. Read
`references/deep-research.md` for the detailed method.

## Method

1. Define the decision question, intended use, scope, freshness cutoff, privacy
   boundary, and material claims.
2. Search the strongest primary and current sources first, then add independent
   source classes where they can change confidence.
3. Connect each material claim to direct support, counterevidence, inference,
   confidence, date, and nearby citation.
4. Investigate contradictions and explain rejected sources or unresolved gaps.
5. Stop when the scope is answered or further retrieval is unlikely to change
   the conclusion; state which condition applies. Persist the checkpoint under
   Persistence before closeout; a host plan or question UI does not complete it.

Maintain an early provisional conclusion as evidence develops, clearly marked
as provisional. The research synthesis must preserve the decision use, a
question tree, a claim-to-evidence table, contradictions and unknowns, coverage
and stop conditions, and notes for every source that actually participated in
the reasoning; source notes are embedded in the document rather than delegated
to a separate index.

A Researcher may own a bounded investigation. Use Explorer when available;
otherwise use native local search for project facts. Give each subagent the
objective, owned scope, settled user constraints, sanitized evidence, and
requested return. Their availability is not a workflow gate; Root may perform
the method directly with available research tools.

## Persistence

Cross-chat memory lives in one Markdown document from `references/research.md`
at `docs/teamwork/research/<YYYY-MM-DD>-<slug>.md`. Same identity means the same
research question; reuse that path and name the document you read. A different
subject gets a new path.

Checkpoints: a material claim-to-evidence synthesis is first settled;
contradictions change confidence or the conclusion; or a stop condition is
reached. Keep user quotes separate from the working understanding.

Prefer Writer, a helper role with its own writing contract, not a Skill. If
Writer is unavailable or returns a no-write, Root writes the same template to
the same path and marks Root fallback in the closeout. Investigation never
blocks on Writer; silently skipping a fired checkpoint is a Skill violation.
