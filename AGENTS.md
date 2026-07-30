# Teamwork Repository

`skills/` is the behavior source of truth for this Codex, Cursor, and Claude
Code skill package. Native work handles clear local inspection and authorized
implementation; skills are self-contained and must not restore a router,
generic Execute skill, cross-skill behavior load, or shared behavior reference.

## Working Conventions

- Use Collaborate for natural dialogue, brainstorming, grill/stress-test, or an
  unsettled consequential choice; Explore for bounded local evidence; Research
  for external/current evidence; Debug for an unknown cause; Plan only after an
  accepted Collaborate handoff; Review for independent acceptance; Goal for
  explicit persistence; Init for one project; and Update for global refreshes.
- Collaborate selects dialogue, brainstorm, or grill from the goal and evidence;
  grill always proceeds global -> boundary -> detail, batches only independent
  material questions, and keeps dependent questions serial.
- Change the owning `SKILL.md` before changing workflow behavior. Keep public
  docs outcome-focused and use direct evidence from code, logs, tests, diffs,
  and artifacts.
- Named Teamwork workflows default-persist reusable artifacts aggressively
  through Writer from frozen bounded packets in initialized writable projects;
  `no files`, off-record, read-only, or no-write requests override. Writer must
  not paraphrase or fill gaps in frozen facts, decisions, authority, status, or
  acceptance, and missing Writer/route/readback fails closed as unsaved.
  Code-coupled wording stays with the implementation owner.
- Persistent memory is schema-first. Existing legacy-v1 project memory keeps its
  current routes until explicit cutover; fresh 5.1 projects use v2 case bundles
  under `docs/teamwork/cases/`. Update/install alone never migrates, rewrites,
  deletes, or cold-archives project documents.
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
- Write changelogs for users, not maintainers. Every release uses the
  4.2/4.3-style shape: one short, natural summary sentence in bold and one to
  four concise bold-led points with one central user-visible detail each; substantive
  releases normally use four. Add `Upgrade action` and `Important limit`
  paragraphs only when they change what users must do or expect.
- Do not force Before → After wording, pad small releases, or add empty
  boilerplate. Keep the Chinese and English version order, point count, facts,
  actions, and limits natural and equivalent.
- Lead with the user outcome. Omit maintainer-only implementation details such
  as source owners, internal scripts, numeric thresholds, test counts, and file
  topology unless they change a required user action or observable compatibility.

## CodeGraph
- Use CodeGraph for structural questions when it is callable and fresh; use
  `rg`/direct reads for literal text or files flagged as stale. If no index
  exists, ask before initializing one.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label (local routing only): `Teamwork`.
- Read `docs/teamwork/index.json` first before choosing Teamwork memory routes.
- For Collaborate dialogue, brainstorm, grill, and accepted-decision checkpoints, legacy-v1 alone uses `docs/teamwork/collaborate/current.md` through `collaborate-inspect`, `collaborate-schema`, and `collaborate-apply`; never mirror them into ordinary memory, legacy Discussion/Design, or a report.
- For ordinary durable memory, read `docs/teamwork/README.md` after the index, then the referenced artifact. Keep volatile progress in its actual artifact.
- CodeGraph: this project has a local `.codegraph/` index.
<!-- TEAMWORK_PROJECT_END -->
