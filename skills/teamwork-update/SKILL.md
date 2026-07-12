---
name: teamwork-update
description: Use when updating Teamwork package version, refreshing installed skills/agents/global policy, checking install freshness, or release metadata.
---

# Teamwork Update

Use for package refresh and maintenance. Read `skills/using-teamwork/references/check-update.md`, `workflow-contract.md`, and `eval-gate.md`.

## Modes

Pick from user intent:

- **User refresh** — run `./scripts/check-update.sh --project "<path>"`; pull
  when upstream is newer; run `./install.sh all` with the checkout profile
  unless explicitly overridden; add `./install.sh --project-root "<path>"
  project` for stale project rows; run `./install.sh cursor-policy-copy` when
  needed; re-run check-update. The user-level Codex install migrates custom-agent
  routing with a 9-thread limit (eight subagents); restart Codex when it reports
  a config update.
  Do not bump `VERSION` or edit plugin manifests.
- **Maintainer release** — change Teamwork itself (below).

## Version Source

- `VERSION` is the package version source of truth; both plugin manifests use it.
- Skill frontmatter stays limited to `name` and `description`.
- Semantic versioning:
  - patch: docs, wording, validation, or installer fixes with no behavior change;
  - minor: new skills, changed routing, or compatible workflow policy changes;
  - major: incompatible install surface, artifact/eval contract, or workflow
    change without an explicit migration.

## Maintainer Workflow

1. Inspect `VERSION`, plugin manifests, install/validation/check-update scripts,
   README files, and affected skills.
2. Choose the smallest justified semver bump and record why.
3. Update `VERSION` and both `plugin.json` together.
4. Update README/CODEX/CURSOR/CLAUDE/AGENTS only for user-visible changes.
5. For behavior, harness, interaction-skill, or release-gate changes, run `python3 scripts/eval-teamwork.py --split dev`; route unclear failures to Debug and cite accepted/rejected ledger deltas.
6. Run `./scripts/validate.sh`, then `./install.sh all`; add `./install.sh --project-root "<project-root>" project` for project-local installs.
7. Before release/version claims, run `python3 scripts/eval-teamwork.py --split release`; the split must be non-empty.
8. For SkillOpt-Lite/HarnessOpt-Lite participation claims, require trajectory samples, same-case baseline/treatment, explicit model/config or offline mode, gate decision, rollback, ledger, fresh review, and release split as audit-only; harness mutation additionally needs allowlist plus smoke and full dev gates.
9. Run `./scripts/check-update.sh` and confirm installed surfaces and Codex
   routing match `VERSION`.
10. For release, verify GitHub remote and tag/release state before pushing;
   missing remote, credentials, or approval blocks.

Treat "update Teamwork" as refreshing every Teamwork-controlled surface, not
metadata only. Project package managers and non-Teamwork MCP plugins are out
of scope unless the user asks explicitly.

## Checklist

```text
Mode: <user refresh | maintainer release>
Current Version: <VERSION and plugin version>
Selected Bump: <patch | minor | major | n/a> because <reason>
Changed Surface: skills | installer | validation | docs | check-update
Verification:
- python3 scripts/eval-teamwork.py --split dev: <result or not_applicable because ...>
- ./scripts/validate.sh: <result>
- python3 scripts/eval-teamwork.py --split release: <non-empty result or not_applicable because ...>
- ./scripts/check-update.sh: <result>
- ./install.sh all: <result or not run because ...>
Ledger Evidence: <accepted/rejected deltas or not_applicable because ...>
```
