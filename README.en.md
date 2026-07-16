# Teamwork

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

**Help Codex, Cursor, and Claude Code produce the real result first, using research, tests, and review only when they advance delivery or protect a named boundary.**

Teamwork is one shared skill package adapted to Codex, Cursor, and Claude Code. Each host still owns skill discovery, native tool calls, permission policy, and the responses produced at runtime. After installation, you can usually describe your goal in natural language. Clear authorized change/build work goes straight to the shortest real path; planning, tests, validation, and review are support and cannot replace an available real run, and work stops when the requested result is obtained. The host still uses the request and skill descriptions to select research, debugging, planning, execution, or review. That selection is model behavior, not deterministic automatic routing. For substantive explanations, Teamwork asks for a short argument that starts with the conclusion or what it means, connects the observed facts to their plain interpretation, and includes only a boundary or comparison that could change the decision. Technical detail appears when it is useful or requested, rather than as unexplained process, version, or label narration.

![Teamwork workflow](assets/teamwork-workflow-gpt-image-2.png)

## What You Get

- **Evidence-grounded research:** Use primary sources, project files, and real configuration instead of inventing paths, ports, models, or parameters.
- **Real result first:** Clear scope, acceptance criteria, and effect authority permit direct modification, generation, or execution; an accepted plan is optional and never supplies authority. Return to Plan only when new evidence changes accepted scope or criteria. Check only the changed path or a named high-risk boundary, stop when the result appears, and use independent review only when the user or an accepted risk gate requires it.
- **Questions only when needed:** Inspect discoverable facts first and ask only about decisions that change the outcome, scope, acceptance, or authority.
- **Bounded collaboration:** Use subagents only when work splits cleanly; the main agent keeps ownership of scope and integration without replaying completed work.
- **Real-path completion:** Prefer the actual artifact, command, or runtime result; plans, mocks, static checks, and proxy tests cannot turn an unrun target into completion.
- **Recoverable discussions:** In an initialized repository where the user has authorized writes and the runtime can write, an explicit request to be questioned or challenged may save one compact summary of the goal, settled choices, open question, key evidence, and continue point for a later task. Any one of explicit save/resume, an approaching handoff or compaction, a settled conclusion with an open discriminator, or three real branches makes it useful; shortness neither triggers nor vetoes it. An ordinary Plan does not automatically enter Grill or write a discussion record.

Teamwork is a good fit for literature and field research, technical evaluation, complex plans, reproducible failures, CI, cross-file implementation, strict review, and “keep going until it passes” work. One-line facts and obvious small edits do not get forced into a workflow.

## Quick Start

You need a working Codex, Cursor, or Claude Code installation. The repository installer runs through Bash.

For the full global setup:

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

Then usually ask for the result directly. Natural language expresses intent; when exact routing matters, explicitly invoke a skill supported by the host:

```text
Research this field, its key papers, and the existing code, then propose an executable plan.
Find the root cause of this CI failure; confirm it with logs and a reproduction before fixing it.
Implement directly and exercise the shortest real path early; fix the first real blocker and stop when it works.
Strictly review this output for false success, defensive fallback, and AI bloat.
Grill me: challenge only decisions that change the outcome, and stop when none remain.
```

## Install

| Target | Command |
|---|---|
| Codex | `./install.sh codex` |
| Cursor | `./install.sh cursor` |
| Claude Code | `./install.sh claude` |
| All platforms | `./install.sh all` |

These global commands make Teamwork skills and agents available to the current user; they do not modify every project automatically. The default full global refresh is `./install.sh all`. To establish Teamwork context for one repository, use `teamwork-init`, or use the `init-project` command below with an explicit project path.

The default installation uses the `performance-first` profile. See every target and option with:

```bash
./install.sh --help
```

Common options:

```bash
./install.sh --profile cost-first codex
./install.sh --notifications codex
./install.sh --project-root /path/to/project init-project
```

- `--profile cost-first`: prefer current lower-cost models.
- `--notifications`: add main-turn completion and permission-request sounds to direct platform installs; subagents stay silent. Full `all`/`init-project` installs enable them by default; use `--no-notifications` to opt out. After a Codex install, run `/hooks` in the CLI and trust the two Teamwork hooks individually.
- `init-project`: establish Teamwork context for one selected repository, including project instructions and, when available, a work-record entrypoint and CodeGraph. It also refreshes the current user's global skills, agents, and default rules; it does not install Teamwork skills or agents into the repository.

Migration note: existing project-level Teamwork copies are no longer supported or refreshed. Delete only entries you have confirmed Teamwork generated—never the whole `.agents`, `.codex`, `.cursor`, or `.claude` directory—then run `./install.sh all`.

Restart Codex after a user-level installation changes role routing; its hooks still require individual trust in the CLI. Cursor User Rules still require a manual copy-and-paste step that the installer cannot verify. The installer manages only Teamwork-owned directories, marked rules, and bounded configuration; it does not take over platform permissions, MCP, browser, test settings, or host model behavior. See the [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md) for platform details.

`./scripts/check-update.sh --readiness` checks the freshness and completeness of Teamwork-managed files and configuration. It does not prove that the manual Cursor User Rules or Codex hook-trust steps are complete, or that a particular natural-language request will activate a specific skill.

## Update

After updating the repository, use the full global install to refresh Teamwork for the current user, then check its state:

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

In an assistant session, `teamwork-update` can check and guide this global refresh; `teamwork-init` handles project context.

## More Information

- [Changelog](CHANGELOG.en.md): user-visible changes in each release.
- [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md): platform setup and advanced usage.
- [Repository architecture](docs/architecture.md): canonical sources, generated directories, stable commands, and change owners.
- [Contributing](CONTRIBUTING.md): change scope and verification requirements.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues): problems and suggestions.
