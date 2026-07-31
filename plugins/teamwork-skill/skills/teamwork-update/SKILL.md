---
name: teamwork-update
description: Use when the user asks to check, install, activate, repair, or refresh globally installed Teamwork skills, agents, managed policy, routing, or notifications, including an explicitly authorized migration of Teamwork memory for one exact project root during that refresh; do not use for general project-local instructions, CodeGraph context, source release publication, or unrelated plugins and tools.
---

# Teamwork Update

Check or refresh Teamwork-managed global installation surfaces. Update is global
only: do not perform project initialization, edit general project context, touch
unrelated plugins/tools, or publish source. One explicitly authorized exact-root
memory migration may run through the package transaction. Role order is Explorer
check, then Worker for owned refresh actions. Unavailable mandatory roles or
unverified isolation are `capability-blocked`; Root must not perform a
named-method fallback.

## Resolve Source

Do not assume the current directory is a Teamwork checkout. From Marketplace,
resolve the package root with `scripts/plugin-runtime-root.py`, two levels above
this skill, then use that root's `scripts/check-update.sh` and `install.sh`. From
a checkout, use the verified repo root. If
`plugin-runtime-root.py` is missing, check `$TEAMWORK_ROOT` or
`~/.cursor/.teamwork-mcp.json`; otherwise report missing source.

## Check Or Refresh

1. Explorer runs resolved `scripts/check-update.sh --plugin` for Marketplace or
   `scripts/check-update.sh` for checkout. Check-only is read-only and stops
   after an evidence-backed status report.
2. Explicit install, activate, repair, or update follows only the checker's safe
   command and detected profile/notification choice; invent no profile,
   destination, or owned file.
3. First activation adding global agents, policy, routing, or notifications
   requires explicit effect authority. Root alone asks for missing mutation
   authority or manual action; answers do not expand authority.
4. Worker handles only transferable Teamwork-owned refresh files. Credentials,
   host UI, trust, notification approval, privileged surfaces, and repository
   effects remain with Root and need exact authority. Preserve unknown/user
   files; stop if ownership is unclear.
5. Explorer reruns the same checker with `--readiness`; use both `--plugin` and
   `--readiness` for Marketplace. Static freshness is not live host activation:
   report restart, policy paste, notification review, or other manual action.

For notifications, trust only package-reported Teamwork hooks; never enable
trust-all. Do not install dependencies, MCP servers, paid services, unrelated
plugins, or credentials without separate authority. This skill does not edit
`VERSION`, manifests, changelogs, commits, tags, or GitHub Releases, and does
not pull or publish source without explicit repository authority.

## Migration

Updating or activating Teamwork does not migrate project documents by default.
Existing legacy-v1 project memory is read-only migration input. Update may
migrate only with explicit authority for the current named project or an exact
`--project-root` value; it must not scan for projects or touch both v1 and v2
memory trees. Use package-owned helper commands for that root, for
example `scripts/teamwork-case-migration.py classify --project-root
<exact-project-root>` and `scripts/teamwork-case-migration.py request-inputs
--project-root <exact-project-root>` before cutover. If accepted migration
requires `teamwork-case-migration.py migrate --project-root <exact-project-root>` or `teamwork-case-migration.py resume --project-root <exact-project-root>`
and the helper lacks that phase, stop `capability-blocked`; do not scan or
invent a replacement. Mixed, unknown, stale, ambiguous case, missing
seed/task_key, legacy-v1 without explicit migration authority, or partial
migration fails closed before any write. Fresh initialized projects use case-v2
bundles through project setup; Update does not run that setup.

## Receipt

A mutating Update in an initialized writable project defaults to a case-v2
completion companion unless `no files`, `off-record`, `read-only`, `no writes`,
or equivalent applies. Core update result and persistence are separate: deliver
source/installed status and validation even if the receipt cannot be saved, and
report `unsaved/blocked`. Claim saved/durable only after readback; wait for
Writer only when claiming it or when a dependent next step needs it.

Freeze a receipt packet: purpose/audience, facts/sources, decision/status,
artifact kind/consumer, preserve/forbid, managed surfaces, freshness evidence,
validation, and manual actions. Writer routes from observed
schema: `case-inspect` first; case-v2 uses exact `case_id`/alias or creates from
a frozen seed/task_key, then `case-schema <update-result> -> case-apply ->
case-inspect/readback`. The transaction derives destination and registers
manifest/claim heads. Writer must not invent or alter facts, authority, status,
or validation. Missing project memory, Writer, packet, authority, consumer,
route, or transaction blocks only persistence. No Root or Worker fallback writes
it.

Finish with versions, profile, freshness, activation strength, manual actions,
unresolved drift, migration state, and receipt state.
