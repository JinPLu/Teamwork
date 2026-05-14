# Runtime Hardening And Repo Cleanup

## Goal

Upgrade the Claude Teamwork goal runtime from a plan-path convention to a
runtime-enforced contract that binds goal completion to the recorded plan
content, review checkpoints, verification status, and evidence progress. Keep
the existing `bin/raoctl.py` controller, `.claude/teamwork-goals/` state path,
and `/rao:*` compatibility commands.

## Requirements Mapping

- Plan identity is stable: verify `raoctl.py plan` only accepts
  `docs/teamwork/plans/*.md`, lints the plan, records the relative path,
  records `active_plan_artifact_sha256`, and status prints both values.
- Plan drift is blocked: verify the Stop hook compares the current plan file
  SHA-256 to runtime state before continuation or automatic completion.
- Completion is checkpoint-gated: verify automatic completion requires a
  current checkpoint for the recorded plan SHA, passing verification, and
  passing plan and execution review verdicts.
- Completion audit is stronger: verify `<completion_audit>` requires
  `plan_artifact`, `plan_artifact_sha256`, `plan_review_verdict`,
  `execution_review_verdict`, requirements mapping, verification evidence,
  and dissent.
- Evidence progress is bounded: verify `checkpoint` increments
  `no_progress_count` on no-progress evidence and the Stop hook stops after
  two consecutive no-progress checkpoints.
- Manual override remains available: verify `/teamwork:complete` and
  `/rao:complete` still mark complete but status clearly says manual completion
  was not automatically verified.
- Repo organization is explicit: add this plan artifact, mark the previous
  goal-subskill plan as executed, include goal-subskill command/runtime files,
  and leave unrelated untracked files untouched.

## Evidence Read

- `bin/raoctl.py` currently stores `active_plan_artifact`, supports `plan`, and
  gates completion on a basic audit with matching path and passing review
  verdict.
- `bin/raoctl.py` does not yet store plan SHA-256, checkpoint fields,
  verification result, review verdict checkpoints, evidence delta, or
  no-progress count.
- `scripts/validate.sh` currently covers topology and basic plan-audit runtime
  smoke tests, but not plan lint, hash mismatch, checkpoint gates, or
  no-progress stopping.
- `commands/teamwork/` and `commands/rao/plan.md` exist as untracked files from
  prior goal-subskill work; no checkpoint command wrappers exist.
- `docs/teamwork/plans/2026-05-14-goal-subskill-plan-anchor.md` still shows an
  unchecked implementation checklist even though the corresponding files are
  present in the working tree.
- `AGENTS.md` and
  `docs/teamwork/plans/2026-05-13-codex-subagent-dispatch.md` are untracked
  external files and are out of scope for edits.

## Scope

In scope:

- `bin/raoctl.py` runtime state, plan linting, checkpoint commands, Stop hook
  gates, and status output.
- `scripts/validate.sh` smoke fixtures and assertions for the new runtime
  contract.
- `/teamwork:checkpoint` and `/rao:checkpoint` command wrappers plus concise
  help/status/complete wording.
- `README.md` and `skills/teamwork-goal/SKILL.md` documentation for checkpoint
  and completion audit semantics.
- This plan artifact and execution-status cleanup for the prior
  goal-subskill plan artifact.

Out of scope:

- Renaming `bin/raoctl.py`.
- Moving `.claude/teamwork-goals/`.
- Introducing third-party dependencies.
- Implementing a full subagent dispatch runtime wrapper.
- Editing `AGENTS.md` or
  `docs/teamwork/plans/2026-05-13-codex-subagent-dispatch.md`.

## Implementation Steps

1. Add validation smoke coverage first for weak plan rejection, wrong path
   rejection, SHA status output, hash mismatch Stop-hook blocking, missing or
   wrong audit SHA blocking, missing checkpoint blocking, verification fail
   blocking, review revise blocking, pass-with-notes completion, no-progress
   stop after two checkpoints, and manual override status wording.
2. Extend `GoalState` and saved frontmatter with
   `active_plan_artifact_sha256`, `plan_recorded_at`,
   `last_checkpoint_plan_artifact_sha256`, `last_checkpoint_at`,
   `last_plan_review_verdict`, `last_execution_review_verdict`,
   `last_verification_command`, `last_verification_result`,
   `last_evidence_delta`, `no_progress_count`, and
   `manual_completion_unverified`.
3. Implement standard-library SHA-256 calculation and a plan artifact
   normalizer that rejects missing files, files outside the project, files
   outside `docs/teamwork/plans`, and non-Markdown files.
4. Implement plan linting for required non-empty sections, required
   Requirements Mapping, Verification with expected results, Worker Handoff,
   Review Handoff, and Subagent Routing sections, plus placeholder rejection
   for `TBD`, `TODO`, angle-bracket placeholders, and standalone ellipsis
   markers.
5. Update `command_plan` so a passing lint records the path and SHA, resets
   stale checkpoint fields, resets `no_progress_count`, and logs the recorded
   plan identity.
6. Add `checkpoint` and `checkpoint-raw` commands. They must validate review
   verdicts, verification result, and evidence delta, tie checkpoint data to
   the current plan SHA, update `no_progress_count`, and mark the goal stopped
   when the count reaches two.
7. Strengthen completion audit parsing and Stop-hook gating so automatic
   completion requires matching plan path, matching plan SHA, current
   checkpoint SHA, verification result `pass`, and plan and execution review
   verdicts of `pass` or `pass-with-notes`.
8. Update continuation and status output to show plan SHA, checkpoint state,
   verification/review state, no-progress count, and manual completion
   override status.
9. Add checkpoint command wrappers and update help, README, and
   `skills/teamwork-goal/SKILL.md` to document the runtime contract.
