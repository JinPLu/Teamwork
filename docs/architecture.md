# Teamwork Repository Architecture

Teamwork is a Codex-first skill package with Cursor and Claude Code adapters.
Version 4 keeps each skill self-contained and leaves ordinary local inspection
and clear authorized implementation to the host. The repository separates
authored capability sources from producer tooling and from generated or local
install surfaces.

## Canonical tree

```text
skills/
  <capability>/SKILL.md          self-contained user-facing capability
  <capability>/references/       only the owning skill's advanced method
  <capability>/agents/openai.yaml optional host interface metadata
templates/                       eight-role install-time host-agent adapters
hooks/                           authored notification runtime and hook manifest
evals/teamwork/
  cases/                         deterministic behavior cases
  live-cases/                    bounded live trajectory cases
  rubrics/                       semantic review criteria
  ledgers/                       accepted/rejected evaluation records
  outputs/                       compact authored output fixtures
scripts/
  build-codex-plugin.py          Marketplace bundle producer/checker
  validate.sh                    stable validation entrypoint
  eval-teamwork.py               stable deterministic evaluation entrypoint
  run-teamwork-live-eval.py      bounded live trajectory recorder
  run-installed-teamwork-live-eval.py
                                  opt-in installed-package canary
  teamwork_tooling/              standard-library Python producers
  validation/                    Bash package and integration checks
  install/                       Bash installer modules
  tests/                         focused harness tests and fixtures
install.sh                       stable installer dispatcher
.codex-plugin/                   authored Codex package metadata
.claude-plugin/                  authored Claude Code package metadata
.agents/plugins/marketplace.json authored Marketplace catalog
plugins/teamwork-skill/          tracked generated Marketplace runtime
VERSION, CHANGELOG*, README*     authored release and public docs
docs/architecture.md             this architecture contract
CONTRIBUTING.md                  contributor entrypoint
```

The public capability inventory is exactly ten: `grill-me`, `teamwork-debug`,
`teamwork-design`, `teamwork-explore`, `teamwork-goal`, `teamwork-init`,
`teamwork-plan`, `teamwork-research`, `teamwork-review`, and
`teamwork-update`. There are exactly three advanced references:
Debug's runtime-diagnosis reference, Research's deep-research reference, and
Review's strict-review reference. They are methods of those skills, not shared
workflow stages.

Host adapters have exactly eight roles—Researcher, Explorer, Debugger, Designer,
Planner, Worker, Plan Reviewer, and Reviewer—under each of the Codex, Cursor,
and Claude Code template directories.

The following are sinks, not package sources:

- `.agents/` except `.agents/plugins/marketplace.json`, `.codex/`, `.cursor/`,
  and `.claude/` may contain generated or legacy local installations. Global Cursor
  installs may write `~/.cursor/mcp.json` and a Teamwork ownership sidecar; project
  init writes `.cursor/rules/` and optional project `.cursor/mcp.json` only with
  explicit `--cursor-mcp` consent. Edit `skills/`, `templates/`, or the owning
  producer instead of an installed copy.
- `docs/teamwork/` is local Teamwork runtime memory. Grill has one
  transaction-owned record, `docs/teamwork/discussion/current.md`, and it is not
  indexed into a second memory file. Natural question-first requests remain
  conversation-only; explicit persistence and independently major boundaries
  use that transaction. A material Design freezes through its controlled
  transaction into one durable Design artifact before Plan. Plan has its own
  single durable artifact; Review is read-only. Research and report artifacts
  remain local unless a maintainer intentionally promotes one.
- Temporary live outputs, homes, caches, logs, and build results are evidence or
  scratch state. They must not become package inputs.

`evals/teamwork/outputs/` is the exception: its compact tracked JSONL files are
authored static fixtures. `evals/teamwork/outputs/installed-v4/**` is ignored
candidate/runtime evidence. Large or raw runs stay untracked in temporary review
storage or an intentional local report.

Tracked public docs, assets, manifests, evaluation inputs, and ledgers are
authored sources. `plugins/teamwork-skill/` is a versioned release artifact
generated only by `scripts/build-codex-plugin.py` from current skills, runtime
helpers, all three host-role template inventories, memory templates, migration
fixtures and ledger, notifications, `VERSION`, and the Codex manifest. The root
Claude Code manifest is validated with the release but is not copied into the
Codex-only bundle. Generated evidence may verify those sources but never defines
them.

## Capability boundaries

