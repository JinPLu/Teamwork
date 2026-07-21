@AGENTS.md

# Teamwork for Claude Code

Teamwork adds focused methods for external research, consequential design,
unknown-cause debugging, planning, review, and long-running convergence. Claude
Code keeps local evidence inspection and clear authorized implementation on its
native path and still controls tools, permissions, agents, and prompts. There is
no generic Execute or router skill.

## Quick setup

Install every supported host or Claude Code alone:

```bash
./install.sh all
./install.sh claude
```

Choose a lower-cost profile or notification behavior when needed:

```bash
./install.sh claude --profile cost-first
./install.sh claude --profile cost-first --notifications
./install.sh claude --no-notifications
```

The default `performance-first` profile balances routine work with deeper
review. Run `./install.sh --help` for advanced options, and use `--link` only
while developing Teamwork from this checkout.

## Everyday use

Ask for the outcome you want:

- "Inspect this repository and implement the requested validation change."
- "Research the current provider options from official sources and cite them."
- "Design the public API boundary and recommend among the real alternatives."
- "This public API could be synchronous, queued, or hybrid; a wrong choice forces costly client migration and the evidence conflicts. Help me decide."
- "Diagnose why this test started failing, then verify the fix on the same path."
- "Turn the selected migration direction into a plan without changing files."
- "Review this diff against the requirements and direct evidence."
- "Keep working until this command is green."

Claude Code natively handles local repository, configuration, test, log,
runtime, and artifact inspection. Clear authorized implementation also stays
native. Use `teamwork-explore` for a distinct read-only local evidence question,
and `teamwork-research` only for external, current, multi-source, or
citation-backed research. Use `teamwork-design` while a consequential solution
is unsettled and `teamwork-plan` once the direction is selected. Design uses
Explorer only for an unresolved local constraint and sanitized external Research
only for a named external/current claim that can change the choice; it never runs
both by default. It compares
2-3 real alternatives or records safe-path evidence, makes one challenge pass,
and keeps the decision frontier finite: it shows the global map first, batches
only independent material decisions, and asks dependent decisions in later
turns. Its controlled transaction creates the
durable Design artifact before Plan; independent Plan Review runs only on user
request or a named material risk gate. It does not
implement the result or enter Plan silently.

Design chooses its search strategy from the request and evidence. It selects
adversarial only when at least two viable directions remain and costly or
irreversible error or conflicting evidence makes one challenge inadequate;
“high-risk” or “complex” alone is insufficient. `adversarial` forces the method
and `standard` disables it. The model states its reason and uses default `B=3`
without another confirmation. Every hypothesis then receives two fresh isolated
Designer critics and two new final auditors must both pass. Missing isolation,
exhausted budget, or failed closure returns an incomplete result and creates no
durable Design. A passing chat recommendation is still not Plan-ready until the
user explicitly accepts and authorizes the controlled Design write.

Debug begins with the real failure and reproduction. Plan translates an already
selected direction into owned executable steps; Review is read-only and returns
`ACCEPT`, `REVISE`, or `BLOCKED`; Goal persists an explicit objective, success
signal, scope, budget, and attempts before it iterates. Clear authorized code
work remains result-first: change the canonical owner, reuse existing
patterns/built-ins/suitable dependencies, add the smallest complete logic, and
prove each Worker slice with proportional focused tests plus the real path.
After Root integrates and seals one candidate, an independent max Review runs
once only on user request or a named material risk gate; findings form one repair
batch with at most one delta recheck per candidate.

Skill selection remains model behavior rather than deterministic routing. Name
a skill when its exact method matters. Research, design, planning, and review
remain read-only by default. Debug makes no change when diagnosis alone was
requested; an original request that already authorizes a fix allows the
evidenced narrow change. Approving a design or plan does not authorize
implementation.

An ordinary "ask me first" request asks questions without writing files. In an
initialized writable project, an explicit `grill-me`, save, resume, or record
request uses the transaction to update only `docs/teamwork/discussion/current.md`.
An independently major public/installable, migration/release, permission,
security, data, destructive, or cross-platform boundary opens the record
automatically. Within one scope, only creation, semantic decision/frontier
change, and close/supersede persist; unchanged state is a no-op. New records use
schema v2 `frontier` / `current_batch` state. An explicit "no files" or
off-the-record instruction wins.

## Initialize a project

```bash
./install.sh --project-root /path/to/project init-project
```

Initialization changes only the selected repository. It establishes
Teamwork-managed project instructions, memory entry points, ignore rules, and
CodeGraph context when available. It does not refresh global skills, agents,
policy, routing, or notifications, and it does not copy Teamwork skills or
agents into the project. Use `teamwork-update` or `./install.sh all` separately
for global setup.

## Agents and profiles

Teamwork may use eight Claude Code roles—Researcher, Explorer, Debugger,
Designer, Planner, Worker, Plan Reviewer, and Reviewer—when separate context is
worth the coordination cost. The main turn owns scope, integration, and the
final answer. Routine local work does not require an agent handoff.
`performance-first` and `cost-first` select Claude Code-native host templates;
they do not promise the Codex model or reasoning-effort mapping on Claude Code.

## Policy and notifications

Claude installs maintain only the Teamwork-owned block in
`~/.claude/CLAUDE.md` and preserve unrelated content. Inspect the block without
installing it with:

```bash
./install.sh claude-policy
```

Notifications cover main-turn completion and permission requests; subagents are
silent. `--no-notifications` removes only Teamwork-owned handlers. Hook
activation still depends on Claude Code trust. Static installation checks do
not prove live event delivery.

Teamwork does not override Claude Code permissions, MCP, tests, tools, UI, or
model behavior. Required paths, ports, credentials, commands, models, and
execution modes must come from the user or project evidence.

## Update and troubleshoot

```bash
./scripts/check-update.sh --readiness
./install.sh all
```

Use `teamwork-update` for a guided global refresh and `teamwork-init` only for
one repository's context. If skill selection is wrong, invoke the skill by
name. If notifications do not fire, check hook trust and the selected
notification setting. Readiness covers Teamwork-managed files and bounded
configuration; it cannot prove live hook delivery, model behavior, or
deterministic skill selection.

See the [main README](README.en.md) for the shared capability overview and the
[changelog](CHANGELOG.en.md) for upgrade details.
