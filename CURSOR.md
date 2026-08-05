# Teamwork for Cursor

Teamwork gives Cursor focused methods for collaborative convergence, external
research, unknown-cause debugging, planning, review, and
long-running convergence.
Cursor keeps local code inspection and clear authorized implementation on its
native path and still controls edits, shell commands, MCP and browser tools,
permissions, and model behavior. There is no generic Execute or router skill.

## Quick setup

From this checkout, install Teamwork for every supported host:

```bash
./install.sh all
```

For Cursor only:

```bash
./install.sh cursor
./install.sh cursor-policy-copy
```

Teamwork registers `codegraph` and `gpu-broker` in `~/.cursor/mcp.json` during
`cursor` and `all` installs. Use `./install.sh --no-mcp cursor` to skip MCP
registration, or `./install.sh cursor-mcp` to refresh MCP entries alone. Enable
new servers in **Cursor Settings → MCP** when prompted; writing `mcp.json` does
not auto-activate them.

Paste the copied policy into **Cursor Settings → Rules → User Rules**.
If clipboard copying is unavailable, run `./install.sh cursor-policy` and copy
the printed block. The installer cannot complete or verify this Cursor-owned
setting.

The default `performance-first` profile balances everyday work with deeper
review. To favor lower-cost model choices:

```bash
./install.sh cursor --profile cost-first
```

Run `./install.sh --help` for advanced options. Use `--link` only when an
installation should track this checkout during Teamwork development.

## Everyday use

Ask for the outcome in ordinary language:

- "Inspect this repository and implement the requested validation change."
- "Research the current provider options from official sources and cite them."
- "Brainstorm a lower-maintenance onboarding flow with me, then ask the most useful next question."
- "Decide the migration boundary and recommend among the real alternatives."
- "This public API could be synchronous, queued, or hybrid; a wrong choice forces costly client migration and the evidence conflicts. Help me decide."
- "Diagnose why this test started failing, then verify the fix on the same path."
- "Turn the selected direction into an executable plan, but do not edit files."
- "Review this diff against the requirements and direct evidence."
- "Keep working until the named checks pass."

Cursor natively handles local repository, configuration, test, log, runtime,
and artifact inspection. Clear authorized implementation also stays native.
Use `teamwork-explore` for a distinct read-only local evidence question and
`teamwork-research` only for external, current, multi-source, or citation-backed
research. Use `teamwork-collaborate` when the user explicitly wants to discuss,
design, plan, brainstorm, compare, or think together; when a material downstream
choice belongs to the user; or when unclear intent needs guided clarification.
Risk, security, migration, publicity, and complexity are not separate triggers.

Before asking, Root inspects discoverable state and acts on safe, reversible
defaults. If one undiscoverable user-owned value is required, Root asks for that
exact gap once, pauses only dependent work, and resumes the same workflow.
Latent preferences or unformed intent that can materially change the outcome
enter Collaborate, which contributes and recommends before asking. Leaf roles
never ask or activate Collaborate; they return an exact gap or reclassification
signal to Root, and the same question is not repeated across roles or stages.

Challenge and adversarial search are Collaborate methods, not public mode names.
Use `teamwork-plan` only after controlled Collaborate records
`acceptance: accepted`. Collaborate uses Explorer only for an unresolved local
constraint and sanitized Research only for a named external/current claim that
can change the choice; it never runs both by default. Research and Explore
gather evidence and return it to the same discussion; they do not own the user
choice. Collaborate maps knowledge-space ambiguity before asking and contributes
synthesis, useful options, a decision map, or provisional recommendation before
any question that materially changes the next step. Its controlled
transaction records `acceptance: pending`, `accepted`, or `blocked`;
persistence is not acceptance, and only `accepted` is Plan-ready. Legacy-v1, old
grill, Discussion, and Design records are Init/Update semantic migration inputs
only. Independent Plan
Review runs only on user request or a named material risk gate. It never
silently authorizes implementation.

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

Debug starts from a real failure and reproduction. Plan turns an accepted
Collaborate handoff into owned executable steps; Review does not edit the candidate and returns
`ACCEPT`, `REVISE`, or `BLOCKED`; Goal persists an explicit objective, success
signal, scope, budget, and attempts before it iterates. Clear authorized code
work remains result-first: change the canonical owner, reuse existing
patterns/built-ins/suitable dependencies, add the smallest complete logic, and
prove each Worker slice with proportional focused tests plus the real path.
After Root integrates and seals one candidate, an independent max Review runs
once only on user request or a named material risk gate; findings form one repair
batch with at most one delta recheck per candidate.

Natural-language skill selection depends on Cursor and the active model. Name a
skill when exact selection matters. Accepting a design or plan does not grant
permission to edit files or change external state.

