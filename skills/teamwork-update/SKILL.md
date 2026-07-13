---
name: teamwork-update
description: Use when updating Teamwork package version, refreshing installed skills/agents/global policy, checking install freshness, or release metadata.
---

# Teamwork Update

Use for package refresh and maintenance. Read
`skills/using-teamwork/references/check-update.md`, `workflow-contract.md`, and
`eval-gate.md`.

## Modes

- **User refresh** — run `./scripts/check-update.sh --project "<path>"`; report
  upstream drift, pull only with repository-update authority, install stale
  global/project surfaces with the checkout profile, copy Cursor policy when
  needed, then recheck. Restart Codex after routing changes. Native interaction
  tools are runtime capabilities and are never enabled by Teamwork. Do not edit
  `VERSION`, manifests, or changelogs.
- **Maintainer release** — change Teamwork itself using the release unit below.

## Release Unit

`VERSION` is the source of truth. One release unit contains `VERSION`, both
plugin manifests, both changelogs, required user docs, verification, release
commit, `v<VERSION>` tag, GitHub Release, and installed-surface freshness.
Until the tag and GitHub Release exist, report `release-ready`, not `released`.

Use the smallest justified semver bump: patch for non-behavioral fixes, minor
for compatible workflow/routing features, and major for incompatible public
contracts without a migration. Skill frontmatter remains `name` and
`description` only.

## Maintainer Workflow

1. Inspect the affected skills, scripts, docs, `VERSION`, manifests, changelogs,
   remote, and current tag/Release state; choose and justify the bump.
2. Update `VERSION`, both manifests, and both changelogs together. Update public
   docs only for user-visible changes.
3. Run relevant dev eval, `./scripts/validate.sh`, non-empty release eval, and
   fresh release review. Apply the stronger ledger/trajectory gates only to
   SkillOpt-Lite or HarnessOpt-Lite claims.
4. Run `./install.sh all`, project install when applicable, then
   `./scripts/check-update.sh`; pre-publication tag/Release drift is expected and
   must be recorded.
5. Stay on the current branch unless the user requests a branch/PR, protection
   requires one, or the user accepts isolation. The default branch alone never
   justifies an `agent/*` branch.
6. Verify remote, credentials, target commit, tag, and Release state. With
   explicit publication authority, push the accepted commit, create and push
   `v<VERSION>`, and create the GitHub Release for that tag.
7. Rerun `check-update.sh`; source, installs, remote tag, and GitHub Release must
   all be current. Missing authority or access stops at `release-ready`.

Treat "update Teamwork" as refreshing every Teamwork-controlled surface, not
metadata only. Project package managers and non-Teamwork MCP plugins are out
of scope unless the user asks explicitly.

## Checklist

```text
Mode: <user refresh | maintainer release>
Version / Bump / Reason: <current -> selected because ...>
Release Unit: <metadata + changelogs + docs current | failed>
Verification: <dev eval; validate; release eval; review; install; check-update>
Publication: <branch; commit; tag; GitHub Release; released | release-ready>
Ledger: <evidence or not_applicable because ...>
```
