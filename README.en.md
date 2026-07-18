<p align="center">
  <img src="assets/teamwork-workflow-gpt-image-2.png" alt="Teamwork workflow" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  A shared skill package that helps Codex, Cursor, and Claude Code research, decide, build, debug, and verify real work without unnecessary process.
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="Supports Codex, Cursor, and Claude Code">
</p>

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## What Teamwork helps you do

Describe the outcome you want. Teamwork helps the host choose the shortest useful path: gather evidence when facts are missing, diagnose failures before changing code, settle material choices, implement directly when the work is clear, and verify the result at the right boundary.

It is especially useful for technical research, architecture choices, CI failures, cross-file changes, strict reviews, and tasks that must keep going until a check passes. Simple questions and obvious edits stay simple.

| Capability | Ask Teamwork to… |
| --- | --- |
| **Research** | Check current facts, primary sources, project files, and real configuration before recommending a direction. |
| **Debug** | Find and confirm the root cause of an unexpected failure before attempting a fix. |
| **Plan** | Resolve choices that materially change scope, architecture, acceptance, or risk. |
| **Execute** | Build or change the requested result, exercise the real path early, and fix the first blocker. |
| **Review** | Check a plan, diff, artifact, or completion claim against direct evidence. |
| **Goal** | Continue iterating toward a verifiable result, including “keep going until it passes” work. |
| **Grill** | Challenge only the decisions that can change the outcome, then stop when none remain. |
| **Initialize and update** | Set up project context or refresh Teamwork-managed global skills, agents, policy, and notifications. |

Teamwork does not replace the host. Codex, Cursor, and Claude Code still control skill discovery, native tools, permissions, and runtime responses. Routing is model behavior, not a guarantee that a particular natural-language prompt selects a particular skill.

## Quick start

### Codex plugin (recommended)

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Start a new Codex task, then run:

```text
$teamwork-update
```

The plugin makes all ten Teamwork skills available without keeping a repository checkout. Full first-time enablement still requires your approval: `$teamwork-update` explains the Codex agents, routing, managed policy, notification choice, and any verified legacy-skill cleanup before applying them. It does not create `~/.agents/skills` copies or overwrite content whose ownership is uncertain.

### Cursor, Claude Code, or checkout-based Codex

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

After installation, ask for the result directly. Name a capability only when you want exact routing:

```text
Research this field, its key papers, and the existing code, then propose an executable plan.
Find the root cause of this CI failure; confirm it with logs and a reproduction before fixing it.
Implement this directly, run the shortest real path early, and stop when it works.
Strictly review this output for false success, defensive fallback, and unnecessary complexity.
Grill me: challenge only decisions that change the outcome, and stop when none remain.
```

## Installation choices

| Target | Install | Required follow-up |
| --- | --- | --- |
| **Codex plugin** | `codex plugin marketplace add JinPLu/Teamwork` then `codex plugin add teamwork-skill@teamwork` | Start a new task and run `$teamwork-update`. |
| **Codex checkout** (3.4.x compatibility) | `./install.sh codex` | Use for local development or when not migrating to the plugin. |
| **Cursor** | `./install.sh cursor` | Manually copy the generated Cursor User Rules. |
| **Claude Code** | `./install.sh claude` | Use the installed managed global policy. |
| **All three hosts** | `./install.sh all` | Refresh Teamwork-managed files, then manually copy the Cursor User Rules. |

Useful checkout commands:

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications codex
./install.sh --project-root /path/to/project init-project
```

- `--profile cost-first` prefers current lower-cost models.
- `--notifications` adds completion and permission-request feedback to direct platform installs. `all` and `init-project` enable it by default; use `--no-notifications` to opt out.
- `init-project` refreshes the current user's global Teamwork surfaces and establishes instructions and work-record entry points for one repository. It adds CodeGraph context only when the CLI is available and initialization succeeds. It does not install Teamwork skills or agents inside that repository.

The default complete checkout refresh is `./install.sh all`. Plugin-based `teamwork-init` can establish project context through its Codex-only path; Cursor and Claude Code use the checkout installer.

## Updates

For a Codex plugin install:

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Start a new task and run `$teamwork-update` to check and refresh the Codex-managed surface.

For a checkout install:

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

To hear about new versions, open [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork), choose **Watch** → **Custom** → **Releases**. GitHub sends a notification but does not upgrade your local plugin or configuration. See [GitHub's notification guide](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications).

## Safety and authority

- A plan never grants permission to make changes. Teamwork acts only within the authority you provide and asks when a decision would change the outcome, scope, acceptance criteria, or permission boundary.
- Delete only entries you have confirmed Teamwork generated—never an entire `.agents`, `.codex`, `.cursor`, or `.claude` directory. The installer stops when same-name content is unknown or modified.
- Marketplace first-time enablement configures Codex agents, routing, managed policy, and optional notifications; it does not copy user skills.
- If you enable notifications, restart Codex, open `/hooks`, and trust only Teamwork's `Stop` and `PermissionRequest` handlers. Do not use trust-all.
- Cursor User Rules require a manual copy-and-paste. The installer cannot verify this host-owned step.
- `./scripts/check-update.sh --readiness` checks Teamwork-managed files and configuration. It cannot prove that a manual host action is complete.

## Learn more

- [Changelog](CHANGELOG.en.md) — user-visible changes and upgrade notes.
- [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md) — platform setup and advanced use.
- [Repository architecture](docs/architecture.md) — canonical sources, generated directories, stable commands, and change ownership.
- [Contributing](CONTRIBUTING.md) — change scope and verification requirements.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues) — report a problem or suggest an improvement.
