# Teamwork

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

**Help Codex, Cursor, and Claude Code gather evidence before acting and finish complex research or engineering work with checkable results.**

Teamwork is a Codex-first skill package. After installation, describe your goal in natural language as usual. Teamwork organizes research, debugging, planning, execution, and review when the task needs them, while simple requests stay direct. Replies lead with the conclusion or what it means. For a substantive discussion, they connect observed facts, their plain interpretation, and only the boundary or next comparison that could change the decision. Continuing discussions keep the current question visible. Technical detail appears when it is useful or requested, rather than as unexplained process, version, or label narration.

![Teamwork workflow](assets/teamwork-workflow-gpt-image-2.png)

## What You Get

- **More reliable research:** Ground work in primary sources, project files, and real configuration instead of inventing paths, ports, models, or parameters.
- **More focused questions:** Inspect discoverable facts first and ask you only about decisions that change the outcome, scope, acceptance, or authority.
- **Controlled collaboration:** Use subagents only when work splits cleanly; the main agent keeps ownership of scope, integration, and final verification.
- **Clear completion evidence:** Show whether the task is truly done with sources, logs, tests, diffs, or review results.
- **Recoverable discussions:** Only observable continuity signals create one compact summary of the goal, settled choices, open question, key evidence, and continue point; one material conclusion with an unresolved next comparison or decision is enough to create it. Ordinary replies stay brief and direct.

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

Then ask for the result directly—there are no skill names to memorize:

```text
Research this field, its key papers, and the existing code, then propose an executable plan.
Find the root cause of this CI failure; confirm it with logs and a reproduction before fixing it.
Execute the accepted plan and verify it; keep iterating until it passes or reaches a real blocker.
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

Restart Codex after a user-level installation changes role routing. Cursor User Rules still require a manual copy-and-paste step that the installer cannot verify. The installer manages only Teamwork-owned directories, marked rules, and bounded configuration; it does not take over platform permissions, MCP, browser, or test settings. See the [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md) for platform details.

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
