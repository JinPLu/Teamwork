# Cursor Usage

Teamwork for Cursor adapts the same result-first skill package used by Codex
and Claude Code. Cursor's editor, shell, MCP, permissions, browser tools, `Task`
subagents, custom agents, and verification remain the execution layer. Cursor
owns skill discovery, available tools, permission prompts, interaction UI, and
the behavior produced by its selected model.

## Install

Global setup:

```bash
./install.sh all
./install.sh cursor
./install.sh cursor --profile cost-first
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
skills or agents into the repository. Use `--link` only when the installation
should track this checkout during development.

Cursor stores User Rules outside a normal project file. Run
`./install.sh cursor-policy-copy` (or print the block with `cursor-policy`), then
paste it manually into Cursor Settings -> Rules -> User Rules. The installer
cannot verify that this manual step was completed.

The default `performance-first` profile balances routine work and review depth.
Use `--profile cost-first` when lower-cost choices matter; `./install.sh --help`
lists advanced profiles when you need them.

Teamwork does not install Cursor notification sounds because the local hook path
has not been live-verified.

## How To Use

Ask naturally for research, debugging, a plan, execution, strict review, or a
verified long-running outcome. Cursor uses the request and skill descriptions
to select a capability; this is model behavior, not deterministic automatic
routing. Explicitly invoke a skill when exact selection matters. Tiny edits and
one-line questions remain on Cursor's native path. An explicit request to be
questioned, challenged, or grilled expresses question-first intent and may
select `grill-me`; otherwise Teamwork asks only for required input or a material
user-owned decision that it cannot discover safely.

Clear authorized change/build work goes directly to the shortest real result
path. Planning, tests, validation, and review are support only; an available
real run cannot be replaced by a proxy check, and work stops when the requested
result is obtained unless a named high-risk boundary remains.

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
settled choices, open question, key evidence, and continue point. Ordinary
requests do not need one.

## Subagents

Teamwork may use Cursor `Task` subagents or installed custom agents for
independent work that benefits from separation or fresh context. Each returns a
compact conclusion, evidence, unresolved impact, and next action. The main
agent keeps responsibility for scope, integration, and a
plain-language response—the conclusion or what it means, why it matters, and what
follows—rather than exposing coordination mechanics.

## Long Tasks And Handoffs

When continuity is useful, Teamwork can save that compact summary in a repository
where the user has authorized writes. It is supporting context, not execution
authority and not a requirement for ordinary replies. Repeated failures return to
evidence gathering or debugging before another implementation attempt.

## Evidence, Limits, And Updates

Paths, ports, models, credentials, commands, and execution modes must come from
the user, repository, configuration, tests, or an accepted plan. Teamwork does
not take over Cursor permissions, MCP, browser, or test settings, and it does
not emulate structured question tools that the current runtime does not expose.

Use `teamwork-init` to configure one selected repository. Use
`teamwork-update` to check and guide a global refresh; the explicit refresh
command is `./install.sh all`. Check the global installation with
`./scripts/check-update.sh --readiness`. Refreshing an installation is not a
maintainer version release. This readiness check covers Teamwork-managed files
and bounded configuration; it cannot verify the manual Cursor User Rules step
or prove live skill selection and model behavior.
