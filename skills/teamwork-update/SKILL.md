---
name: teamwork-update
description: Use when updating Teamwork package version, refreshing installed skills/agents/global policy, checking install freshness, or release metadata.
---

# Teamwork Update

Use for package refresh and maintenance. Read
`skills/using-teamwork/references/check-update.md`, `workflow-contract.md`, and
`eval-gate.md`.

## Modes

- **User refresh** — run `check-update.sh`; report drift and pull only with
  repository-update authority. Always run `install.sh all --profile <profile>`
  (notifications default; honor `--no-notifications`), refresh stale project
  surfaces, copy Cursor policy, and recheck. Restart after routing changes.
  Native interaction tools are never enabled by Teamwork. Never edit release metadata.
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
4. Run `install.sh all`, applicable project install, then `check-update.sh`;
   record expected pre-publication drift. For `review-required`, when authorized
   and interactive, verify the command in `/hooks` and individually trust only
   `Stop` and `PermissionRequest`—never trust-all; otherwise report the action.
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
