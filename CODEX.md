# Teamwork for Codex

Teamwork adds focused methods for collaborative convergence, external research,
unknown-cause debugging, planning, review, and
long-running convergence. Codex keeps local repository inspection and clear
authorized implementation on its native path, so ordinary work does not need an
Execute or router skill.

## Quick start: default Marketplace plugin

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Open a new Codex task and run:

```text
$teamwork-update
```

This is the default Codex installation path. Skills load from the plugin cache.
On first activation, `$teamwork-update` asks for the performance/cost profile
and independently offers managed CodeGraph and the local GPU Broker. It then
explains the agents, agent configuration, Teamwork-managed global policy,
notification choice, and verified legacy cleanup it proposes before approval.
The baseline completes without the optional managed capabilities. It does not copy skills to
`~/.agents/skills` or overwrite content whose ownership is uncertain.

Restart Codex after a routing change. If notifications are enabled, open
`/hooks` and trust the Teamwork `Stop` and `PermissionRequest` handlers
individually. Never use trust-all; the plugin intentionally cannot pretrust
hooks for you.

## Everyday use

Describe the outcome directly:

```text
Inspect this repository and implement the requested validation change.
Research the current provider options from official sources and cite the recommendation.
Brainstorm a lower-maintenance onboarding flow with me, then ask the most useful next question.
Decide the authentication boundary; explore only alternatives with real tradeoffs.
This public API could be synchronous, queued, or hybrid; a wrong choice forces costly client migration and the evidence conflicts. Help me decide.
Find the cause of this CI failure, fix it, and rerun the same failing path.
Turn the selected migration direction into an executable plan without changing files.
Review this diff against the requirements and direct evidence.
Keep working until the named check passes or a genuine blocker remains.
```

Codex natively reads local code, configuration, tests, logs, runtime output, and
Teamwork artifacts. A clear authorized edit or fix also stays native. Use
`$teamwork-explore` only for a distinct, read-only local evidence question; use
`$teamwork-research` only for external, current, multi-source, or
citation-backed research.

Before asking, Root inspects discoverable state and acts on safe, reversible
defaults. If one undiscoverable user-owned value is required, Root asks for that
exact gap once, pauses only dependent work, and resumes the same workflow.
Latent preferences or unformed intent that can materially change the outcome
enter Collaborate, which contributes and recommends before asking. Leaf roles
never ask or activate Collaborate; they return an exact gap or reclassification
signal to Root, and the same question is not repeated across roles or stages.

Use `$teamwork-collaborate` for natural dialogue, brainstorming,
stress-testing, question-before-action, or a consequential solution that is
still open. Challenge and adversarial search are Collaborate methods, not
public mode names. Use `$teamwork-plan` only after controlled Collaborate records
`acceptance: accepted`. Collaborate uses Explorer only for an unresolved local
constraint and sanitized external Research only for a named external/current
claim that can change the choice; it never runs both by default. It compares
2–3 real alternatives or records safe-path evidence, applies the needed
challenge/adversarial method, and keeps the user-decision frontier finite. It contributes synthesis,
candidate space, a decision map, or provisional recommendation before asking.
Its controlled transaction records `acceptance: pending`, `accepted`, or
`blocked`; persistence is not acceptance, and only `accepted` is Plan-ready.
Legacy-v1, old grill, Discussion, and Design records are Init/Update semantic migration inputs only. Independent
Plan Review runs only on user request or a named material risk gate.
Collaborate never implements. `$teamwork-debug` begins with a real failure and reproduction;
`$teamwork-review` does not edit the candidate and returns `ACCEPT`, `REVISE`, or `BLOCKED`;
`$teamwork-goal` persists an explicit objective, success signal, scope, budget,
and attempts before it iterates.

Collaborate selects `dialogue` or `brainstorm` from the requested
outcome and evidence, and never asks the user to name a mode. Open questions
stay in prose.
Only a genuine finite decision with two or three mutually exclusive options
uses Codex's native `request_user_input` surface when the host exposes it. The
live app-server probe selects Plan collaboration mode for bounded scenarios
because that preset exposes the native tool; open brainstorm stays in Default
mode and prose. Sustained pressure-testing follows the complete global ->
boundary -> detail map, places at most three independent decisions in one native
batch, serializes dependent decisions, and applies one semantic Collaborate
update after each answered batch before opening a dependent one.

