# Teamwork Eval Harness

This directory contains tracked fixtures for Teamwork package maintenance.
The harness is producer-side evidence, not a runtime stage for ordinary user
tasks.

## Layout

- `cases/*.json`: compact behavioral cases for Teamwork skills, references, and
  package governance.
- `live-cases/*.json`: maintainer-only Codex trajectory pilots. These are small
  development probes, not release cases or optimizer inputs.
- `rubrics/*.json`: scoring contracts used by cases.
- `ledgers/accepted.jsonl` and `ledgers/rejected.jsonl`: package decisions.
- `ledgers/harness-candidates.jsonl`: deterministic harness candidate history.
- `ledgers/optimizer-candidates.jsonl` when present: Candidate Ledger V2 rows
  for real SkillOpt-Lite/HarnessOpt-Lite pilot runs, with rows pointing to
  evidence artifacts rather than placeholders.
- samples/candidate workspaces: keep compact reusable samples in tracked
  eval artifacts only when promoted; keep large runs under
  `docs/teamwork/reports/`.

Large trajectories and run reports belong in `docs/teamwork/reports/`; promote
only compact, reusable expectations into `cases/`.

## Splits

- `dev`: used while developing skill or harness changes.
- `release`: frozen audit cases for release or public-contract claims.

Release cases are not secret, but they are never optimizer inputs. Candidate
generation must not read release prompts, expected outputs, rubrics, or failure
notes; release findings become new dev-case planning before retuning.

## Commands

```bash
python3 scripts/eval-teamwork.py --split dev
python3 scripts/eval-teamwork.py --split release
python3 scripts/eval-teamwork.py --all
```

The first runner is deterministic and offline. It validates fixture shape,
split/platform/source values, target paths, rubrics, ledgers, and non-empty
behavior expectations. It does not execute Codex, Cursor, Claude, or prove live
model behavior. Eval output is evidence, not final acceptance.

## Maintainer-only live trajectories

`scripts/run-teamwork-live-eval.py` is a separate, stdlib-only live lane. It
runs `codex exec --ephemeral --json`, records raw events and the final answer,
and writes provenance-rich JSONL. It never changes the model or reasoning
effort after launch: an unavailable model, including `gpt-5.6-sol` at `max`, is
recorded as unavailable or failed rather than silently replaced.

All execution-critical inputs are explicit. Cases default to `read-only` by
declaring it in the case file; `workspace-write` is permitted only when the
individual case explicitly declares that sandbox. The tracked cases all remain
read-only pilots. Use `--dry-run` in CI or before a live experiment to validate
case and output schemas without invoking Codex:

```bash
python3 scripts/run-teamwork-live-eval.py \
  --arm baseline \
  --model gpt-5.6-sol \
  --effort max \
  --workdir "$PWD" \
  --output /tmp/teamwork-live-dry-run.jsonl \
  --cases evals/teamwork/live-cases/*.json \
  --repeats 1 \
  --timeout-seconds 1800 \
  --dry-run
```

Remove `--dry-run` only for an intentional maintainer experiment. Choose a new
output path for every invocation; the runner refuses to overwrite provenance.
Large live trajectories belong under `docs/teamwork/reports/`, not in tracked
eval outputs.

For prompt A/B work, compare baseline and slim arms with the same non-treatment
configuration: model, effort, cases, repeats, sandbox, runner hash, and relevant
repository state. Pin the intentionally different treatment with the arm and
skill-tree hash recorded in each row; do not describe the two worktrees as
identical. Only after selecting the prompt candidate should a second experiment
compare `medium`, `high`, and `max`. These pilot cases support development
calibration; they must not be used as release tuning data or as proof of
cross-platform behavior.