Collaborate is one continuous adaptive discussion. It moves as needed among L1
Understand Intent, L2 Explore Together, and L3 Challenge and Converge; these are
not modes, skills, fixed depths, turn budgets, or mandatory phases. A
host-native choice surface is appropriate only when a finite answer materially
changes the next step. Independent questions can batch together, dependent
questions are serialized with a hard wait, and there is no workflow-wide
question, batch, or round cap. Explicit brainstorming, adversarial, stress-test,
or subagent methods must execute the real method or report capability-blocked.

In an initialized writable project, named Teamwork workflows persist reusable
checkpoints and results by default; `no files`, off-record, read-only, or
no-write overrides that default. One-shot explanations, casual fact questions,
and tiny native work create no standalone artifact. Substantive Collaborate,
Goal, Research, Explore, Debug, Plan, Plan Review, Review, mutating Init/Update,
and qualifying execution checkpoints or results write their selected case-v2
artifact. An active Goal suppresses duplicate execution artifacts. Substantive
Explore evidence uses the case evidence route; tiny/check-only reads remain unsaved.

Teamwork 6.0 is a hard cut for normal runtime: runtime writes use v2 case
bundles under `docs/teamwork/cases/c-<64hex>/`, where
Collaborate, Plan, Research, Explore evidence, Debug, Review, Goal, and execution results attach
to one case. legacy-v1 is not a compatible runtime mode. Init/Update may read
legacy-v1 and old grill/Discussion/Design records only as semantic migration
input during an exact one-time project-root migration. Update/install alone
never claims to migrate, rewrite, or delete existing `docs/teamwork`; the
cold-archive and restore-drill gates remain.

Research, Explore, Debug, Plan, and Review require their owning leaf. If Cursor
cannot provide that capability, the workflow returns capability-blocked instead
of falling back to Root or another role. Collaborate and Goal remain Root-owned.

For substantive Collaborate, read `docs/teamwork/index.json` and write the
selected case manifest plus `live/collaborate.md` through case transactions.
Writer updates one semantic document at the first substantive synthesis, every
semantic change, and the end: overall picture; decided items; open
discussion/evidence; and current recommendation or next step. Frozen legacy-v1,
old grill, Discussion, and Design records remain readable only as Init/Update
migration inputs. Unchanged state is a no-op. Collaborate never stores a
transcript or substitutes a report/conclusion; `no files`, off-record,
read-only, or no-write keeps it in the conversation.

## Initialize a project

```bash
./install.sh --project-root /path/to/project init-project
./install.sh --project-root /path/to/project --cursor-mcp init-project
```

Initialization changes only that repository. It establishes Teamwork-managed
project instructions, memory entry points, ignore rules, and CodeGraph context
when available. With `--cursor-mcp`, it also writes project `.cursor/rules/` for
CodeGraph and GPU Broker plus optional project `.cursor/mcp.json`. It does not
refresh global skills, agents, policy, routing, or notifications, and it does
not copy Teamwork skills or agents into the project. Use `teamwork-update` or
`./install.sh all` separately for a global refresh.

## Agents

The installer adds nine Cursor roles: Researcher, Explorer, Debugger, Designer,
Planner, Worker, Writer, Plan Reviewer, and Reviewer. Teamwork may use them when
work splits into genuinely independent scopes or standalone document writing.
Default dispatch is one child, everyday work is capped at four, and five to
eight children are reserved for explicit adversarial or release work when Cursor
supports that concurrency.
Writer uses Cursor's simple `composer-2.5-fast` profile and a frozen bounded
packet for standalone docs and runtime artifacts. It may draft, organize,
summarize, translate, and polish, but must not research, invent, paraphrase, or
change frozen facts, citations, decisions, authority, status, or acceptance;
missing route/readback fails closed as unsaved. Code
comments, docstrings, tests, schemas, manifests, machine config, inline config
text, and other code-coupled wording stay with implementation owners. The main agent owns scope, integration,
and the final result; routine work does not require delegation.
`performance-first` and `cost-first` select Cursor-native host templates; they
do not promise the Codex model or reasoning-effort mapping on Cursor.

## Updates and troubleshooting

Check the global installation:

```bash
./scripts/check-update.sh --readiness
```

Use `teamwork-update` for a guided global refresh, or run:

```bash
./install.sh all
```

Use `teamwork-init` only for one repository's instructions and context. If
readiness reports `cursor-policy-manual`, rerun
`./install.sh cursor-policy-copy` and paste the result into Cursor User Rules;
that manual action cannot be detected automatically.

Teamwork does not override Cursor permissions, MCP, browser, tests, or model
selection. It does not invent missing paths, ports, credentials, models,
commands, or execution modes. Readiness cannot prove the manual User Rules step
or deterministic skill selection. Cursor notification sounds remain
uninstalled because their local hook path has not been live-verified.

See the [main README](README.en.md) for the shared capability overview and the
[changelog](CHANGELOG.en.md) for upgrade details.
