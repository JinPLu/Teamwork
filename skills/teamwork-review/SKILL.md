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
   new record. Persist the checkpoint under Persistence before closeout; a host
   plan or question UI does not complete it.

A protected boundary is a requirement, criterion, candidate identity, or
behavior that must remain unchanged for this review record to stay valid.
Example: the public API contract or the frozen acceptance criteria. Keep one
review record per stable candidate identity. Any correction that changes
candidate content, scope, criteria, or a protected boundary creates a
successor candidate and a new document rather than overwriting the verdict
basis of the old candidate. The old record may receive only an
owner-certified successor link; its findings and verdict remain unchanged.
Preserve the candidate identity, criteria and protected boundaries, direct
evidence, findings and severity, status of each criterion, verdict, residual
uncertainty, and evidence-only bounded recheck scope.

A Reviewer handoff contains the objective, owned scope, settled user
constraints, available evidence, and requested return, naming the frozen
candidate, requirements, and requested verdict. Reviewer remains read-only
and never implements the repair.

## Persistence

Cross-chat memory lives in one Markdown document from `references/review.md`
at `docs/teamwork/reviews/<YYYY-MM-DD>-<slug>.md`. Same identity means the same
candidate; reuse that path and name the document you read. A different subject
gets a new path.

Checkpoints: a verdict is returned; a bounded recheck adds evidence for the
unchanged frozen candidate; or a successor candidate is opened after a
protected-boundary change. Keep user quotes separate from the working
understanding.

Prefer Writer, a helper role with its own writing contract, not a Skill. If
Writer is unavailable or returns a no-write, Root writes the same template to
the same path and marks Root fallback in the closeout. Review never blocks on
Writer; silently skipping a fired checkpoint is a Skill violation.
