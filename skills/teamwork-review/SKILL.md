---
name: teamwork-review
description: Use when the user asks to review, audit, critique, validate, or decide whether a candidate or claim is correct or complete, or a named material risk gate requires independent review of a sealed integrated candidate; do not use for each Worker slice, to implement fixes, write a plan, or perform ordinary evidence collection.
---

# Teamwork Review

Issue an evidence-based `ACCEPT`, `REVISE`, or `BLOCKED` verdict. Review is
read-only: do not edit the candidate, apply fixes, publish, or perform external
effects even when a fix seems obvious.

Each Worker self-verifies its owned slice. Do not review each Worker slice or
each code delta independently. Root first integrates the authorized changes and
seals one stable candidate with its scope and direct evidence. Run one independent
initial pass on that sealed integrated candidate only when the user requests
review or a named material risk gate requires it. A named risk gate may instead
review its exact protected boundary before integration when delay would make the
proof unsafe or invalid.

## Method

1. Establish the candidate, scope, acceptance criteria, protected boundaries,
   and evidence needed for the verdict. User-requested review takes precedence
   over inferred criteria; do not invent new requirements.
2. Inspect primary evidence directly: source and diff, tests and configuration,
   runtime output, rendered artifacts, or authoritative external sources as the
   candidate requires. A summary or claimed test result is input, not proof.
3. Check correctness first: acceptance criteria, security and permission
   boundaries, data behavior, regressions, error paths, compatibility, and direct
   real-path evidence. Do not let style or cleanup substitute for this pass.
4. Then inspect only the changed scope for cohesion and deslop: wrong-layer or
   duplicate owners, thin wrappers, dead code, speculative or single-consumer
   abstractions, unnecessary compatibility or parallel modes, broad catches,
   masking fallbacks, unnecessary public surface, temporary residue, and stale
   touched comments or configuration. A justified multi-file boundary, an
   explicitly accepted product fallback, and purely pre-existing debt are
   negative controls, not blockers.
5. Give each finding a stable `R-*` ID and classify it once:
   - `BLOCKER`: a failed acceptance criterion, regression, boundary breach, or
     missing evidence required for the verdict;
   - `FOLLOW-UP`: a real non-blocking issue outside the accepted result;
   - `SUGGESTION`: an optional improvement.
6. State the concrete evidence, affected criterion or user impact, and smallest
   correction route. Do not promote an out-of-scope improvement into a blocker
   unless the current acceptance criteria cannot pass without it.

Load `references/strict-review.md` only for a named strict release, security,
permission, data, destructive-risk, or public-contract gate.

Failed, blocked, partial, and unverified findings change only with new direct
evidence. Combine all findings from the initial pass into one repair batch. The
same Reviewer may perform at most one bounded delta recheck per candidate, limited
to the stable findings and fix-introduced regressions. Any source change after
that recheck creates a new candidate; materially expanded scope requires a fresh
review decision. The root owner retains final acceptance.

Lead with blockers ordered by severity and include precise file/line or artifact
locations when available. If there are no findings, say so explicitly. `ACCEPT`
requires direct support for every material criterion and no open blocker;
`REVISE` means correctable blockers remain; `BLOCKED` means required evidence or
access is unavailable. Ask for missing user-providable evidence before declaring
`BLOCKED`, but make no change.
