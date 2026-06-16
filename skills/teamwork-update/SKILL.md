---
name: teamwork-update
description: Use when updating Teamwork package version, refreshing installed skills/agents/global policy, checking install freshness, or release metadata.
---

# Teamwork Update

Use for package refresh and maintenance. Read
`skills/using-teamwork/references/check-update.md` for the update report script;
`skills/using-teamwork/references/workflow-contract.md` for evidence and
judgment.

## Modes

Pick from user intent:

- **User refresh** — update installed Teamwork on this machine or project.
  Run `./scripts/check-update.sh --project "<path>"`; `git pull` the Teamwork
  checkout when upstream is newer; `./install.sh all --profile <profile>`;
  add `./install.sh project` when project rows are stale; remind about
  `./install.sh cursor-policy` paste; re-run check-update. Do not bump
  `VERSION` or edit plugin manifests.
- **Maintainer release** — change Teamwork itself (below).

## Version Source

- `VERSION` is the package version source of truth.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` use the same
  version.
- Skill frontmatter stays limited to `name` and `description`.
- Semantic versioning:
  - patch: docs, wording, validation, or installer fixes with no behavior change;
  - minor: new skills, changed routing, or compatible workflow policy changes;
  - major: incompatible install surface, artifact contract, or workflow changes.

## Maintainer Workflow

1. Inspect `VERSION`, both `plugin.json`, `install.sh`, `scripts/validate.sh`,
   `scripts/check-update.sh`, README files, and affected `skills/*/SKILL.md`.
2. Choose the smallest justified semver bump and record why.
3. Update `VERSION` and both `plugin.json` together.
4. Update README/CODEX/CURSOR/CLAUDE/AGENTS only for user-visible changes.
5. Run `./scripts/validate.sh`, then `./install.sh all`; add `./install.sh
   project` for project-local installs.
6. Run `./scripts/check-update.sh` and confirm installed surfaces match
   `VERSION`.
7. For release work, verify GitHub remote and tag/release state before pushing;
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
- ./scripts/validate.sh: <result>
- ./scripts/check-update.sh: <result>
- ./install.sh all: <result or not run because ...>
```
