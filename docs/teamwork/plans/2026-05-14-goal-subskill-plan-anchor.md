# Goal Subskill Plan Anchor Refactor

## Goal

Split autonomous goal control into a dedicated `teamwork-goal` subskill and
anchor every goal iteration to a durable Markdown plan artifact so continuation,
execution, review, and completion audit use the same plan.

## Requirements Mapping

- Goal routing is intuitive: verify `using-teamwork` and `teamwork` route
  autonomous convergence to `teamwork-goal`.
- Goal instructions have a single source: verify `skills/teamwork-goal/SKILL.md`
  owns the autonomous loop, budget, stop rules, and completion audit format.
- Execution cannot drift from chat context: verify `teamwork-execute` requires
  a readable durable plan artifact before any Worker pass.
- Runtime continuation is anchored: verify `bin/raoctl.py` stores and reports
  `active_plan_artifact`, injects it in continuation prompts, and validates it
  in completion audits.
- Claude command surface is clearer: verify `/teamwork:*` commands exist while
  `/rao:*` remains compatible.
- Regression coverage exists: verify `./scripts/validate.sh` covers topology,
  plan anchor runtime behavior, and completion audit gating.

## Evidence Read

- `skills/teamwork/SKILL.md` currently owns `mode: goal` and says not to create a
  separate goal subskill.
- `skills/teamwork-execute/SKILL.md` requires an accepted plan but not a readable
  durable plan artifact path.
- `bin/raoctl.py` stores Markdown goal state but has no active plan artifact
  metadata or `plan` command.
- `commands/rao/goal.md` tells Claude to use `teamwork` with `mode: goal`.
- `scripts/validate.sh` currently expects exactly five skills and requires the
  router to own `mode: goal`.

## Scope

- In scope: Teamwork skill topology, goal runtime state, Claude commands,
  validation, and short user-facing docs.
- Out of scope: renaming `bin/raoctl.py`, moving `.claude/teamwork-goals/`,
  changing Codex native goal APIs, or splitting plan/execution review subskills.
- Sacred boundaries: keep runtime standard-library only and preserve `/rao:*`
  compatibility.

## Implementation Steps

- [x] Add validation expectations for `teamwork-goal`, `/teamwork:*` commands,
  plan artifact audit tags, and runtime plan-anchor smoke checks.
- [x] Add `skills/teamwork-goal/SKILL.md` with autonomous loop, plan-anchor,
  budget, stop, Codex/Claude runtime, and completion audit rules.
- [x] Update `skills/teamwork/SKILL.md` and `skills/using-teamwork/SKILL.md` so
  goal requests route to `teamwork-goal`; keep shared routing policy in the
  router.
- [x] Update `skills/teamwork-execute/SKILL.md` so execution requires a readable
  durable plan artifact and Worker handoffs carry that path.
- [x] Extend `bin/raoctl.py` with `active_plan_artifact`, `plan <path>`, status
  output, `/teamwork:` command suppression, continuation prompt anchoring, and
  completion audit plan matching.
- [x] Add `commands/teamwork/*.md`; update `commands/rao/*.md` wording to
  compatibility and `teamwork-goal`.
- [x] Update `install.sh`, `.claude-plugin/plugin.json`, README, CODEX, CLAUDE,
  CURSOR, and `.cursor/rules/teamwork.mdc`.

## Execution Status

Executed in the working tree before the runtime-hardening pass on
2026-05-14. The later hardening pass strengthens the basic plan-anchor runtime
with plan SHA-256, checkpoint, verification, and no-progress gates.

## Verification

- Focused red check: run `./scripts/validate.sh` after adding validation
  assertions and before implementation; it should fail on the missing
  `teamwork-goal` topology or runtime behavior.
- Focused green check: run `./scripts/validate.sh` after implementation.
- Expected results: validation passes; runtime smoke checks reject completion
  audits without matching `<plan_artifact>` and accept audited completion with
  a matching active plan artifact.

## Risks

- Command duplication can drift; mitigate by keeping `/rao:*` command files
  thin compatibility wrappers with the same runtime controller.
- Completion audit format becomes stricter; mitigate by documenting
  `<plan_artifact>` in `teamwork-goal`, README, and validation.
- Router and goal subskill can diverge; mitigate by keeping goal loop details
  out of `teamwork` and validating route references.

## Stop Rules

- Stop if validation requires a runtime behavior that conflicts with existing
  `/rao:*` compatibility.
- Stop if plan artifact validation would require tracking generated or
  project-local runtime state.
- Stop if a broader command rename becomes necessary.

## Worker Handoff

Execute only the steps above. Keep edits minimal and preserve `/rao:*`,
`bin/raoctl.py`, and `.claude/teamwork-goals/` compatibility.

## Review Handoff

Check topology, routing, command compatibility, runtime state migration,
completion audit gates, validation coverage, and unintended doc duplication.

## Subagent Routing

- Explorer: skipped | scope: already inspected relevant source | tier: fast |
  context: local evidence | order: n/a | why: evidence is compact.
- Designer: skipped | scope: direction selected by user | tier: high reasoning |
  context: accepted plan | order: n/a | why: design was completed in planning.
- Judge: main distinct pass | scope: plan review | tier: high reasoning |
  context: local plan and source | order: serial before execution | why:
  separate subagents are not available under current tool policy.
- Worker: main agent | scope: listed files only | tier: standard | context:
  durable plan artifact | order: serial | why: changes are coupled.
- Reviewer: main distinct pass | scope: diff, validation, runtime smoke |
  tier: high reasoning | context: fresh local pass | order: after verification |
  why: required before completion.
