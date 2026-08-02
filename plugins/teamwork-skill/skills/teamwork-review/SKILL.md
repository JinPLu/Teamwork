---
name: teamwork-review
description: Use when the user asks to review, audit, critique, validate, or decide whether a candidate or claim is correct or complete, or when an active workflow reaches a named material risk gate requiring independent review of one sealed integrated candidate; do not use for each Worker slice, to implement fixes, write a plan, or perform ordinary evidence collection.
---

# Teamwork Review

Issue an evidence-based `ACCEPT`, `REVISE`, or `BLOCKED` verdict. Review is
read-only: do not edit, fix, publish, or perform external effects. The exact
role mapping is Review -> Reviewer, and Plan Review -> Plan Reviewer. If a
mandatory role is unavailable or fresh isolation cannot be verified, return
`capability-blocked`; Root must not perform a named-method fallback.

Reviewer and Plan Reviewer never ask the user or invent missing requirements.
Return an exact proof gap or ambiguity blocker with owner, scope, and closing
evidence. If the ambiguity is a material unformed direction rather than missing
proof, return a reclassification signal to Collaborate through Root.

Each Worker self-verifies its owned slice. Do not review each Worker slice
independently. Root integrates authorized changes and seals one stable candidate
with scope and direct evidence. Run one independent initial pass on that sealed
integrated candidate only for user-requested review or named material risk gate;
a gate may review its exact protected boundary earlier only when delay would
invalidate proof.

## Method

1. Establish candidate identity, sealed_digest, scope, acceptance criteria,
   protected boundaries, and evidence needed for the verdict. Do not invent
   requirements.
2. Inspect primary evidence directly: source/diff, tests/configuration, runtime
   output, rendered artifacts, or authoritative external sources. Summaries and
   claimed test results are inputs, not proof.
3. Check correctness first: acceptance criteria, security/permission boundaries,
   data behavior, regressions, error paths, compatibility, unsupported claims,
   and real-path evidence.
4. Then inspect only the changed scope for cohesion and deslop: wrong owner,
   duplicate owner, thin wrapper, dead code, speculative abstraction,
   unnecessary compatibility mode, broad catch, masking fallback, temporary
   residue, and stale touched comments/config. Accepted product fallbacks and
   pre-existing debt are negative controls, not blockers.
5. Give each finding a stable `R-*` ID and classify it once as `BLOCKER`,
   `FOLLOW-UP`, or `SUGGESTION`; include evidence, affected criterion or user
   impact, and smallest correction route.

Load `references/strict-review.md` only for named strict release, security,
permission, data, destructive-risk, or public-contract gates.

Maintain visible monotonic Review state: `sealed_digest`, stable finding IDs,
`verdict`, `repair_batch`, and `delta_recheck`. Failed, blocked, partial, and
unverified findings change only with direct new evidence tied to the same sealed
candidate or one allowed delta candidate. Combine initial blockers into one repair batch.
The same Reviewer may perform at most one bounded delta recheck;
source changes after that create a new candidate. Root retains final acceptance.

## Persistence And Output

Reviewer always stays read-only. In an initialized writable project, every
terminal verdict defaults to a case-v2 review artifact unless `no files`,
`off-record`, `read-only`, `no writes`, or equivalent applies. Verdict and
persistence are separate: deliver the verdict even if the completion companion
cannot be saved, and state `unsaved/blocked`. Persistence does not imply
Root/user acceptance.

Freeze the verdict packet: purpose/audience, facts/sources, decision/status,
style/structure, artifact kind/consumer, preserve/forbid, findings, evidence,
verdict, repair batch, delta recheck status, and residual risk. Writer routes
from observed schema: `case-inspect` first; case-v2 uses exact `case_id`/alias
or creates from a frozen seed/task_key, then `case-schema
<review-add|code-review-add|plan-review-add> -> case-apply ->
case-inspect/readback`. The transaction derives destination and registers
manifest/claim heads. Writer must not invent or alter facts, authority, status,
findings, verdict, or acceptance. Claim saved/durable only after readback.
Missing project memory, Writer, packet, authority, consumer, route, or
transaction blocks only persistence. No Reviewer, Root, or Worker fallback
writes it. Legacy-v1, mixed v1/v2, unknown, stale, ambiguous case, missing
seed/task_key, or partially migrated state fails closed before any write.

Lead with blockers by severity and precise file/line or artifact location. If
none, say so. `ACCEPT` requires support for every material criterion and no open
blocker; `REVISE` means correctable blockers remain; `BLOCKED` means required
evidence or access is unavailable. Reviewer never asks the user; propose missing
user-providable evidence to Root.
