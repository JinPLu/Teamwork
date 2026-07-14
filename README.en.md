# Teamwork

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

**Help Codex, Cursor, and Claude Code gather evidence before acting and finish complex research or engineering work with checkable results.**

Teamwork is a Codex-first skill package. After installation, describe your goal in natural language as usual. Teamwork organizes research, debugging, planning, execution, and review when the task needs them, while simple requests stay direct.

![Teamwork workflow](assets/teamwork-workflow-gpt-image-2.png)

## What You Get

- **More reliable research:** Ground work in primary sources, project files, and real configuration instead of inventing paths, ports, models, or parameters.
- **More focused questions:** Inspect discoverable facts first and ask you only about decisions that change the outcome, scope, acceptance, or authority.
- **Controlled collaboration:** Use subagents only when work splits cleanly; the main agent keeps ownership of scope, integration, and final verification.
- **Clear completion evidence:** Show whether the task is truly done with sources, logs, tests, diffs, or review results.
- **Continuity for long tasks:** Keep only the records needed across turns and resume failures from the affected stage.

Teamwork is a good fit for literature and field research, technical evaluation, complex plans, reproducible failures, CI, cross-file implementation, strict review, and “keep going until it passes” work. One-line facts and obvious small edits do not get forced into a workflow.

## Quick Start

You need a working Codex, Cursor, or Claude Code installation. The repository installer runs through Bash.

For Codex:

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
./scripts/check-update.sh --no-fetch
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
- `init-project`: install project skills into Codex `.agents/skills/`, Cursor `.cursor/skills/`, and Claude Code `.claude/skills/`, plus platform agents and global defaults, then configure project rules, the Teamwork memory entrypoint, and CodeGraph when available.

Restart Codex after a user-level installation changes role routing. The installer manages only Teamwork-owned directories, marked rules, and bounded configuration; it does not take over platform permissions, MCP, browser, or test settings. See the [Codex](CODEX.md), [Cursor](CURSOR.md), and [Claude Code](CLAUDE.md) guides for platform details.

## Update

After updating the repository, rerun the original install command and check the installed state:

```bash
git pull --ff-only
./install.sh codex
./scripts/check-update.sh --no-fetch
```

To include a project-local installation in the check:

```bash
./scripts/check-update.sh --project /path/to/project
```

## More Information

- [Changelog](CHANGELOG.en.md): user-visible changes in each release.
- [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md): platform setup and advanced usage.
- [Contributing](CONTRIBUTING.md): change scope and verification requirements.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues): problems and suggestions.
