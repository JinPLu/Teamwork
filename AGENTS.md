# Teamwork Repository

`skills/` is the source of truth. Clear authorized work stays native; a named
Skill adds only the method described by its trigger. Cursor and Claude Code
adapters are optional compatibility surfaces and never block Codex work.

## Working Conventions

- Change the owning `SKILL.md` before workflow behavior and regenerate the
  plugin bundle after canonical changes. Public docs stay outcome-focused.
- Shell scripts use Bash with `set -euo pipefail`, quoted variables, and arrays;
  every `SKILL.md` frontmatter has only `name` and `description`, whose value
  starts with `Use when`.
- Agent delegation is optional unless the user explicitly requires independent
  work. Handoffs contain only objective, scope, settled constraints, evidence,
  and requested return. Missing agents never trigger Update automatically.
- Project-local Teamwork setup is one concise managed `AGENTS.md` block. It has
  no document database, schema, case lifecycle, or migration gate.

## Commands

- Run `./scripts/validate.sh` for the small local smoke suite. Use
  `./scripts/validate.sh --release` only for explicit release preparation.
- `./scripts/check-update.sh --readiness` reports Codex install state without
  becoming a workflow gate. `init-project` maintains the project instruction
  block; `update` refreshes Codex unless another host is explicitly selected.

## Releases

- Release on `main` unless the user explicitly requests another Git workflow.
- VERSION and plugin manifest consistency is checked by
  `./scripts/validate.sh`.
- A release is complete only after the requested verification, commit, tag, and
  GitHub Release succeed. Cursor/Claude adapters and project-local files are not
  release blockers.
- Keep release notes short and describe user-visible behavior rather than
  internal tests, gates, or version history.

<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project label: `Teamwork`.
- Teamwork adds no required project-local workflow or state. It creates no empty directory, schema, or mandatory stage chain. Native host modes stay in charge. Follow this project's normal instructions and invoke a named Skill only when its trigger matches.
- User-accepted reusable results live under `docs/teamwork/<kind>/` as one of `discussions`, `research`, `debug`, `plans`, `reviews`, `reports`, or `experiments`. Chat, host plans, and todos are not cross-session memory.
<!-- TEAMWORK_PROJECT_END -->
