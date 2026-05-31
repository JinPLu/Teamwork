---
name: teamwork-update
description: Use when updating Teamwork package version, release metadata, changelog notes, installer surface, or skill topology.
---

# Teamwork Update

Use this stage for Teamwork package maintenance that changes versioned public
behavior, installed skill surface, release metadata, or update notes.

## Version Source

- VERSION is the package version source of truth.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` must use the
  same version.
- Skill frontmatter must stay limited to `name` and `description`; do not add
  per-skill version metadata there.
- Use semantic versioning:
  - patch: docs, wording, validation, or installer fixes with no behavior
    contract change;
  - minor: new skills, changed routing behavior, new package capabilities, or
    compatible workflow policy changes;
  - major: incompatible install surface, artifact contract, or user workflow
    changes.

## Workflow

1. Inspect `VERSION`, `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`,
   `install.sh`, `scripts/validate.sh`, README files, and affected
   `skills/*/SKILL.md`.
2. If update work depends on durable Teamwork memory, check
   `docs/teamwork/index.json` first when present, then current active state
   pointers before deeper artifact reads.
3. Choose the smallest justified semver bump and record why.
4. Update `VERSION`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`
   together.
5. Update README/CODEX/CURSOR/CLAUDE/AGENTS only for user-visible changes.
6. Keep skill prose concise; move shared policy into references instead of
   repeating it across stage skills.
7. Check `SKILL.md` line/word budgets when editing skills.
8. Run `./scripts/validate.sh`.
9. Run `./install.sh all` when installed local skills, agents, and Codex global
   policy should reflect the package update; use individual targets for narrow
   refreshes and `./install.sh project` in checkouts that rely on project-local
   discovery.
10. Include `Memory Delta:` only when durable project memory was checked or
    changed.

## Update Checklist

```text
Current Version:
- <VERSION and plugin version>

Selected Bump:
- <patch | minor | major> because <reason>

Changed Surface:
- Skills: <added | removed | changed | none>
- Installer: <changed | unchanged>
- Validation: <changed | unchanged>
- Docs: <changed | unchanged>

Verification:
- ./scripts/validate.sh: <result>
- ./install.sh: <result or not run because ...>
```
