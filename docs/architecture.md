# Teamwork Repository Architecture

Teamwork is a Codex-first skill package with adapters for Cursor and Claude
Code. The repository keeps authored package inputs separate from producer
tooling and from local or generated install surfaces.

## Canonical Tree

```text
skills/                         authored workflow behavior and shared references
templates/                      authored Codex, Cursor, and Claude agent adapters
hooks/                          authored notification runtime and hook manifest
evals/teamwork/
  cases/                        deterministic behavior cases
  live-cases/                   bounded live trajectory cases
  rubrics/                      semantic review criteria
  ledgers/                      accepted/rejected evaluation records
  outputs/                      curated authored output fixtures
scripts/
  validate.sh                   stable validation entrypoint
  eval-teamwork.py              stable deterministic evaluation entrypoint
  run-teamwork-live-eval.py     stable live trajectory recorder
  run-installed-teamwork-live-eval.py
                                opt-in isolated installed-package canary
  teamwork_tooling/             coarse, standard-library-only Python producers
  validation/                   coarse Bash package and integration checks
  install/                      coarse Bash installer modules
  tests/                        focused harness tests and fixtures
install.sh                      stable installer dispatcher
.codex-plugin/                  authored Codex package metadata
.claude-plugin/                 authored Claude Code package metadata
VERSION, CHANGELOG*, README*    authored release and public documentation
docs/architecture.md            this tracked architecture contract
CONTRIBUTING.md                 contributor entrypoint
```

The following are sinks, not package sources:

- `.agents/`, `.codex/`, `.cursor/`, and `.claude/` are generated local
  installations. Edit `skills/`, `templates/`, or the relevant producer
  instead of editing an installed copy.
- `docs/teamwork/` is local Teamwork runtime memory. Its plans, research,
  discussion, reports, and active-state files are ignored unless a maintainer
  explicitly promotes an artifact.
- Temporary live-run outputs, temporary homes, caches, logs, and build output
  are generated evidence or scratch state. They must not become package inputs.

`evals/teamwork/outputs/` is the exception: its compact tracked JSONL files are
authored static fixtures used by deterministic evaluation. Large or raw runs
remain untracked and belong in temporary review storage or an intentional
`docs/teamwork/reports/` artifact.

Tracked public docs, assets, manifests, evaluation cases, rubrics, and ledgers
are authored source. Generated evidence may verify those sources, but it does
not define them.

## Dependency Direction

Dependencies point from stable entrypoints toward producers and canonical
inputs, never back from generated installations:

```text
public commands
  -> coarse producer modules
    -> skills / templates / hooks / eval inputs / manifests / VERSION
      -> generated install, validation, or evaluation output
```

`skills/` owns workflow meaning. Platform adapters in `templates/` express that
meaning for each host; they do not define a second workflow contract. Validation
and evaluation consume canonical inputs and emit evidence. Installers consume
canonical inputs and write platform-local sinks. A sink must never be read as a
fallback source when its producer input is absent.

## Stable Commands

Keep these public producer commands and their CLI behavior compatible:

```bash
./install.sh [options] TARGET
./scripts/validate.sh
python3 scripts/eval-teamwork.py [options]
```

`python3 scripts/run-teamwork-live-eval.py` is the stable recorder for bounded
live trajectories. `python3 scripts/run-installed-teamwork-live-eval.py` wraps
that recorder with an isolated Codex install, an installed-file manifest, and
externally validated semantic reviews. Both supplement deterministic
evaluation; neither proves automatic skill activation or Cursor/Claude parity.
The installed canary isolates its user home, not an arbitrary supplied
worktree; use a clean Git snapshot when project-local generated surfaces would
confound the treatment.

Thin entrypoints may delegate to `scripts/teamwork_tooling/` or
`scripts/install/`, but callers should not need to know those internal module
boundaries. Python producer modules remain standard-library-only. Installation
is orchestrated by Bash and uses standard-library Python helpers for Codex
routing/configuration; it adds no third-party Python dependency.

## Change Owners

| Change | Primary owner | Required companion evidence |
|---|---|---|
| Workflow routing, stage behavior, or shared policy | `skills/*/SKILL.md` and `skills/using-teamwork/references/` | Focused contract/evaluation case; platform adapters only when their rendering changes |
| Platform agent role, prompt adapter, or model profile | `templates/*-agents/` | Profile/render validation for every affected platform |
| Notifications | `hooks/` and notification configuration scripts | Hook manifest validation and focused hook tests |
| Install targets, destinations, policy blocks, or profiles | `install.sh` and `scripts/install/` | Isolated-home/project installer fixtures |
| Package validation behavior | `scripts/validate.sh` and validation modules | Focused harness tests, including a representative failing mutation |
| Deterministic or semantic evaluation | `scripts/eval-teamwork.py`, evaluation modules, and `evals/teamwork/` | Case/rubric schema checks and mutation-sensitive tests |
| Live trajectory recording | `scripts/run-teamwork-live-eval.py` and live-eval fixtures | Isolated, bounded runner tests; claims limited to observed treatment |
| Installed Codex semantic canary | `scripts/run-installed-teamwork-live-eval.py`, `scripts/teamwork_tooling/live_canary.py`, and the semantic-review contract | Fake-process isolation/redaction tests plus an explicitly authorized bounded live run |
| Versioned public surface | `VERSION`, plugin manifests, changelogs, and public docs | Full validation plus the repository release policy |

## Anti-Drift Rules

- Change canonical producers, never generated copies or local install roots.
- Update the owning skill first for workflow behavior; keep platform adapters
  aligned without creating parallel semantics.
- Preserve the stable command paths, arguments, exit behavior, and install
  destinations. Internal extraction must remain invisible to callers.
- Keep modules coarse and cohesive. Do not add generic utility buckets,
  per-check modules, permanent old/new modes, or a duplicate inventory manifest
  for directories that can be discovered.
- Keep dependency flow one-way. Validation, evaluation, and installers may read
  canonical inputs; canonical inputs must not depend on their outputs.
- Add focused proof at the changed boundary. A successful static or fake-process
  check must not be described as live user-visible model behavior.
- Treat ignored runtime memory and generated evidence as local by default. Do
  not publish or promote it accidentally.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the contributor workflow.
