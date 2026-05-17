# README Skills Research

## Research Question

How should `README.md` be reorganized so it clearly explains the current Teamwork skill set without losing platform, artifact, and runtime constraints?

## Local Evidence

- observed `skills/`: the active skill set contains exactly seven skills: `using-teamwork`, `teamwork`, `teamwork-goal`, `teamwork-research`, `teamwork-plan`, `teamwork-execute`, and `teamwork-review`.
- observed `skills/using-teamwork/SKILL.md`: the normal entrypoint decides whether native flow is enough or whether a narrower Teamwork stage should run.
- observed `skills/teamwork/SKILL.md`: the router defines activation tiers, evidence rules, subagent roles, model tiers, Codex dispatch mapping, and durable plan artifact rules.
- observed `skills/teamwork-research/SKILL.md`: non-trivial research writes artifacts under `docs/teamwork/research/YYYY-MM-DD-<slug>.md` before planning.
- observed `skills/teamwork-plan/SKILL.md`: planning uses the lightest sufficient tier; durable plans live under `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- observed `skills/teamwork-execute/SKILL.md`: execution requires an accepted plan, bounded edits, and focused verification.
- observed `skills/teamwork-review/SKILL.md`: review has explicit `mode: plan` and `mode: execution` rubrics.
- observed `skills/teamwork-goal/SKILL.md`: autonomous goal mode is stricter and requires durable plan anchoring, checkpoint evidence, and completion audit.
- observed `install.sh`: installs the same seven skills for Claude Code and Codex, installs a thin Cursor rule, and supports `--copy` or `--link`.
- observed `commands/teamwork/help.md`: Claude runtime exposes `/teamwork:*`, keeps `/rao:*` as compatibility aliases, and stores state under `.claude/teamwork-goals/`.
- observed `scripts/validate.sh`: README must continue documenting `/teamwork:goal`, `/rao:goal`, Stop hook behavior, `.claude/teamwork-goals`, `RAO_GOAL_COMPLETE`, `<completion_audit>`, `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`, Codex runtime, and concise conceptual Codex dispatch guidance.
- observed `README.md`: the current README contains the right material, but mixes quick start, workflow theory, runtime internals, and completion audit details before first giving readers a compact map of the seven skills.

## External Evidence

Not needed. The requested update depends on repository-local skill and runtime contracts.

## Options

1. Light edit only: keep the current structure and trim wording. Low risk, but does not solve the user's stated problem that README misses the main point.
2. Full rewrite around current skills: make the first half explain when Teamwork activates and which skill owns each stage; move platform/runtime details later. Best fit for the request, with manageable validation risk.
3. Split README into multiple docs: shortest README plus separate runtime docs. Cleaner long-term, but broader than requested and would require updating validation/docs links.

## Recommendation

Use option 2. It directly addresses readability while staying within `README.md` and preserving required runtime details.

## Dissent / Unresolved

- warning: README validation has exact grep requirements, so the rewrite must retain key phrases even if prose is simplified.
- warning: avoid duplicating full skill bodies; README should point to `skills/*/SKILL.md` for authoritative behavior.

## Refresh Triggers

- Rerun research if `scripts/validate.sh` fails on README expectations.
- Rerun research if README changes expose a mismatch with any skill body or command file.