10. Mark the previous goal-subskill plan artifact as executed without changing
    its historical evidence.
11. Run `./scripts/validate.sh`, `python3 -m py_compile bin/raoctl.py`, and
    `git diff --check`.

## Verification

Focused red check:

- Run `./scripts/validate.sh` after adding the new validation assertions and
  before runtime implementation.

Expected red result:

- Validation fails because `raoctl.py` lacks plan SHA storage, plan linting,
  checkpoint commands, checkpoint-gated completion, and no-progress stopping.

Focused green checks:

- Run `./scripts/validate.sh`.
- Run `python3 -m py_compile bin/raoctl.py`.
- Run `git diff --check`.

Expected green results:

- Validation passes all topology, command, install, and runtime smoke checks.
- Python bytecode compilation exits with status 0.
- Git whitespace check exits with status 0.

## Checkpoint Invariants

- A checkpoint is valid only for the `active_plan_artifact_sha256` recorded at
  checkpoint time.
- Recording a new plan path or SHA invalidates stale checkpoint fields by
  clearing review verdicts, verification command and result, evidence delta,
  and last checkpoint SHA.
- Completion gates only accept checkpoint data whose
  `last_checkpoint_plan_artifact_sha256` equals the current recorded
  `active_plan_artifact_sha256`.
- A changed plan file must be recorded again with `raoctl.py plan`, then
  reviewed and checkpointed again before automatic completion can pass.

## Checkpoint Command Contract

`raoctl.py checkpoint` accepts explicit flags:

```text
raoctl.py checkpoint \
  --plan-review-verdict <pass|pass-with-notes|revise|blocked> \
  --execution-review-verdict <pass|pass-with-notes|revise|blocked> \
  --verification-command <command text> \
  --verification-result <pass|fail> \
  --evidence-delta <progress|no-progress>
```

All five flags are required. Values outside the listed enums fail with a
non-zero exit and do not modify state. Empty verification commands fail.

`raoctl.py checkpoint-raw` reads one shell-like argument string from stdin and
parses the same flags with `shlex.split`, matching the existing `goal-raw`
pattern. It maps to the same state fields and validation path as
`checkpoint`.

Successful checkpoint output includes:

```text
Checkpoint recorded.
Plan review verdict: <value>
Execution review verdict: <value>
Verification result: <value>
Evidence delta: <value>
No progress count: <n>
```

When `Evidence delta` is `progress`, `no_progress_count` resets to `0`. When it
is `no-progress`, `no_progress_count` increments by one. At count `2`, the
checkpoint command marks the goal `stopped`, records `stopped_at`, and prints
`Goal stopped after 2 consecutive no-progress checkpoints.`

## Hash Drift Hook Contract

Before any automatic completion or continuation, `hook-stop` validates the
recorded plan identity:

- If no active plan path or SHA is recorded, it returns a Claude
  `decision:block` response instructing the agent to create, lint, review, and
  record a plan before continuing. It does not increment `iteration`.
- If the recorded plan file is missing, outside the allowed path, or has a
  different current SHA-256, it sets `status: stopped`, records `stopped_at`,
  sets `last_hook_event: stop_plan_hash_mismatch`, appends an iteration log
  entry, and returns no continuation prompt. The next agent/user must run
  `raoctl.py plan` again after updating/reviewing the plan, then resume
  explicitly if appropriate.
- If `no_progress_count >= 2`, it sets `status: stopped`, records
  `stopped_at`, sets `last_hook_event: stop_no_progress`, and returns no
  continuation prompt.

## Risks

- The stricter plan linter may reject older valid-looking plans. Limit the
  lint to required runtime-hardening guarantees and avoid style policing.
- Runtime smoke tests can become brittle if they depend on exact prose. Prefer
  checking stable status labels and gate outcomes.
- Manual completion could be mistaken for audited completion. Make the status
  line explicit whenever manual override was used.

## Stop Rules

- Stop if checkpoint gating conflicts with `/rao:*` compatibility.
- Stop if plan linting would require parsing Markdown beyond simple headings
  and text blocks.
- Stop if validation requires editing unrelated untracked files.

## Worker Handoff

Worker role: main agent execution stage.

Task scope: edit only `bin/raoctl.py`, `scripts/validate.sh`, command wrapper
files under `commands/teamwork` and `commands/rao`, `README.md`,
`skills/teamwork-goal/SKILL.md`, this plan artifact, and the prior
goal-subskill plan artifact.

Context strategy: read direct source and diffs before changing each file; keep
existing user or prior-agent changes unless they directly conflict with this
plan.

Verification expectation: perform the focused red check after validation edits,
then implement runtime changes and run all green checks listed above.

## Review Handoff

Review role: final execution review after verification.

Review scope: inspect the diff against this plan, validate hash and checkpoint
state transitions, confirm Stop-hook gates, check command compatibility, review
validation coverage, and verify unrelated untracked files remain untouched.

Required verdict: `pass` or `pass-with-notes` before reporting completion.

## Subagent Routing

- Explorer: skipped. Scope is compact and direct source has already been read.
  Tier is fast. Context is local repository evidence. Order is not applicable.
- Designer: skipped. The user supplied the target design and this artifact
  records the executable plan. Tier is high reasoning. Context is accepted
  runtime-hardening intent.
- Judge: default agent. Scope is plan review before runtime edits. Tier is high
  reasoning. Context is this artifact plus direct repository evidence. Order is
  serial before implementation.
- Worker: main agent. Scope is the files listed in Worker Handoff. Tier is
  standard. Context is this accepted plan artifact. Order is serial because
  runtime and validation edits are coupled.
- Reviewer: default agent or main distinct review pass. Scope is final diff and
  verification evidence. Tier is high reasoning. Context is direct diff,
  validation output, and this plan artifact. Order is after implementation.