Each `skills/<capability>/SKILL.md` contains the behavior needed to use that
capability. Skills do not invoke other skills as subroutines, load another
skill's instructions, depend on shared behavior references, or carry
skill-local scripts. Deterministic package mechanics belong under top-level
`scripts/`; optional `agents/openai.yaml` files contain interface metadata only.

This keeps the main boundaries visible:

- the host natively inspects local repositories, configuration, tests, logs,
  runtime state, and artifacts, and natively implements clear authorized work;
- Explore answers a distinct local read-only evidence question; Research is only
  for external, current, multi-source, or citation-backed investigation;
- Design owns an unsettled consequential solution. Explorer is dispatched only
  for an unresolved local constraint, and Research only for a named sanitized
  external/current claim that can change the decision; neither is mandatory and
  they do not run together by default. Designer integrates the evidence actually
  needed. A real trade-off gets two or
  three alternatives; one safe path gets explicit evidence and exclusions. One
  challenge pass and a finite user-decision frontier converge into a durable
  Design artifact before Plan. The frontier shows a global map first, batches
  only independent material questions, and serializes dependent questions;
- Plan turns an already selected direction into executable steps; independent
  Plan Review runs only on user request or a named material risk gate. Each
  Worker self-verifies its slice. After integration, a sealed candidate receives
  one independent max `ACCEPT`, `REVISE`, or `BLOCKED` Review only on user request
  or a named material risk gate; findings are repaired as one batch and each
  candidate gets at most one delta recheck;
- Debug constrains unknown-cause failure work to real failure, reproduction,
  discriminating evidence, the authorized narrow fix, and the same-path rerun;
- Grill owns user question-first discussion. Explicit persistence and an
  independently major public/installable, migration/release, permission,
  security, data, destructive, or cross-platform boundary use the one durable
  discussion transaction unless the user says no files/off-the-record. Within
  one scope, only create, semantic decision/frontier change, and close/supersede
  write a revision; unchanged state is a no-op. New records use
  `frontier` / `current_batch` state;
- Goal adds explicit durable objective, success signal, scope, protected
  boundaries, budget, and attempt state; Init changes one project's context
  only, while Update changes global Teamwork-managed installation state only.

There is no Teamwork router or generic execution capability. Host skill
discovery chooses a capability directly; exact selection remains model behavior.
The v3.4.2 migration recognizes only proven owned Router/Execute and legacy-role
files so it can remove them safely. That migration recognition is not a v4 alias
or callable compatibility surface.

## Method attribution

Teamwork adopts Superpowers' hard gate, options, and specification self-check
ideas. Its one-pass challenge and finite decision frontier are locally tailored
Teamwork convergence rules, rather than a claim to reproduce a Superpowers
workflow wholesale.

## Templates are install-time adapters

Files under `templates/` are authored inputs that installers render or copy into
host-native agent definitions. They are not runtime skill prompts, not a shared
behavior library, and not a fallback source for a `SKILL.md`. No skill may read
a template to acquire rules. Once installed, the host may use the resulting
agent configuration in its normal way; the canonical Teamwork capability still
lives in its own `SKILL.md`.

The recommended local Codex Root configuration remains user-controlled. The
installer configures only subagent profiles and routing; it does not set the
Root main-task default. Codex renders the eight roles with exact profile
mapping: performance-first uses `gpt-5.5`/`high` for Researcher, Explorer,
Debugger, Planner, and Worker; `gpt-5.6-sol`/`high` for Designer and Plan
Reviewer; and `gpt-5.6-sol`/`max` for Reviewer. cost-first uses
`gpt-5.5`/`medium` for Researcher, Explorer, Debugger, Planner, and Worker;
`gpt-5.6-sol`/`medium` for Designer; and `gpt-5.6-sol`/`high` for Plan Reviewer
and Reviewer. Cursor and Claude Code templates remain host-native adapters; this
does not promise the Codex reasoning-effort mapping on those hosts. On Codex 0.144,
formal `spawn_agent` dispatch is only observed for `gpt-5.5`; Designer, Plan
Reviewer, and Reviewer on `gpt-5.6-sol` may execute without formal agent isolation
on 0.144—verify dispatch fidelity via live eval when Codex advances.

## Dependency direction

Dependencies move from stable entrypoints toward producers and canonical
inputs, never back from generated installations:

```text
public commands
  -> coarse producer modules
    -> independent skills / templates / hooks / eval inputs / manifests / VERSION
      -> generated Marketplace bundle, install, validation, or evaluation output
```

There are no skill-to-skill behavior edges. Platform adapters express
host-specific agent configuration without defining a parallel capability
contract. Validation and evaluation consume canonical inputs and emit evidence.
Installers consume canonical inputs and write host-local sinks. A sink must
never be read as a fallback source when its producer input is absent.

