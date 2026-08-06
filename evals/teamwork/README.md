# Teamwork Evaluations

Teamwork evaluates routing and outcomes, not prompt ceremony. The canonical
mechanical inventory is `config/teamwork-topology.json`; evaluation code derives
Skill, Agent, reference, case, and role coverage from current manifests instead
of asserting an abstract surface count.

## Semantic routing cases

`routing-pairs.json` owns focused routing cases without requiring artificial
positive/negative pairing. Each case names the material routing condition and
expected route. Together the suite covers every public Skill positively and protects the important negative
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

Retired per-case fixtures are not active inputs. Historical ledgers, manifests,
and migration records remain non-executable provenance; only the current
routing manifest defines deterministic routing cases.

## Three evidence layers

Release claims stay separate:

- `structural`: schemas, topology, source/generated synchronization, ordinary
  layout, version parity, and absence of prohibited Teamwork mechanisms;
- `behavioral`: behavior directly observed through an installed host, including
  writable disposable projects when the behavior changes workspace state;
- `semantic`: an independent Reviewer reads the actual output or candidate and
  judges the declared outcomes.

All three layers must pass for the capability actually claimed on the manifest's
declared release hosts. For Teamwork 7.1, `release_hosts` is Codex only.
`NOT RUN`, `UNSUPPORTED`, or `FAIL` in a required release host/case pair remains
a blocker. A release pair declared `conditional-exact-role` may retain either an
observed `PASS` or an `UNSUPPORTED` result classified specifically as
`required-agent-not-observed`; that result verifies the published boundary and
is never relabeled as a pass. Any other failure, missing release-host support
declaration, or omitted release-host pair fails closed. Structural success
never substitutes for host behavior, and a non-empty host answer never
substitutes for semantic acceptance.

The installed release matrix is `live-cases/release-matrix.json`. It declares
`release_hosts`, and the release verifier requires the requested `--hosts` to
match that list exactly. Each case declares an intended Skill, authority,
optional disposable scenario, outcomes, and per-host adapter expectations. Cases
that require a leaf Agent also declare that role; the runner retains observed
child-start identity and never turns a desired dispatch count into a gate. It
keeps final Agent output separate from structural tool observations. Its local
gate checks only that the host completed, the requested Skill file was actually
read (or native work read no Teamwork Skill), the requested authority matches
the case, and a final answer exists. A supported `PASS` additionally requires
the declared Agent identities, successful disposable-scenario verification, and
the retained actual candidate. A conditional missing-role observation stops at
explicit `UNSUPPORTED`; it does not require downstream scenario work that could
not validly occur. The gate does not score answer wording, length, or semantic
correctness.

The three installed-host entrypoints are
`run-installed-codex-teamwork-live-eval.py`,
`run-installed-cursor-teamwork-live-eval.py`, and
`run-installed-claude-teamwork-live-eval.py`. Cursor and Claude entrypoints are
retained adapter diagnostics and development observations; they are not
Teamwork 7.1 release gates or supported-release evidence. Independent semantic
review uses the retained prompt, observed output, declared outcomes, and actual
candidate; it does not rely on fixed wording, marker counts, dispatch counts,
hashes, digests, checksums, or another sealing identity.

## Footprint telemetry

`scripts/teamwork_tooling/instruction_footprint.py` reports real loaded-path
sizes and flags material growth from the reviewed baseline. The baseline is a
regression signal, not a prose budget: a justified semantic change may update
it, while one-byte growth and arbitrary Skill/reference counts do not fail.

## Private outputs

Live observations, host transcripts, declared release cases, reviews, and
evidence artifacts belong only in ignored output or temporary directories. Do
not commit credentials, raw private prompts, copied host state, or live
artifacts.
