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

The Codex Plan-mode fixture treats native Plan mode as the interaction
transport and `teamwork-plan` as the quality gate. It rejects question-only
completion, unsourced locked values, and phases without ownership or proof. This
is a static contract; live Plan-mode quality still requires a fresh app-server
trajectory with `collaborationMode` set to Plan.

Ask-predicate and convergence fixtures are offline behavioral contracts. They
cover zero-question simple work, discoverable facts, required input or human
observation in every Teamwork stage, Plan's non-simple Grill entry and Decision
Summary, authority preservation after confirmation, root-owned deduplicated
Question Candidates, dependent-branch-only blocking, concise text fallback,
stable review finding IDs, blocker classification, and one bounded corrective
recheck. They contain no persistent workflow state. They validate fixture shape
and intended behavior only; they do not prove a live model follows it.

Explicit grill cases label every candidate with an internal fixture key, owner
(`evidence`, `agent`, `user-decision`, `required-input`, or `confirmation`),
grounding requirement, and expected action. Per-turn annotations identify which
user-owned candidates an authored answer asks about; those keys are test-oracle
metadata, not a user-visible protocol. Paired private/public,
internal/package, observable/preference, threshold, and reversibility cases
test semantic ownership; global language, filename, naming, or confidence word
bans are not treated as a materiality oracle. These authored contrasts remain
static, targeted contract fixtures, not evidence that any model makes the same
judgment or that a native adapter is available.

## Maintainer-only live trajectories

`scripts/run-teamwork-live-eval.py` is a separate, stdlib-only live lane. Schema
v5 keeps one-shot cases on `codex exec --ephemeral --json`; multi-turn cases
start a persistent session and continue only through
`codex exec resume <session-id> --json`. Each turn records its prompt, argv,
events, final answer, controller state, usage, reported cost when available, and
elapsed time. The record also exposes prompts consumed/remaining and the exact
termination reason. The recorder checks only bounded question count, absence of
retired grill ceremony, and read-only event structure. Question ownership and
usefulness require separate semantic review. Execution, structure, and model
provenance have separate statuses; suspension is inconclusive, and a runtime
that does not report the resolved model remains unavailable for live-verification
claims. This lane measures only its recorded Codex host/model/mode trajectory;
it does not establish Cursor or Claude parity. A missing session id fails
without `--last` or fallback.

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
eval outputs. The fake-Codex integration test exercises resume argv ordering,
session propagation, and missing-session failure without model spend:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_live_eval_runner.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_eval_teamwork_mutations.py
```

`scripts/codex_app_server_user_input.py` separately probes the Codex app-server
`request_user_input` lifecycle when that capability is callable. It never mounts
a skill, configures Codex, checks a CLI version, or treats native transport as
proof of grill semantics. The ordinary, explicit-grill, zero-question, and
simple-control scenarios state bounded behavioral expectations; question
quality remains `not_evaluated` until a human or model reviewer inspects an
opted-in run. By default the probe retains hashes and sanitized structure, never
assistant prose, native-question text, or user answers. Its fake-server test is
offline; an intentional live smoke must supply explicit `--model`, `--effort`,
`--repeats`, and `--timeout-seconds` values. `--review-dir` explicitly writes
native questions, rejected question payloads, and delimited assistant items to
a temporary reviewer directory; the caller must delete it after review.

For prompt A/B work, compare baseline and slim arms with the same non-treatment
configuration: model, effort, cases, repeats, sandbox, runner hash, and relevant
repository state. Pin the intentionally different treatment with the arm and
skill-tree hash recorded in each row; do not describe the two worktrees as
identical. Only after selecting the prompt candidate should a second experiment
compare `medium`, `high`, and `max`. These pilot cases support development
calibration; they must not be used as release tuning data or as proof of
cross-platform behavior.
