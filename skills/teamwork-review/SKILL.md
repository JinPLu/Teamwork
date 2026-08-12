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
   next action. Recheck only the changed surface needed to close findings.

A Reviewer handoff contains the candidate, requirements, scope, settled
constraints, direct evidence, and requested verdict. Reviewer remains read-only
and never implements the repair.
