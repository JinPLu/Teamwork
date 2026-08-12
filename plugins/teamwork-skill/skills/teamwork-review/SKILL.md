---
name: teamwork-review
description: Use when the user asks to review, audit, critique, or validate a stable code, document, plan, artifact, or claim; do not use to diagnose an unknown failure or create the initial candidate.
---

# Teamwork Review

Review judges one stable candidate against supplied requirements and direct
evidence. Prefer an independent Reviewer when the host can provide one. If it
cannot, Root may still provide a clearly labelled non-independent review instead
of switching workflows or blocking on installation state.

## Method

1. Identify the actual candidate, requirements, scope, settled constraints, and
   direct evidence needed for a verdict.
2. Read the candidate and applicable primary evidence. Do not substitute a
   version, identifier, marker, or test status for semantic inspection.
3. Always judge outcome fit. Judge engineering quality and real-path evidence
   only where they apply; missing evidence is `unknown`, not success.
4. Report material findings by severity with precise evidence, impact, and the
   smallest correction route. Keep unrelated debt separate.
5. Return `ACCEPT`, `REVISE`, or `BLOCKED`, plus residual uncertainty and the
   next action. A bounded recheck may add evidence only for the unchanged,
   frozen candidate. If a correction changes candidate content, scope,
   criteria, or a protected boundary, review it as a successor candidate in a
   new record.

Keep one review record per stable candidate identity. Any correction that
changes candidate content, scope, criteria, or a protected boundary creates a
successor candidate and a new document rather than overwriting the verdict
basis of the old candidate. The old record may receive only an
owner-certified successor link; its findings and verdict remain unchanged.
Preserve the candidate identity, criteria and protected boundaries, direct
evidence, findings and severity, status of each criterion, verdict, residual
uncertainty, and evidence-only bounded recheck scope.

A Reviewer handoff contains the candidate, requirements, scope, settled
constraints, direct evidence, and requested verdict. Reviewer remains read-only
and never implements the repair.

When a durable review record is useful or requested, Root may ask Writer to
maintain it from `references/review.md`. Every wake-up supplies
the document kind and path, stable candidate identity, authoritative review
owner, owner-certified semantic delta, read-only context, and expected base.
Writer only compresses literally, locates, deduplicates the current synthesis
and pending delta, refreshes current synthesis, and appends dated history.
Existing history is immutable. It cannot create or alter a finding,
severity, criterion status, verdict, uncertainty, authority, next action, or
mainline. Missing state or a conflicting base produces a no-write exact gap.
Writer unavailability or conflict does not block the review; if the document
was explicitly requested, only its delivery remains incomplete.
