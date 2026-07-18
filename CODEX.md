# Teamwork for Codex

Teamwork helps Codex research from evidence, diagnose failures, make plans when
they are useful, implement scoped changes, review risky work, and keep going
until a result is verified. For small questions and obvious edits, Codex stays
on its normal fast path.

## Quick start: Marketplace plugin

Install the Marketplace and plugin:

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Open a new Codex task and run:

```text
$teamwork-update
```

The ten Teamwork skills are available immediately from the plugin cache.
`$teamwork-update` completes the recommended setup by proposing Codex agents,
routing, the Teamwork-managed global policy, and your notification choice. The
first full enablement waits for your explicit approval. It does not copy skills
to `~/.agents/skills`, and it removes only verified legacy Teamwork copies.

Restart Codex after routing changes. If notifications are enabled, open `/hooks`
and trust the Teamwork `Stop` and `PermissionRequest` handlers individually.
Never use trust-all. The plugin intentionally ships no pretrusted hooks, so this
manual Codex step cannot be completed by the installer.

## Everyday use

Describe the result you want in normal language:

```text
Research this choice from official sources and the repository, then recommend what to do.
Find the cause of this CI failure from logs and a reproduction, then fix it.
Implement this change and verify the changed path.
Review this diff for correctness, regressions, and unsupported completion claims.
Keep working until the test is green or you are genuinely blocked.
```

Codex selects skills from your request, but selection is model behavior rather
than a deterministic router. Invoke a skill explicitly when the exact workflow
matters, for example `$teamwork-research`, `$teamwork-debug`,
`$teamwork-execute`, `$teamwork-review`, or `$teamwork-goal`. Use
`$teamwork-plan` when you want a plan or a material decision must be settled
before action. Use `$grill-me` when you explicitly want Codex to challenge your
assumptions before proceeding.

Teamwork adds only the amount of process that helps the result: evidence for
research, reproduction for unknown failures, bounded implementation for clear
changes, and fresh review when you ask for it or a high-risk boundary requires
it. Codex still owns permissions, tools, Plan mode, browser and MCP access, and
the final response.

Replies lead with the conclusion; technical detail appears only when it helps
or you ask. When useful and authorized, Teamwork can save one compact summary
of the goal, settled choices, open question, key evidence, and continue point.
Ordinary requests do not need one.

## Agents and profiles

The full setup installs seven Codex agent roles under `~/.codex/agents` and
configures routing for one main task plus up to eight subagents. They give Codex
separate read-only contexts for evidence and design, a bounded worker for
independent implementation, and fresh-context judges and reviewers for work
that benefits from an independent check. Codex uses them only when the work
splits cleanly; the main task remains responsible for scope and integration.

The default `performance-first` profile balances routine work with deeper
review. Choose `cost-first` when lower-cost models should handle routine reading,
design, and implementation while stronger models remain available for review.
`./install.sh --help` lists the advanced compatibility profiles. Installation
and readiness checks confirm configuration, not that Codex will spawn an agent
for a particular natural-language request. Subagents do not send Teamwork
completion or permission notifications.

## Initialize one project

Ask `$teamwork-init` to initialize a selected repository, or use the checkout
command below:

```bash
./install.sh --project-root /path/to/project init-project
```

This refreshes the current user's global Teamwork setup and adds project
instructions, Teamwork work-record entrypoints, and CodeGraph context when
available. It does not copy Teamwork skills or agents into the repository.
Initializing one project does not modify every other project.

## Update the Marketplace installation

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Then open a new task and run `$teamwork-update` again. It checks the Marketplace
catalog and cache, activation marker, agents, routing, policy, notifications,
and duplicate legacy copies before refreshing the managed setup. Restart Codex
after any routing change and repeat the manual `/hooks` review when requested.

## Checkout compatibility (3.4.x)

The repository installer remains available for local development, Cursor and
Claude Code users, and Codex users who have not activated the Marketplace
workflow:

```bash
./install.sh all
./install.sh codex
./install.sh codex --profile cost-first
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
```

Use `./install.sh all` for the default full global refresh, or a platform command
for a narrower installation. Direct `codex` installs leave notifications
unchanged unless `--notifications` or `--no-notifications` is supplied; `all`
and `init-project` enable them by default. Use `--link` only when developing
from this checkout.

The checkout Codex target installs skills under `~/.agents/skills`, agents under
`~/.codex/agents`, and the Teamwork-managed global policy and routing while
preserving unrelated configuration. Older Teamwork copies under
`~/.codex/skills` are migration input, not the supported checkout location. If
Marketplace activation already exists, `./install.sh codex` stops instead of
creating duplicate skills; open a new task and use `$teamwork-update`.

Check a checkout installation with:

```bash
./scripts/check-update.sh --readiness
```

For the plugin runtime, `$teamwork-update` resolves and runs the equivalent
plugin-cache readiness check, so you do not need to keep a checkout.

## Troubleshooting

- **The plugin is installed, but agents or routing are missing:** open a new
  task, run `$teamwork-update`, review its proposed changes, and approve the
  first full enablement.
- **The plugin cache or catalog is stale:** run the Marketplace update sequence
  above, open a new task, and run `$teamwork-update` again.
- **Readiness is green but notifications do not run:** restart Codex, inspect
  `/hooks`, and trust only Teamwork `Stop` and `PermissionRequest`. Static
  readiness cannot perform or verify this host-owned trust step.
- **Installation stops on an existing file:** do not delete whole `.agents` or
  `.codex` directories. Teamwork refuses to overwrite same-name content whose
  ownership or contents it cannot verify; inspect that specific conflict first.
- **A request did not select the skill or agent you expected:** invoke the skill
  explicitly. Installed configuration cannot guarantee model routing or a live
  agent spawn for every prompt.

See the [main README](README.en.md) for the cross-platform overview and the
[changelog](CHANGELOG.en.md) for user-visible changes.
