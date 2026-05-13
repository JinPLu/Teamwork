# Always Persist Teamwork Plans

## Goal

Make every Teamwork planning pass create a durable Markdown plan artifact, including lightweight plans.

## Requirements Mapping

- All `teamwork-design mode: plan` outputs must write a repository artifact: verify by inspecting `skills/teamwork-design/SKILL.md`.
- Router and Codex guidance must not describe chat-only plans as acceptable: verify by inspecting `skills/teamwork/SKILL.md`, `CODEX.md`, and `README.md`.
- Plan review must reject missing artifacts for every plan: verify by inspecting `skills/teamwork-review/SKILL.md`.
- Repository validation must catch regressions: verify with `./scripts/validate.sh`.

## Evidence Read

- `skills/teamwork-design/SKILL.md` currently allows lightweight chat-visible plans.
- `skills/teamwork/SKILL.md`, `CODEX.md`, and `README.md` document the same exception.
- `scripts/validate.sh` currently checks only that non-lightweight durable artifacts are documented.

## Scope

- In scope: Teamwork skill instructions, user-facing Codex/README docs, validation checks.
- Out of scope: Codex runtime hooks, Claude Stop-hook behavior, installer mechanics.
- Sacred boundaries: keep skills Markdown-only and avoid adding runtime dependencies.

## Implementation Steps

- [x] Update `skills/teamwork-design/SKILL.md` so every plan uses `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.
- [x] Update `skills/teamwork/SKILL.md` to remove chat-visible plan exceptions.
- [x] Update `skills/teamwork-review/SKILL.md` so missing artifact is a hard gate for every plan.
- [x] Update `CODEX.md` and `README.md` to document all-plan persistence.
- [x] Update `scripts/validate.sh` to assert the new rule and reject the old exception.

## Verification

- Focused: `rg -n "chat-visible plan is enough|chat-visible plan|non-lightweight work has a Markdown|non-lightweight execution plans|Small, low-risk edits may use a chat|轻量改动可以使用聊天计划|非小改默认" skills README.md CODEX.md scripts/validate.sh`.
- Install check: `rg -n "All plans must be written|Teamwork planning pass must create|every plan has a Markdown plan artifact|chat-visible plan is enough" ~/.codex/skills/teamwork*`.
- Broader: `./scripts/validate.sh`.
- Results: obsolete chat-only plan exceptions are absent from source skills/docs, installed Codex skills contain the new all-plan persistence rules, and validation passes.

## Worker Handoff

Execute only the documentation and validation changes listed above.

## Review Handoff

Check that every planning path now requires a readable durable artifact and that validation catches regressions.
