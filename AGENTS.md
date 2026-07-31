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
- Normal workflow memory uses only v2 case bundles. Legacy-v1 records are
  migration inputs, never runtime routes. Migration requires an exact authorized project root and transaction readback; install/update alone never implies project migration.

## Commands

- Run `./scripts/validate.sh` for behavior, installation, manifest, topology,
  artifact-policy, or platform-mapping changes.
- Use `./scripts/check-update.sh --readiness` for global-install freshness and
  `./install.sh --help` for install targets. `init-project` changes only project
  context; `teamwork-update` changes only global installs.

## Releases

- Teamwork changes release on `main` unless the user requests a branch or pull
  request, or repository protection requires one. `VERSION` is canonical.
- One release unit includes VERSION, manifests, bilingual changelogs, needed
  public docs, verification, commit, `v<VERSION>` tag, GitHub Release, install
  refresh, and applicable project initialization. Until tag and GitHub Release
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

- Project label: `Teamwork`.
- Read `docs/teamwork/index.json` first before choosing Teamwork memory routes.
- Workflow writes are case-v2 only; legacy-v1 and old collaboration modes are migration inputs, not runtime routes.
- Collaborate checkpoints use the selected v2 case manifest and `live/collaborate.md`; decisions use `decision.md`; route through `case-inspect`, `case-schema`, and `case-apply`, never ordinary memory, legacy records, or reports.
- Durable memory follows the relevant case manifest. Volatile progress stays in its actual artifact.
- CodeGraph: this project has a local `.codegraph/` index.
<!-- TEAMWORK_PROJECT_END -->
