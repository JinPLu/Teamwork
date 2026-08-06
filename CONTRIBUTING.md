# Contributing

Keep Teamwork small, semantic, and generated from canonical owners.

## Change the owner first

- Skill behavior: `skills/<skill>/SKILL.md`
- Complex optional method: that Skill's one-level `references/`
- Agent behavior: `templates/{codex,cursor,claude}-agents/`
- Global policy: `policy/teamwork-global.md`; host transport:
  `scripts/install/policy.sh`
- Mechanical inventory: `config/teamwork-topology.json`
- Typed-document storage and schema mechanics: `templates/teamwork-memory/`,
  `scripts/teamwork_index_v4.py`, Init, and migration helpers; semantic content
  remains in the owning Skill
- Marketplace output: regenerate with `scripts/build-codex-plugin.py`; do not edit it directly

Do not add a public router, generic Execute Skill, shared behavior reference, fixed Skill/Agent/reference count, or model-facing transaction protocol.

## Skill rules

Read the installed Skill Creator before changing a Skill.

- Frontmatter contains only `name` and `description`.
- Description starts with `Use when` and carries all trigger and exclusion guidance.
- Body uses imperative language and includes only non-obvious procedure.
- Prefer progressive disclosure and one-level references.
- Every Skill includes matching `agents/openai.yaml` UI metadata.
- Keep storage and migration mechanics out of model-facing instructions.
- Do not add Teamwork-owned hashes, digests, checksums, content fingerprints,
  opaque identity substitutes, or sealed-evidence protocols.

## Validation

Run focused tests while editing, then:

```bash
./scripts/validate.sh --fast
python3 scripts/build-codex-plugin.py --check
./scripts/validate.sh --full
./scripts/check-update.sh --readiness
git diff --check
```

Static tests are structural evidence, not semantic proof. Changed or reasserted
host behavior needs an installed observation where supported. Semantic claims
need an independent Reviewer to read the actual candidate; do not enforce them
through fixed headings, markers, counts, or report shape.

## Compatibility

Retired names may remain only in scoped cleanup, one-time Update inputs,
negative tests, and historical changelogs. They must not appear as active
Skills, Agents, routes, normal readers, or generated installed surfaces.

Preserve unrelated work. An unrecognized same-named file stays in place and is
reported instead of guessed to be Teamwork-owned. Project migration requires an
exact project root, full source-to-output semantic coverage, bounded rollback,
and independent review before old data is retired.

## Releases

`VERSION` is canonical. A release unit updates manifests, bilingual changelogs, public documentation, generated plugin output, validations, tag, GitHub Release, and any separately authorized install refresh. Until the tag and GitHub Release both exist, call the result `release-ready`, not released.

### Changelog style

Use the 4.2/4.3 shape: one natural summary sentence followed by one to four concise, bold-led points. Small releases do not pad the section. Lead with the user outcome and omit maintainer-internal implementation details, test counts, and thresholds.

Chinese and English changelogs keep the same section order and point count, with equivalent facts. Add an upgrade action or important limit only when it changes what users must do or expect.
