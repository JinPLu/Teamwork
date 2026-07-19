# Teamwork for Codex

Teamwork adds focused methods for external research, consequential design,
unknown-cause debugging, planning, review, and long-running convergence. Codex
keeps local repository inspection and clear authorized implementation on its
native path, so ordinary work does not need an Execute or router skill.

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
On first full enablement,
`$teamwork-update` explains the agents, agent configuration,
Teamwork-managed global policy, notification choice, and verified legacy cleanup
it proposes, then waits for approval. It does not copy skills to
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
Design the authentication boundary; explore only alternatives with real tradeoffs.
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

Use `$teamwork-design` while a consequential solution is open, and
`$teamwork-plan` only after the direction is selected. Design uses Explorer only
for an unresolved local constraint and sanitized external Research only for a
named external/current claim that can change the choice; it never runs both by
default. It compares 2–3 real
alternatives or records safe-path evidence, runs one challenge pass, and keeps
the user-decision frontier finite. Its controlled transaction creates the
durable Design artifact before Plan; independent Plan Review runs only on user
request or a named material risk gate. Design never
implements. `$teamwork-debug` begins with a real failure and reproduction;
`$teamwork-review` is read-only and returns `ACCEPT`, `REVISE`, or `BLOCKED`;
`$teamwork-goal` persists an explicit objective, success signal, scope, budget,
and attempts before it iterates.

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
coordination, and the final response. An ordinary request to "ask me first"
stays conversation-only. An explicit `$grill-me`, save, resume, or record uses
the transaction to update only `docs/teamwork/discussion/current.md`; an
independently major public/installable, migration/release, permission, security,
data, destructive, or cross-platform boundary opens that record automatically.
Within one scope, only creation, semantic decision/frontier change, and
close/supersede persist; unchanged state is a no-op. "No files" or off-the-record
wins.

## Agents and profiles

Full setup installs eight roles: Researcher, Explorer, Debugger, Designer,
Planner, Worker, Plan Reviewer, and Reviewer. Codex uses them only when separate
context or genuinely independent work is worthwhile; the main task remains
responsible for scope and integration. No subagent is required for routine local
inspection or implementation. The recommended and currently verified local Root
configuration remains user-controlled. The installer
configures only subagent profiles and routing; it does not set Codex's Root
main-task default.

Codex profiles are exact:

| Profile | Researcher / Explorer / Debugger / Planner / Worker | Designer | Plan Reviewer | Reviewer |
| --- | --- | --- | --- | --- |
| `performance-first` | `gpt-5.5` / `high` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `max` |
| `cost-first` | `gpt-5.5` / `medium` | `gpt-5.6-sol` / `medium` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `high` |

The split follows role behavior: 5.5 keeps high-frequency evidence, diagnosis,
planning, and implementation loops moving; 5.6 handles trade-off selection and
independent acceptance, where its more conservative reasoning is useful rather
than routine-path overhead.

For checkout-based installs, choose `cost-first` when lower-cost models should
handle the roles where that profile permits it:

```bash
./install.sh codex --profile cost-first
```

`./install.sh --help` lists supported targets and profiles. v3.4.2 migration
can remove only verified Router/Execute and legacy-role files; this is cleanup,
not an alias—v4 has no legacy role, Router, or Execute compatibility names.
Readiness confirms installed configuration, not that Codex will spawn a
particular agent for a natural-language request. Subagents do not send Teamwork
completion or permission notifications.

## Initialize one project

Ask `$teamwork-init` to set up the selected repository, or use a checkout:

```bash
./install.sh --project-root /path/to/project init-project
```

Initialization changes only that project. It establishes Teamwork-managed
project instructions, memory entry points, ignore rules, and CodeGraph context
when the CLI is available. It does not refresh global skills, agents, policy,
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
and verified legacy files before refreshing the managed setup. Restart Codex
after a routing change and repeat the manual `/hooks` review when requested.

## Checkout installation

The Marketplace plugin is the default for Codex users. The repository installer
remains useful for local development and for users who do not use the
Marketplace:

```bash
./install.sh all
./install.sh codex
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
./scripts/check-update.sh --readiness
```

Use `./install.sh all` for a full global refresh, a platform command for a
narrower installation, and `--link` only while developing from the checkout.
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
