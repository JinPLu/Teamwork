# Teamwork Eval Harness

This directory contains tracked fixtures for Teamwork package maintenance.
The harness is producer-side evidence, not a runtime stage for ordinary user
tasks.

## Layout

- `cases/*.json`: compact behavioral cases for Teamwork skills, references, and
  package governance.
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
behavior expectations. Eval output is evidence, not final acceptance.
