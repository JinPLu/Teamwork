---
name: teamwork-init
description: Use when the user asks to initialize, audit, repair, migrate, or slim project-local AI instructions, Teamwork context or memory, project routing, or local CodeGraph policy inside a named project; do not use for global skill, agent, policy, notification, plugin, or host installation and refresh.
---

# Teamwork Init

Make project-local agent context accurate, small, and maintainable. This skill
owns only the named project; it never refreshes global Teamwork installations.
Collaborate owns natural dialogue, brainstorming, stress-testing, and decision
convergence; Init activates only when the requested outcome is an actual
project-local context, memory, routing, or CodeGraph setup change. The role
order is exact: Explorer performs the read-only audit first; only after explicit
authorized changes are identified does Worker mutate exact project-local
surfaces. If either mandatory role is unavailable or required isolation cannot
be verified, return `capability-blocked`; Root must not perform a named-method
fallback.

## Authority

An audit request is read-only. An explicit initialize, repair, migrate, or slim
request authorizes only the corresponding files inside the named project. It does
not authorize edits under user-global config directories, host settings,
credentials, plugin catalogs, global skills or agents, dependency installation,
remote services, Git publication, or release work.
Root alone asks users through the current host's native surface; leaf roles
return proposed questions or blockers to Root. Ask only for missing mutation
authority or unavoidable manual host action. Answers do not expand authority.

Resolve the exact project root before writing. Preserve unrelated content and
managed-block boundaries. If ownership is unclear and safe merging is impossible,
stop with the concrete conflict instead of overwriting.

## Full Bootstrap And Candidate Inputs

Emit the complete Capability Matrix only for an explicit full bootstrap. Audit,
repair, migration, or slimming must not manufacture that broad matrix merely from
some platform inspection.

Treat external-memory or docs-graph output as candidate-only context, never as
project or Teamwork truth. Candidate-promotion gates (all must pass): currentness
| scope | direct evidence | privacy/protected-data review | Root authority. Do not
promote it into instructions, memory, routing, or durable artifacts until those
five gates pass. A logged, partial, or permissive gate result is not promotion; a
failed or missing gate leaves the candidate unpromoted and is reported as a
concrete limitation. No logged, partial, permissive, fallback, or exception path
promotes candidate material.

## Project Workflow

1. Dispatch Explorer for the read-only audit of instruction hierarchy,
   platform surfaces, human docs, source/configuration, test commands, runbooks,
   and `docs/teamwork/` context. Ground every durable rule in project evidence;
   do not invent commands, paths, architecture, model mappings, or capabilities.
2. Keep only stable behavior-changing facts: project purpose, canonical owners,
   required commands, boundaries, source-of-truth paths, and local tool policy.
   Leave volatile progress, experiments, and temporary failures in their tracker.
3. Give each fact one canonical owner. Merge duplicates and use short pointers or
   platform deltas elsewhere. Do not copy external docs, schemas, or manuals into
   project instructions.
4. Keep local inspection and clear authorized implementation native. Describe
   special tools such as CodeGraph only when configured or requested, with use and
   unavailable behavior.
5. For Teamwork memory, preserve ordinary retrieval metadata separately from the
   single managed Collaborate record. Never rebuild a collaborate transaction,
   hidden lifecycle, or skill-reference graph.
6. Initialize a repository-local CodeGraph index only when the requested setup
   includes it and the CLI is available. Otherwise report the exact gap; do not
   install external tooling or change host configuration without separate
   authority.
7. Only after the audit identifies an authorized change, dispatch Worker with
   exact project-local ownership. Worker applies the smallest complete mutation,
   preserves recovery state for the whole operation, and fails closed on
   ownership or migration conflicts. Root retains any privileged host action.
8. Re-read every changed instruction surface and exercise the nearest real
   project-local validation or command. If no real activation check is available,
   state that limit instead of treating syntax or file presence as live proof.

An audit/check-only Init remains read-only and conversational. After a mutating
Init in an initialized writable project, a receipt is a case-v2 completion
companion and defaults through Writer unless the user says `no files`,
`off-record`, `read-only`, `no writes`, or equivalent. Freeze a bounded receipt packet:
purpose/audience, facts/sources, frozen decision/status, style/structure,
artifact kind/consumer, preserve/forbid, changed surfaces, evidence, validation,
and human action. Dispatch one low-cost Writer; Root may do only
answer-invariant handoff work while Writer runs and must join and read back
before claiming the receipt is saved or durable. Writer routes from observed
schema: `case-inspect` first; case-v2 uses exact `case_id`/alias or creates from
a frozen seed/task_key, then `case-schema <init-result> -> case-apply ->
case-inspect/readback`. The transaction derives the destination and registers
the case manifest/claim heads.
Writer is disposable compute and the transaction owns destination,
compare-and-swap, journal recovery, atomic apply, and readback. If interrupted
before apply begins, there is no durable claim; recover only from surviving
workflow evidence or report unsaved. Missing project memory, Writer, brief,
authority, consumer, route, or transaction blocks only persistence: deliver the
receipt and report it unsaved/blocked. No Root or Worker fallback writes it.
Fresh v6 project initialization creates v2 case-bundle memory and does not
create maintained `docs/teamwork/current.md` or `docs/teamwork/README.md`.
Existing legacy-v1 memory is read-only migration input and is not used for
normal Collaborate, Goal, or artifact writes. Init may migrate only the exact
project root named by Root and only after explicit project migration/cutover
authority. Use the package-owned helper for that exact root, for example
`scripts/teamwork-case-migration.py classify --project-root <exact-project-root>`
and `scripts/teamwork-case-migration.py request-inputs --project-root
<exact-project-root>` before any cutover. If the accepted migration requires
`teamwork-case-migration.py migrate --project-root <exact-project-root>` or
`teamwork-case-migration.py resume --project-root <exact-project-root>` and the
installed helper does not expose that phase, stop `capability-blocked` instead
of scanning or inventing a replacement. Mixed, unknown, stale, ambiguous case,
missing seed/task_key, legacy-v1 without explicit migration authority, or
partially migrated memory fails closed before any write.

If the Explorer audit finds no decision-relevant change, dispatch no Worker and
write nothing. Report the selected
project surface, changed or proposed files, canonical ownership decisions,
verification strength, conflicts, and any remaining human action. Never invoke a
global update as part of project initialization.
