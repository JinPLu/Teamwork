# Teamwork Repository

`skills/` is source of truth for Codex. Cursor and Claude Code source adapters
may remain for compatibility and development, but Teamwork 7.2 support and
release qualification are Codex-only. Native work handles local inspection and
authorized implementation; skills stay self-contained: no router, generic
Execute skill, cross-skill behavior load, or shared behavior reference.

## Working Conventions

- Change the owning `SKILL.md` before workflow behavior; keep canonical and
  generated plugin surfaces synchronized. Public docs stay outcome-focused.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and arrays;
  every `SKILL.md` frontmatter has only `name` and `description`, whose value
  starts with `Use when`.
- Writer is the sole semantic writer for Discussion, Research, Debug, Plan,
  Review, and Report documents. Skills declare semantic content; indexing,
  migration mechanics, and recovery remain implementation details. Older
  records are explicit migration inputs, never runtime read routes. Given an
  exact project root, Update migrates every Teamwork document before normal
  work resumes.
- Teamwork-owned source, data formats, protocols, and validation do not use
  hashes, digests, checksums, content fingerprints, or substitute identity and
  sealing schemes. Git object identities, host or third-party internals, and an
  explicit user-domain requirement remain outside this repository rule.
- Teamwork 7.2 keeps no normal-runtime compatibility for older document
  formats. Update is the only old-to-new document migration route; after
  migration, only schema v4 typed documents are available to normal readers
  and writers. Valid Teamwork 7 install preferences remain reusable.

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
  public docs, Codex release evidence, verification, commit, `v<VERSION>` tag,
  GitHub Release, install refresh, and applicable exact-root project migration.
  Cursor/Claude adapter state is not a 7.2 release blocker. Until tag and
  GitHub Release both exist, say `release-ready`, not released.
- Write changelogs from a plain-language release kernel drawn from the authorized
  behavior diff: `before, a user experienced X; now, they experience Y`. Name the
  concrete result, never a policy label, implementation, validation, incident,
  plan, or troubleshooting observation.
- Use that kernel for one short natural summary sentence and one to four concise
  bold-led points. Every point is `trigger → Agent behavior → user result`; do not
  list policy exceptions. Chinese, English, and the GitHub Release use the same kernel.
- Do not package pre-existing installation/readiness behavior, test coverage,
  cache state, scripts, numbers, or a release incident as a new capability. Add
  Upgrade action or Important limit only if this release changes required user
  action or expectation. If implementation exceeds the approved user-visible
  increment, stop and clarify—never enlarge the changelog to justify it.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label (local routing only): `Teamwork`.
- Read `docs/teamwork/index.json` first; schema v4 is the only normal Teamwork document route.
- Writer creates material reusable output under `docs/teamwork/{discussions,research,debug,plans,reviews,reports}/<YYYY-MM-DD>-<semantic-slug>.md` and registers it under one human-readable task key.
- A task may reference several typed documents. Update a document only for a material semantic change and finalize it at its owning stage boundary.
- Same-scope editorial or link corrections may update a final document in place; materially new scope uses a new same-type path and preserves the earlier conclusion.
- Older schemas, `cases/`, manifests, and `live.md` are migration-only inputs for Update; Init reads them only to fail closed and never migrates them.
<!-- TEAMWORK_PROJECT_END -->