In an initialized writable project, named Teamwork workflows persist reusable
checkpoints and results by default; `no files`, off-record, read-only, or
no-write overrides that default. One-shot explanations, casual fact questions,
and tiny native work create no standalone artifact. Collaborate and Goal
use case-v2 transactions. Substantive Research, Explore, Debug, Plan, Plan
Review, Review, mutating Init/Update, and qualifying execution checkpoints or
results write their selected case artifact. An active Goal owns execution
progress and suppresses duplicate execution artifacts. Substantive Explore
evidence uses the case evidence route; tiny/check-only reads remain unsaved.

Teamwork 6.0 is a hard cut for normal runtime: runtime writes use v2 case
bundles under `docs/teamwork/cases/c-<64hex>/`, where
Collaborate, Plan, Research, Explore evidence, Debug, Review, Goal, and execution results attach
to one case. legacy-v1 is not a compatible runtime mode. Init/Update may read
legacy-v1 and old grill/Discussion/Design records only as semantic migration
input during an exact one-time project-root migration. Update/install alone
never claims to migrate, rewrite, or delete existing `docs/teamwork`; the
cold-archive and restore-drill gates remain.

Research, Explore, Debug, Plan, and Review require their owning leaf. If the
host cannot provide that capability, the workflow returns capability-blocked
instead of falling back to Root or another role. Collaborate and Goal remain
Root-owned.

Collaborate chooses its search strategy from the request and evidence. It uses
the internal read-only Designer for direction selection, a frozen-hypothesis
challenge, or a search-closure audit. It selects adversarial only when at least
two viable directions remain and costly or irreversible error or conflicting
evidence makes one challenge inadequate; “high-risk” or “complex” alone is
insufficient. `adversarial` forces the method and `standard` disables it. The
model states its reason and uses default `B=3` without another confirmation.
Every hypothesis then receives two fresh isolated Designer critics and two new
final auditors must both pass. Missing isolation, exhausted budget, or failed
closure returns an incomplete result whose controlled state remains `pending` or
becomes `blocked`; it cannot be `accepted` or Plan-ready. A passing chat
recommendation is not Plan-ready. Only a controlled Collaborate state with
`acceptance: accepted` may enter Plan.

For a clear authorized code change, work result-first: modify the canonical
owner, reuse existing patterns/built-ins/suitable dependencies, add the smallest
complete logic, and run proportional focused tests plus the claimed real path.
Each Worker self-verifies its slice. After Root integrates and seals one
candidate, an independent max Reviewer runs once only on user request or a named
material risk gate. Findings form one repair batch, with at most one delta
recheck per candidate.

Skill selection remains model behavior rather than a deterministic Teamwork
router, so invoke a skill by name when exact selection is important. Codex still
owns native Plan mode, tools, browser and MCP access, permissions, agent
coordination, and the final response. Sustained Collaborate intent plus a
substantive synthesis, candidate space, or decision map and an unresolved
question or unaccepted direction defaults to one semantic checkpoint after
reading `docs/teamwork/index.json`: v6 writes the selected case manifest and
`live/collaborate.md` through case transactions. Frozen legacy-v1, old grill,
Discussion, and Design records stay readable only as Init/Update migration
inputs. Unchanged state is a no-op.
Collaborate never stores a transcript or substitutes a report/conclusion; `no
files`, off-record, read-only, or no-write wins.

## Agents and profiles

Full setup installs nine roles: Researcher, Explorer, Debugger, Designer,
Planner, Worker, Writer, Plan Reviewer, and Reviewer. Codex uses them only when
separate context, standalone document writing, or genuinely independent work is
worthwhile; the main task remains responsible for scope and integration. The
default dispatch is one child, the everyday ceiling is four, and five to eight
children are reserved for explicit adversarial or release work when the host
supports them. No subagent is required for routine local inspection or
implementation. Writer uses
a simple model and a frozen bounded brief for standalone project/product docs,
README/guide/architecture docs, change and release notes, and Teamwork runtime
artifacts. It may draft, organize, summarize, translate, and polish,
but must not research, invent, paraphrase, or change frozen facts, citations,
decisions, authority, status, or acceptance; missing route/readback fails closed
as unsaved. Code, comments, docstrings, tests, schemas, manifests,
machine config, and inline config text remain with implementation owners. The recommended and currently verified local Root
configuration remains user-controlled. The installer
configures only subagent profiles and routing; it does not set Codex's Root
main-task default.

Codex profiles are exact:

