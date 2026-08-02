---
name: teamwork-init
description: Use when the user asks to initialize, audit, repair, migrate, or slim project-local AI instructions, Teamwork context or memory, project routing, or local CodeGraph policy inside a named project; do not use for global skill, agent, policy, notification, plugin, or host installation and refresh.
---

# Teamwork Init

Make project-local agent context accurate, small, and maintainable.
Init owns only the named project.
That project-local ownership covers context, memory, routing, and CodeGraph
policy; do not run global refresh, global install, or host update work. The
exact role order
is Explorer read-only audit, then Worker mutation only for authorized, exact
project-local surfaces. Unavailable mandatory roles or unverifiable isolation are
`capability-blocked`; Root must not perform a named-method fallback.

## Authority

Audit/check-only is read-only. Explicit initialize, repair, migrate, or slim
authorizes only corresponding files inside the resolved project root. It does not
authorize user-global config, host settings, credentials, plugin catalogs, global
skills/agents, dependency installation, remote services, Git, release, or
publication. Root alone asks for missing mutation authority or unavoidable manual
host action as one exact gap, then resumes the same Init workflow. Discoverable
state and safe reversible defaults do not trigger a question. If the audit finds
an unformed migration, compatibility, or ownership tradeoff that materially
changes the outcome, reclassify it to Collaborate. Explorer and Worker never ask;
answers do not expand authority.

Resolve the exact root before writing. Preserve unrelated content and managed
blocks. If ownership is unclear and safe merging is impossible, stop with the
conflict.

## Audit And Mutate

1. Explorer audits instruction hierarchy, platform surfaces, human docs,
   source/configuration, commands, runbooks, `docs/teamwork/`, and configured
   CodeGraph policy. Ground rules in direct evidence; invent no paths,
   commands, architecture, model mappings, or capabilities.
2. Keep only stable behavior-changing facts: purpose, canonical owners,
   required commands, boundaries, source-of-truth paths, and local tool policy.
   Volatile progress stays in its tracker.
3. Give each fact one canonical owner; use short pointers or platform deltas
   elsewhere. Do not copy external docs, schemas, or manuals into instructions.
4. Treat external-memory or docs-graph output as candidate-only context. Promote
   it only when currentness, scope, direct evidence, privacy/protected-data
   review, and Root authority all pass; no logged, partial, permissive,
   fallback, or exception path promotes candidate material.
5. Emit the full Capability Matrix only for explicit full bootstrap.
6. When mutating a project whose local CodeGraph index is absent and the CLI is
   available, Root asks only whether to initialize that project-local index and
   passes the answer as `--codegraph` or `--no-codegraph`. Inherit an existing
   index without asking. Init never asks for the global performance/cost profile,
   never installs or configures GPU Broker, and never adds a Cursor calibration
   question. Do not install external tooling or alter host config without
   separate authority.
7. Worker applies the smallest complete authorized mutation and preserves
   operation recovery state. If the audit finds no decision-relevant change,
   dispatch no Worker and write nothing.
8. Re-read changed instruction surfaces and run the nearest real project-local
   validation or activation check; if none exists, state that limit.

Fresh v6 initialization creates v2 case-bundle memory and does not create
maintained `docs/teamwork/current.md` or `docs/teamwork/README.md`. Existing
legacy-v1 memory is read-only migration input for normal operation.

## Migration

Init may migrate only the exact project root named by Root and only after
explicit project migration/cutover authority. Use the package-owned helper for
that exact root, for example `scripts/teamwork-case-migration.py classify
--project-root <exact-project-root>` and `scripts/teamwork-case-migration.py
request-inputs --project-root <exact-project-root>` before cutover. If the
accepted migration requires `teamwork-case-migration.py migrate --project-root <exact-project-root>` or `teamwork-case-migration.py resume --project-root <exact-project-root>`
and the installed helper lacks that phase, stop
`capability-blocked` instead of scanning or inventing a replacement. Mixed,
unknown, stale, ambiguous case, missing seed/task_key, legacy-v1 without
explicit migration authority, or partial migration fails closed before any write.

## Receipt

A mutating Init in an initialized writable project defaults to a case-v2
completion companion unless `no files`, `off-record`, `read-only`, `no writes`,
or equivalent applies. Freeze a bounded receipt packet: purpose/audience,
facts/sources, decision/status, style/structure, artifact kind/consumer,
preserve/forbid, changed surfaces, evidence, validation, and human action.

Writer routes from observed schema: `case-inspect` first; case-v2 uses exact
`case_id`/alias or creates from a frozen seed/task_key, then `case-schema
<init-result> -> case-apply -> case-inspect/readback`. The transaction derives
destination and registers manifest/claim heads. Writer must not invent or alter
facts, authority, status, or validation. Missing project memory, Writer, packet,
authority, consumer, route, or transaction blocks only persistence: deliver the
receipt and report `unsaved/blocked`. No Root or Worker fallback writes it.
Claim saved/durable only after readback; interruption before apply gives no
durable claim.

Finish with selected project surface, changed/proposed files, ownership
decisions, verification strength, conflicts, manual action, and receipt state.
