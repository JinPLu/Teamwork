# Teamwork Evaluations

Teamwork evaluates routing and outcomes, not prompt ceremony. The canonical
mechanical inventory is `config/teamwork-topology.json`; evaluation code derives
skill, agent, reference, case, and role coverage from manifests rather than
asserting an abstract number of surfaces.

## Semantic routing pairs

`routing-pairs.json` owns paired positive and negative cases. Each pair changes
one material routing condition and names the expected route for both arms. The
suite covers every public Skill positively and protects the important negative
boundaries: clear work stays native, routine lookup does not become deep
Research, unknown failure is Debug rather than Review, unfinished direction is
Collaborate rather than Plan, Explorer remains internal, Challenger is strict
adversarial only, Reviewer handles plan review, and Writer does not write after
an unchanged turn.

Run the deterministic contract suite with:

```bash
python3 scripts/eval-teamwork.py --split dev
python3 scripts/eval-teamwork.py --split release
python3 scripts/eval-teamwork.py --all
python3 scripts/test_eval_teamwork_mutations.py
```

Retired per-case fixtures are not kept beside the active suite. Historical
ledgers, manifests, and migration records remain non-executable provenance;
only the pair manifest defines deterministic routing cases.

## Evidence lanes

Release evidence is reported in four distinct lanes:

- `static`: schemas, topology, source synchronization, and deterministic pairs;
- `installed_semantic`: behavior observed through a real installed host;
- `disposable_write`: outcome and boundary checks in a throwaway writable project;
- `dry_run`: harness and transport validation without a behavior claim.

`static`, `installed_semantic`, and `disposable_write` are required for
`release-ready`. `NOT RUN`, `UNSUPPORTED`, or `FAIL` in a required lane remains a
blocker. A passing dry run never substitutes for installed or writable evidence.

The deterministic CLI validates structural fixtures and routing pairs only. It
does not claim live answer quality.

The installed release matrix is
`live-cases/release-matrix.json`. Its cases and required roles are read from
that manifest and the topology manifest; the verifier accepts no numeric
expected-record flags. Native Root controls declare `required_role: root` and
an empty role list; every other case requires observed canonical role evidence.
Installed trace cases retain the final agent output separately from structural
tool events. A local PASS requires direct result evidence plus non-empty,
specific final-output evidence; this deterministic gate rejects empty, generic,
or refusal-style answers but does not judge semantic correctness. The
`installed_semantic` release lane can be marked `PASS` only from an independent
Reviewer verdict over the prompt, retained agent output, and rubric.
The three installed-host entrypoints are
`run-installed-codex-teamwork-live-eval.py`,
`run-installed-cursor-teamwork-live-eval.py`, and
`run-installed-claude-teamwork-live-eval.py`. Runtime hashes bind candidate
bytes and provenance only. They do not prove semantic correctness and are not
routing or acceptance gates.

## Footprint telemetry

`scripts/teamwork_tooling/instruction_footprint.py` reports real loaded-path
sizes and flags material growth from the reviewed baseline. The baseline is a
regression signal, not a prose budget: a justified semantic change may update
it, while one-byte growth and arbitrary skill/reference counts do not fail.

## Private outputs

Live trajectories, host transcripts, candidate manifests, reviews, and evidence
artifacts belong only in ignored output or temporary directories. Do not commit
credentials, raw private prompts, copied host state, or live artifacts.
