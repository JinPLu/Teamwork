---
name: teamwork-update
description: Use when updating Teamwork package version, installed skills/agents/global policy, release metadata, or skill topology.
---

# Teamwork Update

Use for package refresh and maintenance: versioned behavior, installed surfaces,
release metadata, or update notes. Read
`skills/using-teamwork/references/workflow-contract.md` for evidence and
judgment.

## Version Source

- `VERSION` is the package version source of truth.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` use the same
  version.
- Skill frontmatter stays limited to `name` and `description`.
- Semantic versioning:
  - patch: docs, wording, validation, or installer fixes with no behavior change;
  - minor: new skills, changed routing, or compatible workflow policy changes;
  - major: incompatible install surface, artifact contract, or workflow changes.

## Dependency Surface

- Treat "update Teamwork" as refreshing every Teamwork-controlled surface, not
  metadata only.
- Default: `./install.sh all` for Codex/Cursor/Claude skills, Codex/Claude
  agents, and Codex global policy. Add `./install.sh project` for project-local
  installs.
- For release work, verify GitHub remote and tag/release state before pushing;
  missing remote, credentials, or approval blocks.

## Workflow

1. Inspect `VERSION`, both `plugin.json`, `install.sh`, `scripts/validate.sh`,
   README files, and affected `skills/*/SKILL.md`.
2. Choose the smallest justified semver bump and record why.
3. Update `VERSION` and both `plugin.json` together.
4. Update README/CODEX/CURSOR/CLAUDE/AGENTS only for user-visible changes; keep
   shared policy in references.
5. Check SKILL line/word budgets, then run `./scripts/validate.sh`.
6. Run `./install.sh all` after validation; add `./install.sh project` for
   project-local installs.
7. Include `Memory Delta:` only when durable project memory was checked or
   changed.

## Checklist

```text
Current Version: <VERSION and plugin version>
Selected Bump: <patch | minor | major> because <reason>
Changed Surface: skills | installer | validation | docs
Verification:
- ./scripts/validate.sh: <result>
- ./install.sh all: <result or not run because ...>
```
