---
name: teamwork-review
description: Use when the user asks to review, audit, critique, or validate a stable code, document, plan, artifact, or claim, or when the current authorized mutation crosses an actual independent-review gate; do not use to diagnose an unknown failure, gather ordinary evidence, implement fixes, or create the initial candidate.
---

# Teamwork Review

Review is the current independent-evaluation stage. Root identifies the actual
effect of the authorized work and selects ordinary or Strict Review; Reviewer
owns the chosen read-only evaluation. Root does not simulate required
independence or let the candidate's author accept their own work.

## Establish The Candidate

Identify the stable candidate with its natural handle, such as exact files and
diff, artifact path and version, document revision, or supplied text. State the
scope, acceptance criteria, protected boundaries, and direct evidence needed
for a verdict. Do not invent requirements or substitute an identifier, test
status, or summary for reading the actual candidate.

## Classify The Actual Effect

Ordinary Review is the default, including an ordinary release. It uses one
independent semantic Reviewer on the actual candidate.

Strict Review applies only when the current authorized mutation actually
crosses at least one of these boundaries:

- permission or security behavior;
- an irreversible effect on user data;
- migration of persistent data; or
- changed published compatibility or another public contract.

The request's keywords, importance, complexity, research topic, or subjective
risk do not activate Strict Review. When a listed boundary is real, read
`references/strict-review.md`. Additional independent review is useful only for
separable bounded effects where it changes the gate; no reviewer count is
prescribed.

## Evaluate

Evaluate claim-sensitive lenses independently. Outcome fit is always judged
against the supplied requirements and criteria and is never not applicable.
When requirements or applicable outcome evidence are missing, record outcome
fit as unknown. Engineering quality applies
only when the candidate has an engineering surface such as code, configuration,
automation, schema, tests, deployment, migration, or comparable implementation
work. Real-path evidence applies only to runtime, host, rendered, external, or
execution claims. Missing applicable evidence is `unknown`, not success; `not
applicable` requires a candidate-specific reason. Lenses cannot compensate for
one another, so a satisfied lens does not erase an adverse or unknown result in
another applicable lens.

Inspect primary evidence directly: candidate content, source and diff, runtime
behavior, rendered output, tests and configuration, or authoritative sources as
applicable. Review the actual effects against the supplied criteria, focusing
on material correctness and missing proof. Report findings by severity with
precise evidence, impact or failed criterion, and the smallest correction
route. Keep unrelated pre-existing debt separate.

Return `ACCEPT` when the material criteria are supported and no blocker remains,
`REVISE` when correctable blockers remain, or `BLOCKED` when required evidence
or access is unavailable. Recheck only the changed candidate surface needed to
close findings; materially broadened work is a new candidate. Reviewer never
implements the repair or declares the surrounding task complete.

Reviewer is required. If unavailable, Root suspends Review, switches to Update
for readiness repair, waits, and resumes or returns the exact blocker. Root
cannot recreate the independence by reviewing in the missing role's place.

## Codex Role Dispatch

On Codex, dispatch Reviewer and Writer through `spawn_agent.agent_type` as
`teamwork_reviewer` and `teamwork_writer`. Use `fork_turns` set to `none` or a
bounded recent context, then observe a live child start; never silently
substitute an unavailable role.

When context is omitted or bounded, the brief must include every still-applicable
settled user constraint. A child cannot infer that a missing constraint was relaxed.

A live child start proves the role is active. Do not impose an arbitrary return
deadline or replace it; wait for its terminal result unless the user interrupts
it or the host reports a terminal failure.

## Review Document

When a stable candidate plus direct evidence or a finding becomes reusable,
Root assigns Writer the typed Review document. It carries candidate scope and
criteria, protected boundaries, evidence and findings by severity, the semantic
verdict, residual uncertainty, next action, and any bounded recheck. Writer may
not alter findings or the verdict. Same-scope editorial or link corrections may
update a finalized document; a new candidate or materially new scope needs a
new Review document.
