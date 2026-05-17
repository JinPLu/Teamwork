# Finalize Runtime Hardening GitHub Sync

## Goal

Finish the Teamwork runtime-hardening cleanup, include the relevant durable
artifacts, verify the package, then commit and push `main` to GitHub.

## Requirements Mapping

- Preserve the completed runtime hardening: verify `bin/raoctl.py`,
  `commands/teamwork`, `commands/rao`, `skills/teamwork-goal/SKILL.md`, and
  `scripts/validate.sh` remain consistent.
- Keep future agents aligned with Teamwork naming: update and include
  `AGENTS.md`, then verify it no longer describes `run-analyze-optimize` as
  the active package.
- Keep plan artifacts durable: include the previously untracked Codex
  dispatch plan and this final sync plan in `docs/teamwork/plans/`.
- Keep plan templates compatible with Claude runtime plan linting: verify
  `teamwork-design` plan output includes a `Goal` section name that matches
  the runtime linter.
- Push to GitHub only after focused validation, Python compilation, whitespace
  check, and a final execution review pass.

## Evidence Read

- Observed `git status --short --branch`: branch is `main...origin/main` with
  tracked runtime/docs changes and untracked `AGENTS.md`, command wrappers,
  and plan artifacts.
- Observed `AGENTS.md`: current text still says the repository packages
  `run-analyze-optimize` and lists four installed skills.
- Observed `bin/raoctl.py`: plan linting requires non-empty `Goal`,
  `Requirements Mapping`, `Evidence Read`, `Scope`, `Implementation Steps`,
  `Verification`, `Risks`, `Stop Rules`, `Worker Handoff`, `Review Handoff`,
  and `Subagent Routing` sections.
- Observed `skills/teamwork-design/SKILL.md`: the plan output template uses
  `Root Cause / Goal`, which is less directly compatible with the runtime
  linter's exact `Goal` section requirement.

## Scope

In scope:

- `AGENTS.md` wording and command counts.
- `skills/teamwork-design/SKILL.md` plan output section name alignment.
- `scripts/validate.sh` focused checks for the above alignment.
- Relevant untracked Teamwork command and plan artifact files.
- Git staging, commit, and push after verification.

Out of scope:

- Rewriting the already implemented runtime-hardening logic.
- Renaming `bin/raoctl.py` or removing `/rao:*` compatibility.
- Editing generated runtime state under `.claude/teamwork-goals/`.
- Rewriting historical plan artifacts beyond including them in version
  control.

## Implementation Steps

- [x] 1. Judge this plan against the current diff and scope before editing.
- [x] 2. Update `AGENTS.md` from stale `run-analyze-optimize` wording to
  current Teamwork structure, commands, and installed skill count.
- [x] 3. Update `skills/teamwork-design/SKILL.md` so the plan output template
  uses `Goal` as the durable artifact section name.
- [x] 4. Add focused validation checks that catch stale `AGENTS.md` naming and
  the exact `Goal` plan-template heading.
- [x] 5. Run `./scripts/validate.sh`, `python3 -m py_compile bin/raoctl.py`,
  and `git diff --check`.
- [x] 6. Perform a distinct execution review pass over the diff and
  verification evidence.
- [x] 7. Stage only in-scope files, commit with a concise imperative message,
  push `main` to `origin`, and verify branch status.

## Verification

- Focused: `./scripts/validate.sh`.
- Python syntax: `python3 -m py_compile bin/raoctl.py`.
- Whitespace: `git diff --check`.
- Git hygiene: `git status --short --branch` before and after push.

Expected Results:

- Validation prints `OK: Teamwork skill package validates`.
- Python compilation exits with status 0.
- Whitespace check exits with status 0.
- The commit includes Teamwork runtime hardening, command wrappers, docs,
  relevant plan artifacts, and refreshed `AGENTS.md`.
- `main` is pushed to `origin/main`.

## Risks

- Including stale `AGENTS.md` could mislead future agents. Mitigation: update
  it before staging.
- Validation checks could overfit prose. Mitigation: check stable project names
  and key section headings only.
- A push could fail because the remote advanced. Mitigation: stop and report
  the non-fast-forward instead of rewriting history.

## Stop Rules

- Stop if validation fails for a reason unrelated to this scoped cleanup and
  the cause is not clear from local evidence.
- Stop if `git push` is rejected as non-fast-forward.
- Stop if staging would require unrelated files outside this plan.

## Worker Handoff

Execute only the steps above. Preserve the existing runtime implementation and
avoid adjacent refactors.

## Review Handoff

Review the final diff against this artifact, validation output, commit
contents, and push result. Check for stale `run-analyze-optimize` claims,
broken `/rao:*` compatibility, and missing durable artifacts.

## Subagent Routing

- Explorer: skipped | scope: current evidence already read from files and git
  status | tier: fast | context: local repository evidence | order: not
  applicable | why: remaining work is narrow.
- Designer: skipped | scope: direction selected by user and encoded in this
  artifact | tier: high reasoning | context: this plan | order: not
  applicable | why: no unresolved architecture decision.
- Judge: main distinct pass | scope: plan review before edits | tier: high
  reasoning | context: plan plus current diff | order: serial before
  implementation | why: subagent dispatch was not explicitly requested.
- Worker: main agent | scope: `AGENTS.md`, `skills/teamwork-design/SKILL.md`,
  `scripts/validate.sh`, staging/commit/push | tier: standard | context:
  accepted plan artifact | order: serial | why: edits are coupled and small.
- Reviewer: main distinct pass | scope: final diff, validation, and Git state |
  tier: high reasoning | context: direct evidence | order: serial after
  verification | why: required final quality gate before completion.
