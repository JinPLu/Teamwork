# Teamwork Repository Architecture

Teamwork is a Codex-first skill package with Cursor and Claude Code adapters.
Version 6 keeps each skill self-contained, makes Collaborate and durable workflow
handoffs first-class, and leaves ordinary local inspection and clear authorized
implementation to the host. The repository separates authored capability
sources from producer tooling and from generated or local install surfaces.

## Canonical tree

```text
skills/
  <capability>/SKILL.md          self-contained user-facing capability
  <capability>/references/       only the owning skill's advanced method
  <capability>/agents/openai.yaml optional host interface metadata
templates/                       nine-role install-time host-agent adapters
hooks/                           authored notification runtime and hook manifest
evals/teamwork/
  cases/                         deterministic behavior cases
  live-cases/                    bounded live trajectory cases
  rubrics/                       semantic review criteria
  ledgers/                       accepted/rejected evaluation records
  outputs/                       compact authored output fixtures
scripts/
  build-codex-plugin.py          Marketplace bundle producer/checker
  plugin-runtime-root.py         Marketplace/source runtime resolver with integrity checks
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
.teamwork-runtime-integrity.json generated inside Marketplace runtime only
VERSION, CHANGELOG*, README*     authored release and public docs
docs/architecture.md             this architecture contract
CONTRIBUTING.md                  contributor entrypoint
```

The public capability inventory is exactly nine: `teamwork-collaborate`,
`teamwork-debug`, `teamwork-explore`, `teamwork-goal`, `teamwork-init`,
`teamwork-plan`, `teamwork-research`, `teamwork-review`, and
`teamwork-update`. There are exactly four public skill-owned advanced
references: Collaborate's adversarial-search, Debug's runtime-diagnosis,
Research's deep-research, and Review's strict-review. Collaborate owns the
former public Design method; the Designer role remains read-only and is not a
public skill surface.

Host adapters have exactly nine roles—Researcher, Explorer, Debugger, Designer,
Planner, Worker, Writer, Plan Reviewer, and Reviewer—under each of the Codex,
Cursor, and Claude Code template directories. Writer uses the simplest model
profile and a frozen bounded brief for standalone document drafting, rewriting,
organizing, summarizing, translation, polishing, and Teamwork runtime artifacts.
It must not research, invent or change facts, citations, decisions, authority,
status, or acceptance. Code, code comments, docstrings, tests, schemas,
manifests, machine config, and inline config text remain with implementation
owners. Designer remains read-only
and may receive one direction-selection, frozen-hypothesis challenge, or
search-closure audit assignment; Root retains orchestration and final acceptance.

The following are sinks, not package sources:

- `.agents/` except `.agents/plugins/marketplace.json`, `.codex/`, `.cursor/`,
  and `.claude/` may contain generated or legacy local installations. Global Cursor
  installs may write `~/.cursor/mcp.json` and a Teamwork ownership sidecar; project
  init writes `.cursor/rules/` and optional project `.cursor/mcp.json` only with
  explicit `--cursor-mcp` consent. Edit `skills/`, `templates/`, or the owning
  producer instead of an installed copy.
- `docs/teamwork/` is local Teamwork runtime memory. In an initialized writable
  project, named Teamwork workflows persist reusable checkpoints and completion
  results by default unless the user says `no files`, off-record, read-only, or
  no-write. One-shot explanations, casual fact questions, and tiny native work
  do not force an extra workflow artifact. Writer authors ordinary artifacts
  from frozen bounded packets without paraphrasing, filling gaps, or changing
  frozen facts, citations, decisions, authority, status, or acceptance; durable workflow
  artifacts are registered only through the schema-selected transaction route.
  In v6 normal runtime, Collaborate, Research, Debug, Plan, Plan Review,
  Review, Goal, mutating Init/Update, and qualifying terminal execution
  handoffs write case-v2 transactions/case artifacts. legacy-v1 is not a
  compatible runtime mode; legacy-v1, old grill, Discussion, and Design records
  are read only as Init/Update semantic migration inputs. Active Goal owns
  execution progress and forbids a duplicate execution artifact. Ordinary completion workflows share
  `active.results` so their companions can coexist; `active.report` remains for
  non-workflow report pointers. Explore does not create a standalone report; its
  evidence is folded into the consuming artifact or answer.

  Teamwork 6.0 is a hard cut to case-v2 for normal runtime. Initialized
  projects use case-bundle memory: a case manifest under
  `docs/teamwork/cases/c-<64hex>/manifest.json` owns live collaboration,
  accepted decision, plan, evidence, review, goal, and result slots under the
  same case directory. One transaction may not touch both v1 and v2 trees.
  Unknown, hybrid, stale, or partially migrated state fails closed before write.
  Init/Update project-root migration is exact and one-time, and update/install
  alone does not migrate project memory or claim migration success.
