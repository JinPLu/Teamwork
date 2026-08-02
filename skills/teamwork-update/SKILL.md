---
name: teamwork-update
description: Use when the user asks to check, install, activate, repair, or refresh Teamwork's global setup and its declared managed dependencies (CodeGraph and a local GPU Broker companion), including an explicitly authorized migration of Teamwork memory for one exact project root during that refresh; do not use for general project-local instructions, source release publication, or unrelated tools.
---

# Teamwork Update

Check or refresh Teamwork-managed global installation surfaces and its optional
managed runtime capabilities. A mutating update always owns the Teamwork baseline:
skills, agents, routing, policy, notifications, Cursor compatibility surfaces,
and verification. Pinned CodeGraph and the local GPU Broker companion are
independently enabled full-capability choices. It is global only: do not
perform project initialization, edit general project context, update drivers,
CUDA, package managers, arbitrary plugins/tools, or publish source. One
explicitly authorized exact-root memory migration may run through the package
transaction. Role order is Explorer check, then Worker for owned refresh actions.
Unavailable mandatory roles or unverified isolation are `capability-blocked`;
Root must not perform a named-method fallback.

## Resolve Source

Do not assume the current directory is a Teamwork checkout. From Marketplace,
resolve the package root with `scripts/plugin-runtime-root.py`, two levels above
this skill, then use that root's `scripts/check-update.sh` and `install.sh`. From
a checkout, use the verified repo root. If
`plugin-runtime-root.py` is missing, check `$TEAMWORK_ROOT` or
`~/.cursor/.teamwork-mcp.json`; otherwise report missing source.

## Check Or Refresh

1. Explorer runs resolved `scripts/check-update.sh --plugin` for Marketplace or
   `scripts/check-update.sh` for checkout, plus
   `python3 scripts/install/preferences.py status --field json`. Check-only is
   read-only and reports baseline readiness, full-capability readiness, desired
   preferences, observed CodeGraph/GPU Broker state, and any invalid receipt.
2. On first activation or a missing preference receipt, Root asks one bounded
   batch of three independent choices: `performance-first|cost-first`, managed
   CodeGraph `enabled|disabled`, and managed GPU Broker `enabled|disabled`.
   Recommend the performance profile plus both capabilities for the full
   experience; explain that the baseline remains complete when either optional
   capability is disabled. On later updates, show and inherit all valid recorded
   choices without asking again. Re-ask only for explicit reconfiguration, an
   invalid/missing preference, or a newly introduced undecided managed
   capability. An invalid or unowned receipt is never overwritten: stop for an
   exact repair decision before mutation. These enumerated preferences are exact
   missing required values, not an open-ended intent interview. A broader rollout,
   compatibility, or effect tradeoff is reclassified to Collaborate instead.
3. For an explicit update/install/repair request, show the compact execution
   summary and run `install.sh update --profile <choice>` with one of
   `--managed-codegraph|--no-managed-codegraph` and one of
   `--managed-gpu-broker|--no-managed-gpu-broker`. The shell command never
   prompts. It records the choices, completes the mandatory baseline, and
   independently preflights and refreshes only enabled capabilities before
   downstream global writes. The local GPU companion source comes from
   `TEAMWORK_GPU_BROKER_SOURCE`, the checkout sibling `../gpu-broker`, or its
   existing uv receipt; a missing source fails closed instead of guessing a
   download location.
4. First activation adding global agents, policy, routing, notifications, or
   managed dependencies
   requires explicit effect authority. Root alone asks once for one exact missing
   mutation value or manual action, then resumes the same Update workflow.
   Discoverable state and inherited valid preferences do not trigger a question;
   Explorer and Worker never ask. Answers do not expand authority.
5. Worker handles only transferable Teamwork-owned refresh files. Credentials,
   host UI, trust, notification approval, privileged surfaces, and repository
   effects remain with Root and need exact authority. Preserve unknown/user
   files; stop if ownership is unclear.
6. Explorer reruns the same checker with `--readiness`; use both `--plugin` and
   `--readiness` for Marketplace. Require `BASELINE_READY=yes`. Claim the full
   experience only when `FULL_CAPABILITY_READY=yes`; an intentional opt-out is
   reported as such, not as a missing baseline. Static freshness is not live
   host activation: report restart, policy paste, notification review, or other
   manual action.

For notifications, trust only package-reported Teamwork hooks; never enable
trust-all. CodeGraph is pinned to the package-declared release. GPU Broker is
installed only from the resolved local companion and verified through its daemon
and local health endpoints. `--no-dependencies` is an explicit opt-out, never
the default. Do not update Node/npm/uv themselves, install paid services,
unrelated plugins, credentials, drivers, CUDA, or remote workloads. This skill does not edit
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
