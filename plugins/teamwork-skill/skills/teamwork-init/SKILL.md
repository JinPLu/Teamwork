---
name: teamwork-init
description: Use when the user asks to initialize, audit, repair, migrate, or slim project-local AI instructions, Teamwork context or memory, project routing, or local CodeGraph policy inside a named project; do not use for global skill, agent, policy, notification, plugin, or host installation and refresh.
---

# Teamwork Init

Make project-local agent context accurate, small, and maintainable. This skill
owns only the named project; it never refreshes global Teamwork installations.

## Authority

An audit request is read-only. An explicit initialize, repair, migrate, or slim
request authorizes only the corresponding files inside the named project. It does
not authorize edits under user-global config directories, host settings,
credentials, plugin catalogs, global skills or agents, dependency installation,
remote services, Git publication, or release work.

Resolve the exact project root before writing. Preserve unrelated user content
and existing managed-block boundaries. If ownership of an existing file is
unclear and safe merging is impossible, stop with the concrete conflict instead
of overwriting it.

## Full Bootstrap And Candidate Inputs

Emit the complete Capability Matrix only for an explicit full bootstrap. An
audit, repair, migration, or slimming request must not manufacture that broad
matrix merely because it inspects some platform surfaces.

Treat external-memory or docs-graph output as candidate-only context, never as
project or Teamwork truth. Candidate-promotion gates (all must pass): currentness
| scope | direct evidence | privacy/protected-data review | Root authority. Do not
promote it into instructions, memory, routing, or durable artifacts until those
five gates pass. A logged, partial, or permissive gate result is not promotion; a
failed or missing gate leaves the candidate unpromoted and is reported as a
concrete limitation. No logged, partial, permissive, fallback, or exception path
promotes candidate material.

## Project Workflow

1. Dispatch Explorer for the read-only audit of the instruction hierarchy,
   applicable platform surfaces, canonical human docs, source/configuration,
   test commands, runbooks, and
   existing `docs/teamwork/` context. Ground every durable rule in project
   evidence; do not invent commands, paths, architecture, model mappings, or
   capabilities.
2. Keep only stable facts that change agent behavior: project purpose, canonical
   owners, required commands, boundaries, source-of-truth paths, and local tool
   policy. Leave volatile progress, experiment output, and temporary failures in
   their actual tracker or artifact.
3. Give each fact one canonical owner. Merge duplicates and use short pointers or
   platform-specific deltas elsewhere. Do not copy external documentation,
   schemas, or large workflow manuals into project instructions.
4. Keep local inspection and clear authorized implementation native. Describe
   special tools such as CodeGraph only when configured or requested, including
   when they should be preferred and what to do when unavailable.
5. For Teamwork memory, preserve ordinary retrieval metadata separately from the
   single optional Grill record. Never rebuild a discussion transaction, hidden
   lifecycle, or skill-reference graph.
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

If the Explorer audit finds no decision-relevant change, dispatch no Worker and
write nothing. Report the selected
project surface, changed or proposed files, canonical ownership decisions,
verification strength, conflicts, and any remaining human action. Never invoke a
global update as part of project initialization.