- Temporary live outputs, homes, caches, logs, and build results are evidence or
  scratch state. They must not become package inputs.

| Workflow | Runtime artifact |
| --- | --- |
| Collaborate | v2 case live collaborate and decision slots; accepted Collaborate is the public Plan gate; legacy-v1, old grill, Discussion, and Design remain Init/Update migration inputs only |
| Research | v2 case evidence artifact with claim head and monotonic status |
| Plan | v2 case plan slot and plan history with monotonic status |
| Debug | v2 case evidence/result artifact; hypothesis-first diagnosis starts from failure and reproduction |
| Plan Review / Review | v2 case review/delta artifact with monotonic status; persistence is not acceptance |
| Goal | v2 case live goal with monotonic attempts/progress while executing |
| Native / Worker execution | terminal execution handoff/result only with an explicit real consumer and no active Goal |
| Mutating Init / Update | receipt; update/install alone never migrates project memory |
| Explore | no standalone report; evidence is folded into its consumer |

## Dialogue and persistence

Root owns live dialogue, dispatch timing, user-facing claims, decisions,
authority, and acceptance. Leaf roles return bounded packets; Writer is a
low-cost disposable leaf that receives a frozen brief and never becomes
continuity state. The durable source of truth is the transaction record
inspect/CAS/journal/atomic apply/readback plus the workflow artifact, not the
identity of the Writer that drafted it.

| Persistence disposition | User-visible outcome | Ordering rule |
| --- | --- | --- |
| Checkpoint | A reusable intermediate artifact that later workflow steps may consume | Dependent work waits until transaction readback succeeds |
| Completion companion | A durable companion to an already determined result packet | Root freezes the result before dispatch, may overlap only answer-invariant delivery work, and joins before claiming saved/durable |
| None | Native dialogue answer or local work without a standalone durable artifact | No Writer transaction and no saved/durable claim |

Feedback loops stay reference-local: v6 workflows use case transactions/case
artifacts. legacy-v1 generic and specialized transaction routes are migration
inputs only where Init/Update explicitly owns semantic migration. Before any
`case-apply` or legacy `artifact-apply`, inspection/schema work is preparatory
only; interruption before apply/readback provides no durable claim.

Collaborate schema v1 writes the three explicit acceptance states `pending`,
`accepted`, and `blocked`; persistence is not acceptance and only `accepted` is
Plan-ready. Frozen legacy-v1, old grill, Discussion, and Design records stay
readable as Init/Update migration inputs only; archives are never rewritten
merely to upgrade schema. Collaborate uses a common lifecycle plus a
`dialogue|brainstorm` discriminator and selects the mode from natural intent and
evidence rather than asking for a mode name. Sustained pressure-testing follows
the strict global -> boundary -> detail decision map, limits each current batch
to three mutually independent decisions, and keeps dependent decisions serial.
One answered batch is one
semantic transaction unit: all resolutions and the next valid frontier change
are applied together before a dependent batch opens.

Persistence behavior is checked on real command paths. v2 probes run
`case-inspect` → `case-schema` → `case-apply` → `case-inspect` against case
bundles. legacy-v1 generic and Collaborate probes are migration-path checks, not
normal runtime compatibility. Positive and negative persistence cases cover
specialized routing, generic routing, semantic no-ops, legacy read-only
migration inputs, Goal/execution deduplication, and write overrides.

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
them. Generated Marketplace runtimes carry `.teamwork-plugin-runtime` and
`.teamwork-runtime-integrity.json`; `scripts/plugin-runtime-root.py` verifies the
marker, `VERSION`, Codex manifest hash, and regular single-link runtime file
hashes before reporting a runtime root. Source checkouts omit the marker and are
accepted only through source-manifest consistency.

