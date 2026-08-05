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
- exactly three base Collaborate triggers, L1 intent clarification, L2 joint
  exploration, L3 challenge inside an active discussion, and the
  selected-direction Plan boundary; risk categories are not another trigger;
- contribution and recommendation before native Ask Question, with independent
  questions batched, dependent questions serialized and waited on, and no
  workflow-wide question or round cap;
- four-part semantic Collaborate persistence through Writer at the first
  substantive synthesis, each semantic change, and the end, using the case-v2
  `case-inspect -> case-schema -> case-apply` transaction, with legacy-v1
  artifacts treated only as read-only migration inputs and no transcript or
  report substitute;
- Debug, Goal, Review, Init, Update, Ask Gate, minimal native change,
  monotonic verification, permission/privacy, and cross-platform host ownership.

The release split is deliberately small but non-empty. It holds out four public
boundaries: external Research versus local Native inspection; unresolved
Collaborate options versus selected-direction Plan; the three base triggers and
L3 adversarial execution versus risk-only cues and chat-only recommendations;
and semantic Collaborate persistence versus one-shot and no-files controls. Release cases are never
optimizer inputs.

The deterministic runner does not execute Codex, Cursor, or Claude Code and does
not prove automatic skill activation. It proves only that tracked source and
fixtures preserve the declared static contract. Mutation tests must show that
removing or inverting a protected boundary makes the harness fail.

## What v4 removed

The active harness no longer protects the retired router, generic Execute skill,
an exact reference inventory, shared behavioral-reference prose, staged packet
terminology, transaction-helper anchors, multi-file collaboration lifecycle, or
fixed source sentences. Each public skill owns its behavior in one `SKILL.md`;
Collaborate may directly link its single layer/scenario reference and unchanged
adversarial-method reference. Topology validation rejects extra behavioral
references, skill-local behavior scripts, cross-skill loading, dependency
cycles, and retired skill names.

Mechanical safety tests for ordinary memory/index handling remain separate from
behavior activation. Collaborate has three base triggers: the user explicitly
asks to discuss, design, plan, brainstorm, compare, or think together; a
material choice belongs to the user; or intent needs guided clarification. Risk
alone is not a trigger. One discussion moves between L1 Understand Intent, L2
Explore Together, and L3 Challenge and Converge. It contributes synthesis,
options, and a recommendation before native Ask Question; batches necessary
independent questions, serializes and waits on dependent questions, and has no
workflow-wide question or round cap. Writer maintains one four-part semantic
document at the first substantive synthesis, each semantic change, and the end
through the managed case-v2
`case-inspect -> case-schema -> case-apply` transaction in a named, initialized
writable project. Legacy-v1 records are read-only migration inputs with no
write fallback, no transcript or report is substituted, `no files` overrides
persistence, and no Collaborate action grants implementation authority.

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
   claim about the observed case-v2 Collaborate write footprint. Historical
   Grill names appear only in legacy detector fixtures or migration inputs.

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
