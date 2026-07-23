---
name: teamwork-update
description: Use when the user asks to check, install, activate, repair, or refresh globally installed Teamwork skills, agents, managed policy, routing, or notifications; do not use for project-local instructions, memory, CodeGraph context, source release publication, or unrelated plugins and tools.
---

# Teamwork Update

Check or refresh Teamwork-managed global installation surfaces only. Never rewrite
project context as part of an update.

## Resolve The Package

Do not assume the current directory is a Teamwork checkout. From Marketplace,
resolve the package root with package-owned `scripts/plugin-runtime-root.py`, two
levels above this skill, then use that root's `scripts/check-update.sh` and
`install.sh`. From a checkout, use the verified repo root. If
`plugin-runtime-root.py` is missing, also check `$TEAMWORK_ROOT` or
`~/.cursor/.teamwork-mcp.json`; otherwise report missing source instead of
searching or modifying arbitrary directories.

## Check Or Refresh

1. Dispatch Explorer to run resolved `scripts/check-update.sh --plugin` for
   Marketplace, or `scripts/check-update.sh` for a checkout. Freshness checks are
   read-only and stop after an evidence-backed status report.
2. For explicit install, activate, repair, or update, explain managed global
   surfaces and preserve detected profile/notification choice. Follow the
   checker's safe command; do not invent profile or destination.
3. First activation that would add global agents, policy, routing, or
   notifications requires explicit effect authority. An explicit request to
   perform that activation supplies it; a request merely asking what is stale
   does not.
4. Dispatch Worker only for transferable, precisely owned refresh actions.
   Credentials, host UI, trust, notification approval, and privileged surfaces
   remain with Root and require exact effect authority. Refresh only verified
   Teamwork-owned files. Preserve unrelated/unknown files. If cleanup cannot
   distinguish owned files from user content, stop and name the conflict.
5. Dispatch Explorer to rerun the same checker with `--readiness` after changes; pass both `--plugin`
   and `--readiness` for Marketplace. Static file freshness is not proof of live
   host activation; report required restart, policy paste, notification review,
   or other human action separately.

A check-only Update remains read-only and conversational. After a mutating Update
in an initialized writable project, a receipt defaults through Writer unless the
user says `no files`, `off-record`, `read-only`, `no writes`, or equivalent.
Update returns a bounded receipt packet: purpose/audience, facts/sources, frozen
decision/status, style/structure, artifact kind/consumer, preserve/forbid,
managed surfaces, freshness evidence, validation, and manual actions. Writer uses
`artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply`;
the transaction derives the destination and registers the ordinary index. Missing
project memory, Writer, brief, authority, consumer, or transaction blocks only
persistence: deliver the receipt and report it unsaved/blocked. No Root or Worker
fallback writes it.

For notifications, trust only the specific Teamwork hooks reported by the
package; never enable trust-all. Do not install external dependencies, MCP
servers, paid services, unrelated plugins, or credentials without separate
authority.

This skill does not edit `VERSION`, manifests, changelogs, commits, tags, or
GitHub Releases. It does not pull or publish source without explicit repository
authority. It never runs project initialization or edits project instruction and
memory files. Finish with source and installed versions, profile, each managed
surface's freshness, activation strength, manual actions, and unresolved drift.
