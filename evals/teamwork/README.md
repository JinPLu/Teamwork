# Teamwork Eval Harness

This directory contains maintainer evidence for Teamwork. It is not a runtime
stage and does not wrap ordinary user work.

## Deterministic v4 cases

Active cases use `cases/*.v4.json`. The offline runner validates their schema,
targets, three-host declaration, source limits, capability coverage, skill
topology, rubrics, and ledgers:

```bash
python3 scripts/eval-teamwork.py --split dev
python3 scripts/eval-teamwork.py --split release
python3 scripts/eval-teamwork.py --all
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_eval_teamwork_mutations.py
```

The cases are organized by capability metadata rather than hard-coded case IDs.
The dev matrix keeps bilingual coverage for:

- external Research and the local-evidence Native negative control;
- default Design activation, explicit adversarial Design activation,
  selected-direction Plan, and their ownership boundaries;
- ordinary natural question-first Grill with no file write, plus explicit
  `$grill-me` save persistence and independently-major automatic persistence
  through the managed `inspect -> schema -> apply` transaction;
- Debug, Goal, Review, Init, Update, Ask Gate, minimal native change,
  monotonic verification, permission/privacy, and cross-platform host ownership.

The release split is deliberately small but non-empty. It holds out four public
boundaries: external Research versus local Native inspection, unresolved Design
versus selected-direction Plan, explicit adversarial Design versus risk-only
default Design and chat-only recommendations, and ordinary no-write Grill versus
explicit persistence or independently-major automatic persistence through the
managed transaction. Release cases are never
optimizer inputs.

The deterministic runner does not execute Codex, Cursor, or Claude Code and does
not prove automatic skill activation. It proves only that tracked source and
fixtures preserve the declared static contract. Mutation tests must show that
removing or inverting a protected boundary makes the harness fail.

## What v4 removed

The active harness no longer protects the retired router, generic Execute skill,
an exact reference inventory, shared behavioral-reference prose, staged packet
terminology, transaction-helper anchors, multi-file discussion lifecycle, or
fixed source sentences. Each of the ten public skills owns its behavior in one
`SKILL.md`; topology validation rejects behavioral references, skill-local
behavior scripts, cross-skill loading, dependency cycles, and retired skill
names.

Mechanical safety tests for ordinary memory/index handling remain separate from
behavior activation. Grill persistence has one public contract: ordinary natural
question-first language is conversation-only; explicit save/resume/record may
persist only through the managed `inspect -> schema -> apply` transaction, while
an independently-major Grill automatically records its state through that same
route in a named, initialized writable project;
`no files` overrides it; no discussion action grants implementation authority.

## Evidence lanes

Keep evidence lanes separate:

1. **Static contract** — `eval-teamwork.py` and mutation tests validate tracked
   source and fixture behavior offline.
2. **Native transport** — `scripts/codex_app_server_user_input.py` checks the
   Codex request/response transport only; it does not mount or score a skill.
3. **Installed semantic** — the Codex, Cursor, and Claude installed-v4 adapters
   consume one prepared candidate manifest, materialize only its frozen Git tree,
   install into disposable host homes, and emit the shared v4 trajectory schema.
4. **Disposable write** — an explicitly authorized test uses a disposable
   initialized project and before/after manifests. Only this lane can support a
   claim about the observed Grill write footprint.

Do not merge these into one green claim. Record the host, model, prompt set,
repeats, sandbox, and unresolved evidence limit.

## Live trajectories

`scripts/run-teamwork-live-eval.py` keeps one-shot cases on `codex exec
--ephemeral --json`; multi-turn cases use `codex exec resume <session-id>
--json`. Use `--dry-run` first:

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

Large trajectories and paid-run evidence belong under ignored
`docs/teamwork/reports/`, not in tracked case outputs. The fake-Codex test checks
resume argv, session propagation, and missing-session failure without model
spend:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_live_eval_runner.py
```

The release matrix is `live-cases/v4-release-matrix.json`. It has exactly twelve
cases, an explicit host/profile/role model-and-effort map, and a candidate-tracked
scenario for each case. Each Codex, Cursor, and Claude slice for both
`performance-first` and `cost-first` must emit twelve records and observe all
eight formal roles inside that slice. `run-teamwork-release-matrix.py verify`
checks 72 records against `schemas/host-trajectory-v4.schema.json`, the precise
case binding, and persisted artifact hashes.

Every installed-v4 adapter requires `--project-root` and
`--candidate-manifest`. It cryptographically binds the exact base commit,
candidate tree, paths-manifest hash, allowed path/status records, Git delta, and
every post-image before extracting only that tree. Cases, schema, and setup
fixtures are then read only from that extracted candidate; a dirty source case or
schema cannot affect the run. The runner never inventories the dirty worktree and
rejects symlinked or external candidate, matrix, and output paths. Every fresh
scenario requires a non-agent host tool trace marker or a changed workspace
result with its case-specific marker and an unchanged candidate-tracked post-run
verifier. Outputs
and evidence hashes belong only under the ignored
`evals/teamwork/outputs/installed-v4/` namespace. A missing binary,
authentication/identity gap, unobservable actual model/effort/tool/authority,
privacy failure, or absent direct result is `UNSUPPORTED` or `FAIL`; neither can
be rewritten as success. Cursor and Claude prerequisites are fixed in
`protocols/cursor-installed-live.md` and `protocols/claude-installed-live.md`.

## Ledgers and optimization

`ledgers/accepted.jsonl`, `rejected.jsonl`, and
`harness-candidates.jsonl` record maintainer decisions. An optional
`optimizer-candidates.jsonl` must point to real package evidence and may use dev
cases only. Candidate generation must not read release prompts, expected values,
rubrics, or failure notes. A release failure becomes a new dev-case requirement
before retuning.
