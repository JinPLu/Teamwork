# Sync All-Plans Rule to GitHub

## Goal

Commit and push the all-plans-must-persist workflow update to `origin/main`.

## Requirements Mapping

- Include the workflow rule changes: stage `skills/teamwork-design/SKILL.md`, `skills/teamwork/SKILL.md`, `skills/teamwork-review/SKILL.md`, `CODEX.md`, `README.md`, and `scripts/validate.sh`.
- Include durable plan artifacts for the change and this sync operation: stage `docs/teamwork/plans/2026-05-13-always-persist-plans.md` and this file.
- Exclude unrelated untracked `AGENTS.md`: verify with `git status --short` before commit.
- Push to GitHub: verify with `git status --short --branch` after push.

## Evidence Read

- `git status --short --branch`: branch is `main...origin/main`; six tracked files modified, `docs/` and `AGENTS.md` untracked.
- `git remote -v`: `origin` fetch and push point to `https://github.com/JinPLu/Teamwork.git`.
- `git diff --stat`: tracked workflow/doc/validation changes are present.

## Scope

- In scope: commit and push the all-plans persistence changes and plan artifacts.
- Out of scope: staging unrelated `AGENTS.md`, rewriting history, changing remotes.
- Sacred boundaries: do not include unrelated local files.

## Implementation Steps

- [x] Run validation before commit.
- [x] Stage only in-scope files.
- [x] Commit with a concise imperative message.
- [x] Push `main` to `origin`.
- [x] Verify the working tree and branch status.

## Verification

- Focused: `git status --short` confirms only intended files are staged before commit.
- Broader: `./scripts/validate.sh` passes before commit.
- Push: `git push origin main` succeeds and `main` is no longer ahead locally.

## Worker Handoff

Execute the git sync steps exactly as listed.

## Review Handoff

Confirm the commit excludes `AGENTS.md`, validation passed, and push succeeded.