## Capability boundaries

Each `skills/<capability>/SKILL.md` contains the behavior needed to use that
capability. Skills do not invoke other skills as subroutines, load another
skill's instructions, depend on shared behavior references, or carry
skill-local scripts. Deterministic package mechanics belong under top-level
`scripts/`; optional `agents/openai.yaml` files contain interface metadata only.

This keeps the main boundaries visible:

- the host natively inspects local repositories, configuration, tests, logs,
  runtime state, and artifacts, and natively implements clear authorized work;
- Root owns request readiness: inspect and act when state is discoverable or a
  safe reversible default applies; ask once for one exact undiscoverable
  user-owned required value, pause only dependent work, and resume the same
  workflow; or enter Collaborate for latent preferences and unformed intent that
  materially change the result. Leaves never ask or activate Collaborate. They
  return one exact gap or an explicit reclassification signal to Root, with one
  active gap and no duplicate question across roles or stages;
- Explore answers a distinct local read-only evidence question; Research is only
  for external, current, multi-source, or citation-backed investigation;
- Collaborate owns natural dialogue, brainstorming, sustained questioning,
  stress-testing, question-before-action, and unsettled consequential solution
  convergence. Explorer is dispatched only for an unresolved local constraint,
  and Research only for a named sanitized external/current claim that can change
  the decision; neither is mandatory and they do not run together by default.
  Internal Designer integrates only the evidence actually needed. A real
  trade-off gets two or three alternatives; one safe path gets explicit evidence
  and exclusions. Collaborate uses challenge/adversarial methods for
  consequential direction work. It uses a budget-bounded hypothesis search only when multiple
  viable directions plus costly error or conflicting evidence make one challenge
  inadequate; `adversarial` forces the method and `standard` disables it. The
  default budget is 3 without another confirmation. Each actual hypothesis gets
  two fresh isolated Designer critics, materially revised hypotheses consume a
  new trial, and two new final auditors must both pass. Missing isolation or
  closure leaves the controlled Collaborate state `pending` or `blocked`; it
  never produces an `accepted`, Plan-ready result. All strategies use the same
  finite user-decision frontier and controlled v2 case transaction. Persistence
  is not acceptance, and only `accepted` may enter Plan. Sustained
  pressure-testing shows a global map first, then boundary, then detail; batches
  only independent material questions; and serializes dependent questions;
- Plan turns an `accepted` Collaborate handoff into executable steps; independent
  Plan Review runs only on user request or a named material risk gate. Each
  Worker self-verifies its slice. After integration, a sealed candidate receives
  one independent max `ACCEPT`, `REVISE`, or `BLOCKED` Review only on user request
  or a named material risk gate; findings are repaired as one batch and each
  candidate gets at most one delta recheck;
- Debug constrains unknown-cause failure work to real failure, reproduction,
  discriminating evidence, the authorized narrow fix, and the same-path rerun;
- Goal adds explicit durable objective, success signal, scope, protected
  boundaries, budget, and attempt state; Init changes one project's context
  only, while Update changes global Teamwork-managed installation state only.

Research, Explore, Debug, Plan, and Review require the corresponding owning
leaf. Missing host support is capability-blocked; Root does not impersonate a
missing leaf or reroute the workflow to a different role. Collaborate and Goal
remain Root-owned. Default dispatch is one child, ordinary work is capped at
four, and five to eight children are reserved for explicit adversarial or
release work when the host supports that concurrency.

There is no Teamwork router or generic Execute skill. `execution` is only a
terminal artifact kind with a named consumer, never a routing capability. Host
skill discovery chooses a capability directly; exact selection remains model
behavior. Migration recognizes only exact Teamwork-owned legacy Grill,
Discuss/Design, Router/Execute, and legacy-role files so it can remove them
safely. Modified or unmarked copies block replacement and remain untouched;
recognition creates no alias or callable compatibility surface.

## Method attribution

Teamwork adopts Superpowers' hard gate, options, and specification self-check
ideas. Its default one-pass challenge and finite decision frontier are locally
tailored Teamwork convergence rules. The adversarial Collaborate strategy
adopts a bounded hypothesis-taxonomy, fresh-critic, and dual-closure-audit method
without copying a discussion-only terminal contract or claiming to reproduce
another workflow wholesale.

