@AGENTS.md

# Claude Code Usage

Teamwork for Claude Code adapts the same result-first skill package used by
Codex and Cursor. Claude Code native capabilities—editing, shell execution,
MCP, permissions, `Task` subagents, planning, and verification—remain the
execution layer. Claude Code owns skill discovery, available tools, permission
prompts, interaction UI, hook trust, and the behavior produced by its selected
model.

## Install

Global setup:

```bash
./install.sh all
./install.sh claude
./install.sh claude --profile cost-first
./install.sh claude --profile cost-first --notifications
./install.sh claude --no-notifications
```

Use `./install.sh all` for the default full global refresh. The platform-specific
commands above are for a deliberately narrower setup. None initialize every
repository. Establish context for one selected repository with:

```bash
./install.sh --project-root /path/to/project init-project
```

`init-project` refreshes the current user's global Teamwork surfaces and sets
up the selected repository's Teamwork context, such as project instructions and
available work-record or CodeGraph entrypoints. It does not install Teamwork
skills or agents into the repository. A direct Claude install also maintains the
Teamwork-owned global policy; `claude-policy` prints that block for manual
review. Use `--link` only for local development.

Notifications are opt-in for direct installs and enabled by default for `all`
and `init-project`. They cover main-turn completion and permission requests;
subagents remain silent. Installation is tested in isolation, but live Claude
event delivery has not been verified, and plugin activation remains subject to
Claude Code's hook trust controls.

The default `performance-first` profile balances routine work and review depth.
Use `--profile cost-first` when lower-cost choices matter; `./install.sh --help`
lists advanced profiles when you need them.

## How To Use

Ask for research, debugging, a plan, execution of accepted scope, strict review,
or a verified long-running outcome. Claude Code uses the request and skill
descriptions to select a capability; this is model behavior, not deterministic
automatic routing. Explicitly invoke a skill when exact selection matters.
Small questions and tiny edits remain on Claude Code's native path. An explicit
request to be questioned, challenged, or grilled expresses question-first
intent and may select `grill-me`; otherwise Teamwork asks only for required
input or a material user-owned decision that it cannot discover safely.

Clear scope, criteria, and effect authority send change/build work directly to
the shortest real result path; an accepted plan is optional and never supplies
missing authority. Return to Plan only when new evidence changes accepted scope
or criteria. Planning, tests, validation, and review are support only: verify
only the changed path or a named high-risk boundary, and use fresh review only
when the user or an accepted risk gate requires it.

For planning, Teamwork grounds scope, required values, and verification in
evidence. Entering or confirming a plan authorizes neither implementation nor
writing a discussion record.

Replies lead with the conclusion or what it means. For a substantive discussion,
they connect observed facts, their plain interpretation, and only the boundary or
next comparison that could change the decision; continuing discussion keeps its
current question visible. This is a reasoning order, not a fixed answer format,
and simple facts stay one sentence. They add technical detail when it helps or
when you ask, rather than narrating internal workflow labels or version details.
In a repository initialized for Teamwork, when the user has authorized writes,
the runtime can write, and an explicit question-first discussion leaves a next
comparison or decision open, Teamwork can save one compact summary of the goal,
settled choices, open question, key evidence, and continue point. Explicit
save/resume, an approaching handoff or compaction, or three real branches also
make it useful; shortness neither triggers nor vetoes it. Ordinary requests do
not need one.

## Subagents

Teamwork may use Claude Code `Task` subagents for independent work that benefits
from separation or fresh context. Installed roles include `explore`, `designer`,
`judge`, `worker`, `code-reviewer`, plus `deep-judge` and `deep-reviewer` for
higher-risk review. Each returns a compact conclusion, evidence, unresolved
impact, and next action. The main agent keeps responsibility for scope,
integration, and a plain-language response—the conclusion or what
it means, why it matters, and what follows—rather than exposing coordination
mechanics.

## Long Tasks And Handoffs

When continuity is useful, Teamwork can save that compact summary in a repository
where the user has authorized writes. It is supporting context, not execution
authority and not a requirement for ordinary replies. Repeated failures return to
evidence gathering or debugging before another implementation attempt.

## Evidence, Limits, And Updates

Paths, ports, models, credentials, commands, and execution modes must come from
the user, repository, configuration, tests, or an accepted plan. Teamwork does
not take over Claude Code permissions, MCP, or test settings, and it does not
emulate structured question tools that the current runtime does not expose.

Use `teamwork-init` to configure one selected repository. Use
`teamwork-update` to check and guide a global refresh; the explicit refresh
command is `./install.sh all`. Check the global installation with
`./scripts/check-update.sh --readiness`. Refreshing an installation is not a
maintainer version release. This readiness check covers Teamwork-managed files
and bounded configuration; it does not verify Claude Code hook trust or prove
live skill selection and model behavior.
