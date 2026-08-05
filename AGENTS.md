# Teamwork Repository

`skills/` is source of truth for Codex/Cursor/Claude. Native work handles local
inspection and authorized implementation; skills stay self-contained: no router,
generic Execute skill, cross-skill behavior load, or shared behavior reference.

## Working Conventions

- Change the owning `SKILL.md` before workflow behavior; keep canonical and
  generated plugin surfaces synchronized. Public docs stay outcome-focused.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and arrays;
  every `SKILL.md` frontmatter has only `name` and `description`, whose value
  starts with `Use when`.
- Writer maintains one live document per task. Skills declare semantic content;
  storage locking, migration, integrity, and recovery remain implementation details.
  Older records are explicit migration inputs, never runtime read routes. Given
  an exact project root, Update migrates every Teamwork document before normal
  work resumes.
- Teamwork 7.0.0 is not backward compatible with older settings or data. Update
  is the only old-to-new migration route; after migration, only the new format
  is available to normal readers and writers.

## Commands

- Run `./scripts/validate.sh` for behavior, installation, manifest, topology,
  artifact-policy, or platform-mapping changes.
- Use `./scripts/check-update.sh --readiness` for global-install freshness and
  `./install.sh --help` for install targets. `init-project` creates current
  project context; `teamwork-update` refreshes global installs and migrates an
  exactly named project's Teamwork documents.

## Releases

- Teamwork changes release on `main` unless the user requests a branch or pull
  request, or repository protection requires one. `VERSION` is canonical.
- One release unit includes VERSION, manifests, bilingual changelogs, needed
  public docs, verification, commit, `v<VERSION>` tag, GitHub Release, install
  refresh, and applicable exact-root project migration. Until tag and GitHub Release
  both exist, say `release-ready`, not released.
- Write changelogs for users. Every release uses the 4.2/4.3-style: one short, natural summary sentence
  and one to four concise bold-led points; substantive releases normally use four.
  Add Upgrade action and Important limit only when they change required user action
  or expectation.
- Lead with the user outcome. Omit maintainer-only details such as internal scripts,
  numeric thresholds, and test counts unless they change required action or compatibility.

## CodeGraph
- Use CodeGraph for structural questions when callable/fresh; use `rg`/direct
  reads for literals or stale files. Ask before initializing a missing index.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label (local routing only): `Teamwork`.
- Read `docs/teamwork/index.json` first before choosing Teamwork memory routes.
- Writer maintains one live document at `docs/teamwork/cases/<case_id>/live.md` for each task that produces reusable content.
- Create the live document when reusable content first appears, update it only for material evidence, decision, conclusion, or next-step changes, and finalize it when the task ends.
- Legacy-v1 memory and case manifests without a live document are migration-only inputs for Update; Init reads them only to fail closed and never migrates them.
- CodeGraph: this project has a local `.codegraph/` index.
<!-- TEAMWORK_PROJECT_END -->
