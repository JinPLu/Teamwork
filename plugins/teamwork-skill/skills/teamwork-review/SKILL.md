---
name: teamwork-review
description: Use when the user asks to review, audit, critique, validate, or decide whether a candidate or claim is correct or complete, or when an active workflow reaches a named material risk gate requiring independent review of one sealed integrated candidate; do not use for each Worker slice, to implement fixes, write a plan, or perform ordinary evidence collection.
---

# Teamwork Review

Issue an evidence-based `ACCEPT`, `REVISE`, or `BLOCKED` verdict. Review is
read-only: do not edit the candidate, apply fixes, publish, or perform external
effects even when a fix seems obvious. The role mapping is exact:
Review -> Reviewer, and Plan Review -> Plan Reviewer. If the mandatory role is
unavailable or required fresh isolation cannot be verified, return
`capability-blocked`; Root must not perform a named-method fallback.

Each Worker self-verifies its owned slice. Do not review each Worker slice or
code delta independently. Root integrates authorized changes and seals one stable
candidate with scope and direct evidence. Run one independent initial pass on
that sealed integrated candidate only for user-requested review or a named
material risk gate. A named risk gate may review its exact protected boundary
before integration when delay would invalidate proof.

## Method

1. Establish candidate, scope, acceptance criteria, protected boundaries, and
   evidence needed for the verdict. User-requested review takes precedence over
   inferred criteria; do not invent requirements.
2. Inspect primary evidence directly: source and diff, tests and configuration,
   runtime output, rendered artifacts, or authoritative external sources as the
   candidate requires. A summary or claimed test result is input, not proof.
3. Check correctness first: acceptance criteria, security/permission boundaries,
   data behavior, regressions, error paths, compatibility, and direct real-path
   evidence. Do not let style or cleanup substitute for this pass.
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
evidence. Combine initial findings into one repair batch. The same Reviewer may
perform at most one bounded delta recheck per candidate, limited to stable
findings and fix-introduced regressions. Any source change after that creates a
new candidate; expanded scope requires a fresh review decision. Root retains final acceptance.

Maintain visible monotonic Review state: `sealed_digest`, stable finding IDs,
`verdict`, `repair_batch`, and `delta_recheck`. A finding may close only with
direct new evidence tied to the same sealed candidate or the one allowed delta
candidate. Reused summaries, changed scope, or missing candidate identity cannot
weaken a blocker.

Reviewer always stays read-only. In an initialized writable project, every verdict
defaults to a case-v2 review artifact unless the user says `no files`,
`off-record`, `read-only`, `no writes`, or equivalent. Freeze the terminal
verdict before persistence. Root freezes the verdict and Reviewer returns a
bounded packet: purpose/audience, facts/sources, frozen decision/status,
style/structure, artifact kind/consumer, preserve/forbid, findings, evidence,
verdict, repair batch, delta recheck status, and residual risk. Writer routes
from observed schema: `case-inspect` first; case-v2 uses exact `case_id`/alias
or creates from a frozen seed/task_key, then
`case-schema <review-add|code-review-add|plan-review-add> -> case-apply ->
case-inspect/readback`. The transaction derives the destination and registers
the case manifest/claim heads.
Writer is disposable; Root may continue only answer-invariant delivery work and
must join before claiming saved or durable. Interruption before apply means
unsaved unless surviving evidence permits a new frozen packet. Missing project
memory, Writer, brief, authority, consumer, route, or transaction blocks only
persistence: deliver the verdict and report it unsaved/blocked. No Reviewer,
Root, or Worker fallback writes it. Persistence does not imply Root/user
acceptance. In v2 case-bundle projects, Review writes only transaction-derived
case review artifacts and the single allowed delta review for the sealed
candidate. Plan Review and code Review remain separate consumers. Legacy-v1,
mixed v1/v2, unknown, stale, ambiguous case, missing seed/task_key, or partially
migrated state fails closed before any write.

Lead with blockers ordered by severity and include precise file/line or artifact
locations when available. If there are no findings, say so explicitly. `ACCEPT`
requires direct support for every material criterion and no open blocker;
`REVISE` means correctable blockers remain; `BLOCKED` means required evidence or
access is unavailable. Reviewer never asks the user; propose missing
user-providable evidence to Root before declaring `BLOCKED`, but make no change.
Candidate changes invalidate the old review and require a new sealed candidate.
