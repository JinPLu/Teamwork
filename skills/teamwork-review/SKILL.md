---
name: teamwork-review
description: Use when the user asks to review, audit, critique, or validate a stable code, document, plan, artifact, or claim, or when a named material risk gate requires independent evaluation; do not use to find the cause of an unknown failure, gather ordinary evidence, implement fixes, or create the initial plan.
---

# Teamwork Review

Use Reviewer to evaluate a stable candidate independently. Reviewer remains
read-only and may review implementation plans as well as completed code,
documents, artifacts, and claims.

## Establish The Candidate

Identify the candidate by the most natural stable handle: exact files and diff,
commit, artifact path and version, document revision, or supplied text. A hash
is optional integrity evidence, not a semantic acceptance gate. Record the
scope, acceptance criteria, protected boundaries, and evidence needed for a
verdict. Do not invent requirements.

## Review

1. Inspect primary evidence directly: candidate content, source and diff,
   tests and configuration, runtime output, rendered artifact, or authoritative
   sources. Treat summaries and claimed results as leads rather than proof.
2. Check the acceptance criteria and highest-impact failure modes first,
   including permissions, security, data behavior, error paths, regressions,
   compatibility, unsupported claims, and real-path verification when relevant.
3. Inspect the changed scope for wrong ownership, duplication, masking
   fallbacks, speculative abstraction, temporary residue, and stale touched
   documentation or configuration. Do not turn unrelated pre-existing debt into
   a blocker.
4. Report findings by severity with precise evidence, impact or violated
   criterion, and the smallest correction route. Separate blockers from
   follow-ups and suggestions.

Load `references/strict-review.md` only for an explicitly named release,
security, permission, data, destructive-risk, or public-contract gate. Missing
required access or evidence produces `BLOCKED`; plausible but unobserved concern
is not proof.

Return `ACCEPT` when all material criteria are supported and no blocker remains,
`REVISE` when correctable blockers remain, or `BLOCKED` when required evidence
is unavailable. Recheck only the changed candidate surface needed to close
findings; treat materially broadened work as a new candidate. Reviewer does not
implement repairs or accept the overall task on the implementer's behalf.

## Live Document

Have Writer maintain the task's single live document with a review shape; reuse
it rather than creating a parallel artifact. Create it when the candidate and
first reusable evidence are established, update it only when the candidate,
evidence, finding, verdict, residual risk, or recheck result materially changes,
and finalize it at the verdict. Include candidate identity, scope, criteria,
evidence, findings by severity, verdict, residual risk, and any bounded recheck.
Writer must not change findings, evidence, or acceptance.