`scripts/build-codex-plugin.py` is the only producer for
`plugins/teamwork-skill/`; `--check` rejects hand edits or an incomplete runtime
closure. Marketplace skills run from Codex's cache. Plugin bootstrap owns Codex
agents, routing, managed policy, notifications, verified legacy cleanup, and
the activation marker; it does not copy plugin skills into a user skill root.

Project initialization is intentionally separate. Checkout and plugin init
paths write only the selected project's managed instructions, memory entry
points, ignore rules, and available CodeGraph context. With explicit
`--cursor-mcp` consent they may also write project `.cursor/rules/*.mdc` and
merge Teamwork MCP entries into project `.cursor/mcp.json`. They never refresh
global skills, agents, policy, routing, notifications, or Cursor clipboard
state. Global Cursor installs register `codegraph` and `gpu-broker` in
`~/.cursor/mcp.json` by default; use `--no-mcp` to opt out.

## Stable commands

Keep these public producer commands and their CLI behavior compatible:

```bash
./install.sh [options] TARGET
./scripts/build-codex-plugin.py [--check]
./scripts/validate.sh
python3 scripts/eval-teamwork.py [options]
```

`python3 scripts/run-teamwork-live-eval.py` records bounded live trajectories.
`python3 scripts/run-installed-teamwork-live-eval.py` wraps that recorder with
an isolated Codex installation, an installed-file manifest, and external
semantic review. Both supplement deterministic evaluation; neither proves
automatic skill activation or Cursor/Claude Code parity. The installed canary
isolates its user home, not an arbitrary supplied worktree, so use a clean Git
snapshot when legacy local surfaces could affect the result.

Thin entrypoints may delegate to `scripts/teamwork_tooling/` or
`scripts/install/`, but callers should not need to know those internal module
boundaries. Python producer modules remain standard-library-only. Installation
is orchestrated by Bash and standard-library Python helpers.

## Change owners

| Change | Primary owner | Required companion evidence |
| --- | --- | --- |
| One capability's trigger, behavior, authority, or output | Its `skills/<capability>/SKILL.md` | Focused capability and boundary case; no shared behavior reference |
| Skill inventory or removal | `skills/` plus installer and bundle producers | Inventory discovered from canonical sources; real previous-release upgrade fixture |
| Host agent role or model profile | `templates/*-agents/` | Render/profile validation for every affected host; no runtime skill dependency |
| Notifications | `hooks/` and notification configuration producers | Hook manifest validation and focused hook tests |
| Install targets, destinations, policy blocks, or profiles | `install.sh` and `scripts/install/` | Isolated-home and project-context fixtures |
| Codex Marketplace bundle, catalog, activation, or cache bootstrap | `scripts/build-codex-plugin.py`, `.agents/plugins/marketplace.json`, Codex installer runtime, and generated bundle | Bundle `--check`, cache installation, isolated bootstrap, and legacy-protection checks |
| Package validation | `scripts/validate.sh` and validation modules | Focused harness tests including a representative failing mutation |
| Deterministic or semantic evaluation | Evaluation producers and `evals/teamwork/` | Schema, rubric, and mutation-sensitive checks |
| Live trajectory recording | Live-eval producers and fixtures | Isolated bounded runner checks; claims limited to the observed treatment |
| Versioned public surface | `VERSION`, plugin manifests, changelogs, and public docs | Full validation and repository release policy |

## Anti-drift rules

- Keep behavior in the owning skill. Reject cross-skill instruction loads,
  shared behavior references, and router-like orchestration.
- Discover skill inventory from canonical directories in producers and tests.
  Release-facing docs may name the current ten public skills and must be updated
  with an inventory change rather than becoming a second runtime source of truth.
- Change canonical producers, never generated copies or local install roots.
  Regenerate the tracked Marketplace bundle rather than editing it by hand.
- Keep templates one-way: they may be installed into host agent configuration,
  but skills and canonical behavior must never depend on installed templates.
- Preserve stable command paths, arguments, exit behavior, and destinations.
  Internal extraction remains invisible to callers.
- Keep modules coarse and cohesive. Do not add generic utility buckets,
  permanent old/new modes, or duplicate inventory manifests.
- Add proof at the changed boundary. Static or fake-process checks must not be
  described as live user-visible model behavior.
- Test removed files against an actual previous release. A fixture copied from
  the candidate cannot prove owned stale-file cleanup or user-file protection.
- Treat ignored runtime memory and generated evidence as local by default. Do
  not publish them accidentally.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the contributor workflow.
