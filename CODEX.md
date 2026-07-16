# Codex Usage

Teamwork for Codex adapts the same shared skill package used by Cursor and
Claude Code. Codex native capabilities—editing, shell execution, plans,
custom agents, permissions, MCP, browser tools, and review—remain the execution
layer. Teamwork helps decide when extra research, debugging, planning,
delegation, or verification will improve the result without slowing down simple
requests. Codex owns skill discovery, tool availability, permission prompts,
interaction UI, and the behavior produced by the selected model.

For clear authorized change/build work, Teamwork sends Codex straight to the
shortest real result path. Plans, tests, validation, and review are support only:
they must unblock delivery, distinguish the current failure, check changed
behavior, or protect a named high-risk boundary. An available real run is never
replaced by a proxy check, and work stops when the requested result is obtained.

## Install

Global setup:

```bash
./install.sh all
./install.sh codex
./install.sh codex --profile cost-first
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
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
skills or agents into the repository. Use `--link` only when developing from
this checkout.

The current supported Codex target installs user skills under
`~/.agents/skills` and custom agent roles under `~/.codex/agents`. Older
Teamwork copies under `~/.codex/skills` are migration input, not the supported
runtime location. Custom-agent routing stays on Teamwork's currently compatible
Codex path; installation and readiness checks do not prove a live spawn.

The default `performance-first` profile balances routine work and review depth.
Use `--profile cost-first` when lower-cost choices matter; `./install.sh --help`
lists advanced profiles when you need them.

Global Codex installs maintain Teamwork's role routing while preserving unrelated
user configuration. Restart Codex after a routing change. If another tool owns
that configuration, consult `./install.sh --help` before changing it.

Notifications are opt-in for direct Codex installs and enabled by default for
`all` and `init-project`. They cover main-turn completion and permission
requests; subagents remain silent. After installation, open the Codex CLI, run
`/hooks`, and review and trust each Teamwork hook. The installer cannot perform
that user-owned trust step.

## How To Use

Ask for the outcome in normal language. Codex uses the request and each skill's
description to select a suitable capability, but this is model behavior rather
than deterministic automatic routing. Explicitly invoke a skill when exact
selection matters. Teamwork is most useful for:

- research grounded in papers, official documentation, project files, or
  source history;
- reproducible debugging based on logs and runtime evidence;
- plans only when requested or a material choice/protected boundary blocks action;
- direct implementation of authorized change/build work or a known fix;
- fresh review for unsupported completion claims, risky fallbacks, or clutter;
- long-running work that should continue until verified or genuinely blocked.

Small facts, tiny edits, and obvious local fixes stay on Codex's native fast
path. An explicit request to be questioned, challenged, or “grilled” expresses
question-first intent and may select `grill-me`; otherwise Teamwork asks only
when required input or a material user-owned decision cannot be discovered
safely.

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

Codex Plan mode and `teamwork-plan` share one planning path: Codex owns the host
UI and plan state, while Teamwork grounds scope, required values, and
verification in evidence. Entering or confirming a plan authorizes neither
implementation nor writing a discussion record.

Use `teamwork-init` to set up one repository, align its project instructions,
or add the optional Teamwork work-record and CodeGraph entrypoints. It targets
the selected repository rather than changing every project for the user.

## Subagents And Goals

Codex custom agents are useful only for independent work that benefits from
separation or fresh context. Each returns a compact conclusion, evidence,
unresolved impact, and next action. The root agent remains responsible for
scope, integration, and a plain-language response—the conclusion
or what it means, why it matters, and what follows—rather than exposing coordination
mechanics.

Use native Codex goal state when the user explicitly requests it or accepts a
goal proposal. Numeric budgets must come from the user or runtime; Teamwork does
not invent one.

## Evidence, Limits, And Updates

Teamwork relies on sources, repository files, configuration, tests, logs,
diffs, screenshots, and review evidence. It does not enable platform tools,
change permission policy, configure MCP or browsers, or prove model behavior by
installation alone. Codex owns its native structured-question UI; Teamwork uses
it only when the runtime exposes it and otherwise asks concisely in text.

Use `teamwork-update` to check and guide a global Teamwork refresh from this
checkout. The explicit refresh command is `./install.sh all`; refreshing an
installation is separate from publishing a new Teamwork version.

Useful global check:

```bash
./scripts/check-update.sh --readiness
```

This reports freshness and completeness of Teamwork-managed files and bounded
configuration. It does not verify that the user has trusted Codex hooks or that
a natural-language request will select a particular skill at runtime.