## Templates are install-time adapters

Files under `templates/` are authored inputs that installers render or copy into
host-native agent definitions. They are not runtime skill prompts, not a shared
behavior library, and not a fallback source for a `SKILL.md`. No skill may read
a template to acquire rules. Once installed, the host may use the resulting
agent configuration in its normal way; the canonical Teamwork capability still
lives in its own `SKILL.md`.

The recommended local Codex Root configuration remains user-controlled. The
installer configures only subagent profiles and routing; it does not set the
Root main-task default. Codex renders the nine roles with exact profile
mapping. performance-first uses Terra/high for Researcher, Explorer, and Worker;
Luna/high for Writer; Sol/high for Debugger, Designer, Planner, and Plan
Reviewer; and Sol/max for Reviewer. cost-first uses Terra/high for Researcher,
Debugger, Designer, Planner, and Plan Reviewer; Luna/high for Explorer and
Writer; Luna/xhigh for Worker; and Sol/high for Reviewer. Terra is the routine
balance tier, Luna is limited to bounded and mechanically verifiable work, and
Sol owns ambiguity and acceptance gates. Cursor and Claude Code templates remain
host-native adapters; this does not promise the Codex reasoning-effort mapping
on those hosts. Catalog readiness is not behavioral dispatch proof; run a live
isolation/provenance canary after Codex changes, especially for Luna-backed roles.

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
state. The `update` target always owns the Teamwork baseline and separately owns
two optional managed capability lifecycles. Desired profile, CodeGraph, and GPU
Broker choices live in the Teamwork-owned schema-v1 receipt at
`${XDG_STATE_HOME:-~/.local/state}/teamwork/install-preferences.json`; desired,
observed, and last-action state remain distinct so an opt-out is not reported as
a failed install. CodeGraph and the explicitly resolved local GPU Broker
companion are preflighted and refreshed independently. Shell entrypoints remain
noninteractive: host skills ask, then pass deterministic flags. Existing Cursor
MCP behavior remains a compatibility surface rather than a new calibration
question. `--dependencies` enables both managed capabilities,
`--no-dependencies` disables both, and the granular flags select either one.
Only the `codex`, `all`, `update`, and `plugin-codex-bootstrap` lifecycle owners
accept those overrides; narrow targets reject them before recording preferences
or writing global surfaces.

## Instruction footprint

Release-blocking runtime volume budgets apply to surfaces that a host can
actually load together. `scripts/teamwork_tooling/instruction_footprint.py` is
their sole authority; validation must not recreate the removed policy 365,
Skill 975, role 260, or AGENTS/Skill line-count shadow thresholds. The fenced
host-template checks remain structural gates, not a second volume budget.
The current `instruction_footprint.py --json` result reports:

| Real loading surface | Current words | Word limit |
| --- | ---: | ---: |
| Resident host policy | Codex 362; Cursor 365; Claude 357 | 430 each |
| One Skill | 976 | 1,150 |
| One Skill plus its own on-demand reference | 1,569 | 1,850 |
| One role template | 257 | 330 |
| Skill discovery catalog | 490 | 650 |
| Project instruction block | 46 | 220 |
| Repository instructions | 610 | 750 |
| Runtime memory README | 272 | 320 |
| Runtime memory index | 145 | 200 |
| Worst initialized Root path | 2,887 | 3,300 |
| Worst leaf path | 2,727 | 3,200 |
| Worst repository Root path | 3,451 | 3,900 |

The three-host, 49-surface union (14,103 words) and the nine-Skill aggregate
(6,366 words) are telemetry, not release-blocking proxies for a context that no
host co-loads. The same authority still enforces the exact nine-Skill inventory
and rejects cross-Skill instruction loads or dependency cycles.

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
| Versioned public surface | `VERSION`, plugin manifests, changelogs, public docs, and root `.gitignore` runtime-memory entries | Focused consistency/JSON/diff checks plus release-policy validation when packaging |

## Anti-drift rules

- Keep behavior in the owning skill. Reject cross-skill instruction loads,
  shared behavior references, and router-like orchestration.
- Discover skill inventory from canonical directories in producers and tests.
  Release-facing docs may name the current nine public skills and must be updated
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
