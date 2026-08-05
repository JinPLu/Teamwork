---
name: teamwork-init
description: Use when the user asks to initialize, audit, repair, or slim project-local AI instructions, current-format Teamwork context, task documents, project routing, or local CodeGraph policy inside a named project; do not use for global Teamwork installation, host configuration, or conversion of existing Teamwork documents.
---

# Teamwork Init

Keep project-local AI context accurate, small, and maintainable. Resolve the
exact project root first. Use Explorer for read-only discovery and Worker only
for requested mutations allowed by the current host and tool authority. Do not
create a second approval protocol inside the Skill.

## Inspect

1. Read the applicable instruction hierarchy and identify canonical owners,
   generated surfaces, local commands, task-document state, and CodeGraph
   policy before proposing changes.
2. Ground project facts in current source, configuration, tests, scripts, and
   version-control evidence. Do not invent paths, capabilities, commands, or
   architecture.
3. Keep only stable behavior-changing context: purpose, owners, required
   commands, boundaries, source-of-truth paths, and local tool policy. Leave
   volatile progress in its live task document.
4. Give each fact one canonical owner and use short pointers elsewhere. Avoid
   copying manuals, schemas, or external documentation into project
   instructions.
5. Distinguish Teamwork-managed content from user-owned content. Preserve
   unrelated material and report an ownership conflict when safe merging is not
   possible.

If the user requested only an audit, stop after Explorer's evidence-backed
findings. If a mutation was requested, give Worker the exact owned surfaces and
desired outcome, then re-read changed files and run the nearest real
project-local validation. Report any activation or human action the tools cannot
perform.

Create and maintain only the current Teamwork document format. Do not add old
format readers, compatibility shims, dual-write behavior, or partial conversion
inside Init. If existing Teamwork documents require a version conversion, leave
them unchanged and route the exact project root to Update; do not treat Init as
a migration fallback.

Init never installs or refreshes global skills, agents, policies, plugins,
notifications, managed dependencies, credentials, or host settings. Route those
Teamwork-owned global surfaces to Update.

## Live Document

When Writer is used, include the project root, inspected surfaces, findings,
ownership, changes, validation, conflicts, document-format state, and remaining
actions. Writer must not invent project facts or report unapplied changes as
complete.
