# Teamwork Repository

`skills/` is the behavior source of truth for this Codex, Cursor, and Claude
Code skill package. Native work handles clear local inspection and authorized
implementation; skills are self-contained and must not restore a router,
generic Execute skill, cross-skill behavior load, or shared behavior reference.

## Working Conventions

- Use Explore for a bounded local-evidence question, Research for external or
  current evidence, Debug for an unknown cause, Design for an unsettled choice,
  Plan for a selected direction, Review for independent acceptance, Goal for
  explicit persistence, Init for one project, and Update for global refreshes.
- Change the owning `SKILL.md` before changing workflow behavior. Keep public
  docs outcome-focused and use direct evidence from code, logs, tests, diffs,
  and artifacts.
- Change the canonical owner, reuse existing patterns, write the smallest
  complete logic, and verify the real changed path in proportion to risk.
  Each Worker self-verifies its slice. Independent Plan or code Review runs only
  on user request or a named material risk gate; code Review targets the sealed
  integrated candidate once, combines findings into one repair batch, and allows
  at most one delta recheck per candidate.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and arrays;
  every `SKILL.md` frontmatter has only `name` and `description`, whose value
  starts with `Use when`.

## Commands

- Run `./scripts/validate.sh` for repository changes that affect behavior,
  installation, manifests, topology, artifact policy, or platform mapping.
- Use `./scripts/check-update.sh --readiness` for global-install freshness and
  `./install.sh --help` for installation targets. `init-project` changes only
  project context; `teamwork-update` changes only global installations.

## Releases and Changelog

- Teamwork changes release on `main` unless the user requests a branch or pull
  request, or repository protection requires one. `VERSION` is canonical.
- One release unit includes the version, manifests, bilingual changelogs,
  necessary public docs, verification, commit, `v<VERSION>` tag, GitHub Release,
  installation refresh, and applicable project initialization. Use patch for
  fixes, minor for compatible features, and major for incompatible contracts.
- Until both the tag and GitHub Release exist, call the result `release-ready`,
  not released. A generic PR flow does not replace the release unit.
- Write changelogs for users, not maintainers. A substantive release starts with
  one short, natural summary sentence followed by concise points with one central
  user-visible detail each; small changes may use the summary alone.
- Do not force Before → After wording, upgrade/no-action boilerplate, or a limit
  section. Include an action, boundary, or limitation only when it changes what
  users must do or expect. Keep Chinese and English natural and equivalent.

## CodeGraph
- Use CodeGraph for structural questions when it is callable and fresh; use
  `rg`/direct reads for literal text or files flagged as stale. If no index
  exists, ask before initializing one.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label (local routing only): `Teamwork`.
- For saved, resumed, or independently major Grill discussion, use only `docs/teamwork/discussion/current.md`; never mirror it into ordinary memory.
- For ordinary durable memory, read `docs/teamwork/index.json` first, then `docs/teamwork/README.md`; keep volatile progress in its actual artifact.
- CodeGraph: this project has a local `.codegraph/` index.
<!-- TEAMWORK_PROJECT_END -->