| Profile | Researcher | Explorer | Debugger | Planner | Worker | Writer | Designer | Plan Reviewer | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `performance-first` | Terra / `high` | Terra / `high` | Sol / `high` | Sol / `high` | Terra / `high` | Luna / `high` | Sol / `high` | Sol / `high` | Sol / `max` |
| `cost-first` | Terra / `high` | Luna / `high` | Terra / `high` | Terra / `high` | Luna / `xhigh` | Luna / `high` | Terra / `high` | Terra / `high` | Sol / `high` |

The split follows role behavior: Terra balances speed and quality for routine
evidence and bounded implementation; Luna handles cheap, bounded, mechanically
verifiable work; Sol owns unknown-cause diagnosis, quality-sensitive planning,
direction selection, and final acceptance. Reviewer stays on Sol/max in
`performance-first` until a same-case A/B supports the lower-cost xhigh candidate.

Catalog readiness proves that a configured model/effort exists, not that a
formal custom-agent dispatch preserved isolation and provenance. Run a live
spawn canary after Codex changes, especially for Luna-backed roles.

For checkout-based installs, choose `cost-first` when lower-cost models should
handle the roles where that profile permits it:

```bash
./install.sh codex --profile cost-first
```

`./install.sh --help` lists supported targets and profiles. v6 keeps retired
public names `$grill-me`, `$teamwork-discuss`, and `$teamwork-design`
unavailable; use `$teamwork-collaborate` instead, with no alias. Migration removes only exact
Teamwork-owned legacy Grill/Discuss/Design/Router/Execute and legacy-role
files. Modified or unmarked copies are preserved and stop automatic replacement.
legacy-v1 project memory is migration input only; no install or update performs
or claims live cutover.
Readiness confirms installed configuration, not that Codex will spawn a
particular agent for a natural-language request. Subagents do not send Teamwork
completion or permission notifications.

## Initialize one project

Ask `$teamwork-init` to set up the selected repository, or use a checkout:

```bash
./install.sh --project-root /path/to/project init-project
```

Initialization changes only that project. It establishes Teamwork-managed
project instructions, memory entry points, and ignore rules, and asks whether
to initialize local CodeGraph context when the CLI is available and no index
exists. It never asks for the global profile or installs GPU Broker. It does not refresh global skills, agents, policy,
routing, or notifications, and it does not install skills or agents inside the
repository. Run `$teamwork-update` separately when the global Codex setup needs
refreshing.

## Update the Marketplace installation

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Then open a new task and run `$teamwork-update`. It checks the Marketplace
catalog and cache, activation marker, agents, routing, policy, notifications,
saved install preferences, optional capability readiness, and verified legacy
files before refreshing the managed setup. Valid choices are inherited; only
missing, invalid, explicitly reconfigured, or newly introduced choices are
asked again. Restart Codex
after a routing change and repeat the manual `/hooks` review when requested.

## Checkout installation

The Marketplace plugin is the default for Codex users. The repository installer
remains useful for local development and for users who do not use the
Marketplace:

```bash
./install.sh all
./install.sh --dependencies all        # optional full CodeGraph + GPU Broker
./install.sh codex
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
./scripts/check-update.sh --readiness
```

Use `./install.sh all` for the mandatory baseline on every platform,
`./install.sh --dependencies all` for the optional full managed-capability
setup, a platform command for a narrower installation, and `--link` only while
developing from the checkout. Managed-capability flags are valid only with
`codex`, `all`, `update`, and `plugin-codex-bootstrap`; narrower targets reject
them because they do not own dependency lifecycles.
The installer preserves unrelated configuration and stops rather than
overwriting an unknown same-name file. If Marketplace activation already
exists, use `$teamwork-update` instead of creating duplicate checkout skills.

## Troubleshooting

- **The plugin is installed, but agents or routing are missing:** open a new
  task, run `$teamwork-update`, review the proposed first enablement, and
  approve it.
- **The plugin cache or catalog is stale:** run the Marketplace update sequence
  above, open a new task, and run `$teamwork-update` again.
- **Readiness is green but notifications do not run:** restart Codex, inspect
  `/hooks`, and trust only Teamwork `Stop` and `PermissionRequest`. Static
  readiness cannot perform or verify this host-owned action.
- **Initialization did not update global Teamwork:** this is intentional in v4.
  Use `$teamwork-update` or `./install.sh all` for the global installation.
- **A request did not select the expected skill:** invoke that skill explicitly.
  Installed configuration cannot make natural-language selection deterministic.
- **Installation stops on an existing file:** inspect that specific conflict;
  never delete an entire `.agents` or `.codex` directory to bypass the check.

See the [main README](README.en.md) for the capability overview and the
[changelog](CHANGELOG.en.md) for upgrade details.
