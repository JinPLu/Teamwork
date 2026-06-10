---
name: teamwork-update
description: Use when updating Teamwork package version, installed skills/agents/global policy, release metadata, or skill topology.
---

# Teamwork Update

Use this stage for end-user package refresh and Teamwork package maintenance:
versioned behavior, installed surfaces, release metadata, or update notes.

## Version Source

- VERSION is the package version source of truth.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` use the same
  version.
- Skill frontmatter must stay limited to `name` and `description`; do not add
  per-skill version metadata there.
- Use semantic versioning:
  - patch: docs, wording, validation, or installer fixes with no behavior
    contract change;
  - minor: new skills, changed routing behavior, new package capabilities, or
    compatible workflow policy changes;
  - major: incompatible install surface, artifact contract, or user workflow
    changes.

## Dependency Surface

- Treat "update Teamwork" as refreshing every Teamwork-controlled dependency
  surface, not metadata only.
- Default: `./install.sh all` for Codex/Cursor/Claude skills, Codex/Claude
  agents, and Codex global policy.
- Run `./install.sh project` when a checkout uses project-local discovery.
- For publication work, verify GitHub remote and existing tag/release state
  before pushing artifacts; missing remote, credentials, or approval blocks.

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
5. Update README/CODEX/CURSOR/CLAUDE/AGENTS only for user-visible changes; keep
   skill prose concise and shared policy in references.
6. Check `SKILL.md` line/word budgets, then run `./scripts/validate.sh`.
7. Run `./install.sh all` by default after validation; add `./install.sh project`
   for project-local installs or an individual target only when the user asked
   for a narrow refresh.
8. For release/public-version work, check branch sync, GitHub remote, and
    tag/release state; create or push release artifacts only when explicitly in
    scope.
9. Include `Memory Delta:` only when durable project memory was checked/changed.

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
- ./install.sh all: <result or not run because ...>
- ./install.sh project: <result or not run because ...>
- GitHub remote / tag/release: <checked | skipped because ...>
```
