<p align="center">
  <img src="assets/teamwork-workflow-gpt-image-2.png" alt="Teamwork workflow" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  Help Codex, Cursor, and Claude Code deliver the real result first; use research, tests, and review only when they advance delivery or protect a named boundary.
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="Supports Codex, Cursor, and Claude Code">
</p>

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## ✨ What it solves

Teamwork is one shared skill package adapted to Codex, Cursor, and Claude Code. It does not take over the host: Each host still owns skill discovery, native tool calls, permission policy, and the responses produced at runtime.

Usually, describe the outcome you want. When scope, acceptance criteria, and authority are clear, Teamwork takes the shortest real path. Plans, tests, validation, and review are support, never substitutes for an available real run; work stops when the result is obtained. Choosing research, debugging, planning, execution, or review remains model behavior rather than deterministic routing.

| 🎯 Focus | What you get |
| --- | --- |
| **Evidence-grounded work** | Use primary sources, project files, and real configuration instead of invented paths, ports, models, or parameters. |
| **Real result first** | A plan neither grants authority nor blocks execution; verify only the changed path or a named high-risk boundary. |
| **Questions only when needed** | Inspect discoverable facts first, then ask only about decisions that change outcome, scope, acceptance, or authority. |
| **Bounded collaboration** | Use subagents only when the work splits cleanly; the main task retains scope and integration ownership. |
| **Recoverable discussions** | Save useful continuity only for explicit save/resume, an approaching handoff, an open discriminator, or enough real branches. |

> [!TIP]
> One-line facts and obvious small edits are not forced through a workflow. Teamwork is most useful for research, technical choices, CI, cross-file implementation, strict review, and “keep going until it passes” work.

### 🧭 Communication and continuity

For substantive explanations, Teamwork starts with the conclusion or what it means, then connects observed facts, their plain interpretation, and the boundary that could change the decision. Technical detail appears when it is useful or requested.

In an initialized repository where the user has authorized writes and the runtime can write, an explicit request to be questioned or challenged may save one compact summary of the goal, settled choices, open question, key evidence, and continue point. Explicit save/resume, an approaching handoff, an open discriminator, or enough real branches can also make that continuity useful. An ordinary Plan does not automatically enter Grill or write a discussion record.

---

## 🚀 Quick start

### Codex: Marketplace plugin (recommended)

```bash
codex plugin marketplace add JinPLu/Teamwork@v3.4.0
codex plugin add teamwork-skill@teamwork
```

Then start a new Codex task and invoke:

```text
$teamwork-update
```

All ten Teamwork skills are available from the plugin cache as soon as the plugin is installed.

> [!IMPORTANT]
> Full first-time enablement still requires your explicit approval. `$teamwork-update` explains the Codex agents, routing, managed policy, notification choice, and verified legacy-skill cleanup it would apply. It never creates `~/.agents/skills` copies or overwrites content whose ownership is uncertain.

### Cursor, Claude Code, or the checkout compatibility path

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

Then ask for the outcome directly. Explicitly invoke a host-supported skill only when exact routing matters:

```text
Research this field, its key papers, and the existing code, then propose an executable plan.
Find the root cause of this CI failure; confirm it with logs and a reproduction before fixing it.
Implement directly and exercise the shortest real path early; fix the first real blocker and stop when it works.
Strictly review this output for false success, defensive fallback, and AI bloat.
Grill me: challenge only decisions that change the outcome, and stop when none remain.
```

---

## 🧩 Choose an installation path

| Target | Recommended entry point | Follow-up |
| --- | --- | --- |
| **Codex** | `codex plugin marketplace add JinPLu/Teamwork@v3.4.0` → `codex plugin add teamwork-skill@teamwork` | Start a new task and run `$teamwork-update` |
| **Codex checkout** (3.4.x compatibility) | `./install.sh codex` | For local development or users not ready to migrate to the plugin |
| **Cursor** | `./install.sh cursor` | Copy the Cursor User Rules |
| **Claude Code** | `./install.sh claude` | Use the managed global policy |
| **All platforms** | `./install.sh all` | Refresh every global Teamwork surface |

The Marketplace bundle is a complete runtime: it does not require users to keep a checkout, and carries the ten skills, Codex-specific install/update logic, agent templates, and notification resources. `teamwork-init` can establish project context for one repository through the plugin's Codex-only path; Cursor and Claude Code continue to use the repository installer.

### Common checkout options

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications codex
./install.sh --project-root /path/to/project init-project
```

- `--profile cost-first`: prefer current lower-cost models.
- `--notifications`: add main-turn completion and permission-request feedback to direct platform installs. Full `all` / `init-project` installs enable it by default; use `--no-notifications` to opt out.
- `init-project`: establish instructions, available work-record entrypoints, and CodeGraph context for one selected repository while refreshing the current user's global Teamwork surfaces; it does not install Teamwork skills or agents into the repository.

The default full global refresh is `./install.sh all`.

---

## 🔄 Updates and release reminders

### Update an installed Codex plugin

```bash
codex plugin marketplace upgrade teamwork
codex plugin add teamwork-skill@teamwork
```

Then start a new task and invoke `$teamwork-update` to check and refresh its managed Codex-only surface.

### Update the checkout workflow

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

### 🔔 Prefer a reminder instead of remembering versions?

Open [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork), choose **Watch** → **Custom**, then select **Releases**. GitHub notifies you in its inbox—and by email when enabled—when a new Release is published. It informs you of an update; it does not automatically upgrade a local plugin or configuration. [GitHub notification documentation](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)

---

## 🛡️ Safety boundaries and migration

> [!WARNING]
> Delete only entries you have confirmed Teamwork generated, never the whole `.agents`, `.codex`, `.cursor`, or `.claude` directory. The installer stops for same-name content that is unknown or modified and asks for human review.

- Marketplace first enablement configures only Codex agents, routing, managed policy, and optional notifications; it does not copy user skills.
- When notifications are enabled, restart Codex, open `/hooks`, and trust only Teamwork's `Stop` and `PermissionRequest` handlers—never trust-all.
- Cursor User Rules still need a manual copy-and-paste; the installer cannot verify that host-owned step.
- `./scripts/check-update.sh --readiness` verifies Teamwork-managed files and configuration only. It does not prove a manual host action is complete or guarantee that a natural-language request selects a particular skill.

---

## 📚 Learn more

- [Changelog](CHANGELOG.en.md): user-visible changes in each release.
- [Codex guide](CODEX.md), [Cursor guide](CURSOR.md), and [Claude Code guide](CLAUDE.md): platform setup and advanced use.
- [Repository architecture](docs/architecture.md): canonical sources, generated directories, stable commands, and change owners.
- [Contributing](CONTRIBUTING.md): change scope and verification requirements.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues): report a problem or suggest an improvement.
