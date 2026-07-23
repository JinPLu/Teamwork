# Teamwork for Cursor

Teamwork gives Cursor focused methods for external research, consequential
design, unknown-cause debugging, planning, review, and long-running convergence.
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
- "Design the migration boundary and recommend among the real alternatives."
- "This public API could be synchronous, queued, or hybrid; a wrong choice forces costly client migration and the evidence conflicts. Help me decide."
- "Diagnose why this test started failing, then verify the fix on the same path."
- "Turn the selected direction into an executable plan, but do not edit files."
- "Review this diff against the requirements and direct evidence."
- "Keep working until the named checks pass."

Cursor natively handles local repository, configuration, test, log, runtime,
and artifact inspection. Clear authorized implementation also stays native.
Use `teamwork-explore` for a distinct read-only local evidence question and
`teamwork-research` only for external, current, multi-source, or citation-backed
research. Use `teamwork-design` while the solution is unsettled and
`teamwork-plan` only after the controlled Design records `acceptance: accepted`. Design uses Explorer only
for an unresolved local constraint and sanitized Research only for a named
external/current claim that can change the choice; it never runs both by default.
It compares 2–3 real
alternatives or records safe-path evidence, makes one challenge pass, and keeps
the decision frontier finite: it shows the global map first, batches only
independent material decisions, and asks dependent decisions in later turns. Its controlled transaction records
`acceptance: pending`, `accepted`, or `blocked`; persistence is not acceptance,
and only `accepted` is Plan-ready. Legacy v1/v2 records are read as `accepted`
for compatibility. Independent Plan Review runs only on user request
or a named material risk gate. It never silently
authorizes implementation.

Design chooses its search strategy from the request and evidence. It selects
adversarial only when at least two viable directions remain and costly or
irreversible error or conflicting evidence makes one challenge inadequate;
“high-risk” or “complex” alone is insufficient. `adversarial` forces the method
and `standard` disables it. The model states its reason and uses default `B=3`
without another confirmation. Every hypothesis then receives two fresh isolated
Designer critics and two new final auditors must both pass. Missing isolation,
exhausted budget, or failed closure returns an incomplete result whose controlled
state remains `pending` or becomes `blocked`; it cannot be `accepted` or
Plan-ready. A passing chat recommendation is not Plan-ready. Only a controlled
Design with `acceptance: accepted` may enter Plan.

Debug starts from a real failure and reproduction. Plan turns an accepted
Design into owned executable steps; Review does not edit the candidate and returns
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

In an initialized writable project, named Teamwork workflows persist reusable
artifacts by default; `no files`, off-record, read-only, or no-write overrides
that default. Ordinary clarification or chat, one-off native work, and clear
code implementation requests do not force an extra workflow artifact. Grill,
Design, and Goal use specialized transactions. Research, Debug, Plan, Review,
and mutating Init/Update use the generic artifact transaction. Explore creates
no standalone report; its evidence is folded into the consuming artifact or
answer.

An ordinary "ask me first" request stays in the conversation and does not
trigger Grill or persistence. Once Grill is named or entered, an existing Grill
is resumed, or an independently major public/installable, migration/release,
permission, security, data, destructive, or cross-platform boundary invokes it,
the specialized transaction updates only `docs/teamwork/discussion/current.md`
by default. Within one scope, only creation, semantic decision/frontier
change, and close/supersede persist; unchanged state is a no-op. New records use
schema v2 `frontier` / `current_batch` state. `no files`, off-record, read-only,
or no-write keeps it in the conversation.

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
Writer uses Cursor's simple `composer-2.5-fast` profile and a frozen bounded
brief for standalone docs and runtime artifacts. It may draft, rewrite,
organize, summarize, translate, and polish, but must not research, invent or
change facts, citations, decisions, authority, status, or acceptance. Code
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
