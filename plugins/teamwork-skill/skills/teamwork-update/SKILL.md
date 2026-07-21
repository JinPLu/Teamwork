---
name: teamwork-update
description: Use when the user asks to check, install, activate, repair, or refresh globally installed Teamwork skills, agents, managed policy, routing, or notifications; do not use for project-local instructions, memory, CodeGraph context, source release publication, or unrelated plugins and tools.
---

# Teamwork Update

Check or refresh Teamwork-managed global installation surfaces only. Never rewrite
project context as part of an update.

## Resolve The Package

Do not assume the current working directory is a Teamwork checkout. From a loaded
Marketplace package, resolve its package root with the package-owned
`scripts/plugin-runtime-root.py`, located two levels above this skill directory,
then use that root's `scripts/check-update.sh` and `install.sh`. From a checkout,
use the verified repository root. If `plugin-runtime-root.py` is not at the expected
relative path, also check `$TEAMWORK_ROOT` or `~/.cursor/.teamwork-mcp.json` for
the package root before reporting missing source. If neither package root can be
resolved, report the missing source instead of searching or modifying arbitrary user
directories.

## Check Or Refresh

1. Dispatch Explorer to run the resolved `scripts/check-update.sh --plugin` for a Marketplace package,
   or `scripts/check-update.sh` for a checkout. A request to check freshness is
   read-only and stops after an evidence-backed status report.
2. For an explicit install, activate, repair, or update request, explain the
   managed global surfaces and preserve the detected install profile and
   notification choice. Follow the checker's reported safe command rather than
   inventing a profile or destination.
3. First activation that would add global agents, policy, routing, or
   notifications requires explicit effect authority. An explicit request to
   perform that activation supplies it; a request merely asking what is stale
   does not.
4. Dispatch Worker only for transferable, precisely owned refresh actions.
   User-global credentials, host UI, trust, notification approval, and other
   privileged surfaces remain with Root and require exact effect authority.
   Refresh only verified Teamwork-owned files. Preserve unrelated and unknown
   files. If legacy cleanup cannot distinguish an owned file from user content,
   stop before cleanup and name the conflict.
5. Dispatch Explorer to rerun the same checker with `--readiness` after changes; pass both `--plugin`
   and `--readiness` for Marketplace. Static file freshness is not proof of live
   host activation; report required restart, policy paste, notification review,
   or other human action separately.

For notifications, trust only the specific Teamwork hooks reported by the
package; never enable trust-all. Do not install external dependencies, MCP
servers, paid services, unrelated plugins, or credentials without separate
authority.

This skill does not edit `VERSION`, manifests, changelogs, commits, tags, or
GitHub Releases. It does not pull or publish source without explicit repository
authority. It never runs project initialization or edits project instruction and
memory files. Finish with source and installed versions, profile, each managed
surface's freshness, activation strength, manual actions, and unresolved drift.
