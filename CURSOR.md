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
- "Diagnose why this test started failing, then verify the fix on the same path."
- "Turn the selected direction into an executable plan, but do not edit files."
- "Review this diff against the requirements and direct evidence."
- "Keep working until the named checks pass."

Cursor natively handles local repository, configuration, test, log, runtime,
and artifact inspection. Clear authorized implementation also stays native.
Use `teamwork-explore` for a distinct read-only local evidence question and
`teamwork-research` only for external, current, multi-source, or citation-backed
research. Use `teamwork-design` while the solution is unsettled and
`teamwork-plan` after a direction has been selected. Design uses Explorer only
for an unresolved local constraint and sanitized Research only for a named
external/current claim that can change the choice; it never runs both by default.
It compares 2–3 real
alternatives or records safe-path evidence, makes one challenge pass, and keeps
the decision frontier finite. Its controlled transaction produces the durable
Design artifact before Plan; independent Plan Review runs only on user request
or a named material risk gate. It never silently
authorizes implementation.

Debug starts from a real failure and reproduction. Plan turns a selected
direction into owned executable steps; Review is read-only and returns
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

An ordinary "ask me first" request asks questions without writing files. In an
initialized writable project, an explicit `grill-me`, save, resume, or record
request uses the transaction to update only `docs/teamwork/discussion/current.md`.
An independently major public/installable, migration/release, permission,
security, data, destructive, or cross-platform boundary opens the record
automatically. Within one scope, only creation, semantic decision/frontier
change, and close/supersede persist; unchanged state is a no-op. "No files" or
off-the-record keeps it in the conversation.

## Initialize a project

```bash
./install.sh --project-root /path/to/project init-project
```

Initialization changes only that repository. It establishes Teamwork-managed
project instructions, memory entry points, ignore rules, and CodeGraph context
when available. It does not refresh global skills, agents, policy, routing, or
notifications, and it does not copy Teamwork skills or agents into the project.
Use `teamwork-update` or `./install.sh all` separately for a global refresh.

## Agents

The installer adds eight Cursor roles: Researcher, Explorer, Debugger, Designer,
Planner, Worker, Plan Reviewer, and Reviewer. Teamwork may use them when work
splits into genuinely independent scopes. The main agent owns scope,
integration, and the final result; routine work does not require delegation.
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
