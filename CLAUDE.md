@AGENTS.md

# Teamwork for Claude Code

Teamwork helps Claude Code research, diagnose failures, plan, implement scoped
changes, review completed work, and keep going until a result is verified.
Claude Code still performs the actual work and controls its tools and prompts.

## Quick setup

From this checkout, install Teamwork for every supported platform:

```bash
./install.sh all
```

For Claude Code only, use:

```bash
./install.sh claude
```

Both commands install the skills, agents, and Teamwork-managed global policy.
`all` and `init-project` enable completion and permission sounds by default. A
direct Claude install leaves notification settings unchanged unless chosen:

```bash
./install.sh claude --profile cost-first
./install.sh claude --profile cost-first --notifications
./install.sh claude --no-notifications
```

The default `performance-first` profile balances routine work and review depth;
`cost-first` favors lower-cost choices. Run `./install.sh --help` for advanced
profiles. Use `--link` only to develop Teamwork from this checkout.

Initialize each repository that needs project context:

```bash
./install.sh --project-root /path/to/project init-project
```

This refreshes the global installation and sets up the selected repository's
instructions, work-record entrypoints, and available CodeGraph context. It does
not copy Teamwork skills or agents into the repository.

## Everyday use

Ask for the outcome you want:

- “Research the current options and recommend one with sources.”
- “Diagnose why this test started failing.”
- “Plan this migration, but do not implement it yet.”
- “Implement this scoped change and verify the changed path.”
- “Review this diff against the requirements.”
- “Keep working until this command is green.”

The matching skills work by outcome: research gathers evidence; debug finds an
unknown cause before code changes; plan settles material choices; execute
produces an authorized result; review checks finished work; and goal supports
long-running convergence.

Claude Code selects skills from your request, so selection is model behavior,
not deterministic routing. Name a skill when exact selection matters. Small
questions and edits can stay on the native path. Asking to be “challenged,”
“questioned,” or “grilled” can select `grill-me`; ordinary work asks only for
required input or a decision Claude Code cannot safely make.

Replies lead with the conclusion; technical detail appears only when it helps or
you ask.

A clear change request can go directly to implementation. A plan is optional,
and approving one does not authorize edits. Research, debugging, planning, and
review stay read-only without separate change authority. Verification focuses
on the changed path or a named high-risk boundary.

When useful and authorized, Teamwork can save one compact summary of the goal,
settled choices, open question, key evidence, and continue point. Ordinary
requests do not need one.

## Agents and profiles

Teamwork may use Claude Code `Task` agents for independent work or fresh context:

- `explore` gathers evidence without editing.
- `designer` compares genuine design choices.
- `judge` checks whether a consequential plan is executable.
- `worker` implements one bounded slice.
- `code-reviewer` independently reviews completed work.
- `deep-judge` and `deep-reviewer` scrutinize higher-risk work.

The main turn owns scope, integration, and the final answer. Agents are optional.

## Policy and notifications

Claude installs maintain only the Teamwork-owned block in
`~/.claude/CLAUDE.md` and preserve other content. Inspect the block without
installing it with:

```bash
./install.sh claude-policy
```

Notifications cover main-turn completion and permission requests; subagents are
silent. `--no-notifications` removes only Teamwork-owned handlers. Hook activation
still depends on Claude Code trust. Installation is tested in isolation, but
live Claude event delivery has not been verified.

Teamwork does not override Claude Code permissions, MCP, tests, tools, UI, or
model behavior. Required paths, ports, credentials, commands, models, and
execution modes must come from you or repository evidence. Teamwork does not
guess them or emulate unavailable host features.

## Update and troubleshoot

Check whether the global installation is complete and current:

```bash
./scripts/check-update.sh --readiness
```

Use `teamwork-update` to check or guide a global refresh, or run:

```bash
./install.sh all
```

Use `teamwork-init` when a repository needs project context. If selection is
wrong, invoke the skill by name. If notifications do not fire, check hook trust
and your notification choice. Readiness covers Teamwork-managed files and
bounded configuration; it cannot prove live hook delivery, skill selection, or
model behavior.
