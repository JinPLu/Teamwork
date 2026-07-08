# Teamwork Eval Harness

This directory contains tracked fixtures for Teamwork package maintenance.
The harness is producer-side evidence, not a runtime stage for ordinary user
tasks.

## Layout

- `cases/*.json`: compact behavioral cases for Teamwork skills, references, and
  package governance.
- `rubrics/*.json`: scoring contracts used by cases.
- `ledgers/*.jsonl`: accepted, rejected, and harness-candidate decisions.

Large trajectories and run reports belong in `docs/teamwork/reports/`; promote
only compact, reusable expectations into `cases/`.

## Splits

- `dev`: used while developing skill or harness changes.
- `release`: frozen audit cases for release or public-contract claims.

Release cases are not secret, but they are not optimization targets. If a
release case reveals a real missing behavior, add or update a dev case and
ledger the decision before retuning.

## Commands

```bash
python3 scripts/eval-teamwork.py --split dev
python3 scripts/eval-teamwork.py --split release
python3 scripts/eval-teamwork.py --all
```

The first runner is deterministic and offline. It validates fixture shape,
split/platform/source values, target paths, rubrics, ledgers, and non-empty
behavior expectations. Eval output is evidence, not final acceptance.
