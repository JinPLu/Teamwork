<h1 align="center">Teamwork</h1>

<p align="center">
  Focused research, design, debugging, planning, and review skills for Codex, Cursor, and Claude Code—without wrapping everyday work in another workflow.
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="Supports Codex, Cursor, and Claude Code">
</p>

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## What Teamwork helps you do

Teamwork is a set of installable skills for work that benefits from a distinct method. This version has 10 public skills, 3 advanced references used only by their owning skills, and 8 host-agent roles for external multi-source research, local evidence, consequential design, unknown-cause debugging, executable planning, independent review, and long-running convergence.

Inspecting local code, configuration, tests, logs, and runtime evidence is already a core agent capability. So is implementing a clear authorized change. In v4, those tasks stay on the host's native path: there is no generic Execute skill and no router skill making a second routing decision. Describe the result you want; the host still owns tools, permissions, skill selection, and the final response.

## Choose a capability when exact selection matters

| What you need | Skill | Use it when… |
| --- | --- | --- |
| Research the outside world | `$teamwork-research` | You need official sources, papers, market information, current facts, multiple sources, or traceable citations. |
| Find local project evidence | `$teamwork-explore` | You need a read-only answer from code, configuration, tests, logs, history, artifacts, or runtime state. |
| Design a consequential solution | `$teamwork-design` | A product, architecture, workflow, or public-contract choice still contains tradeoffs that can change the outcome. |
| Diagnose an unknown failure | `$teamwork-debug` | A real failure has an unknown cause and needs reproduction, discriminating evidence, and a verified fix. |
| Turn a direction into a plan | `$teamwork-plan` | The direction is selected and you need owned steps, dependencies, direct proof, and stop or replan conditions. |
| Review an output or claim | `$teamwork-review` | A plan, diff, artifact, or completion claim needs an independent evidence-backed verdict. |
| Keep going to a verified result | `$teamwork-goal` | You explicitly ask to continue until green, fix until passing, or pursue a budgeted verifiable target. |
| Challenge your decisions first | `$grill-me` | You explicitly want to be questioned or want the discussion saved, resumed, or recorded. |
| Initialize one project | `$teamwork-init` | You need project instructions, Teamwork memory entry points, or available CodeGraph context set up or cleaned up. |
| Check or refresh global setup | `$teamwork-update` | Teamwork-managed skills, agents, policy, routing, or notifications need an update. |

Research covers external or current evidence; Explore covers local project evidence. The Design/Plan boundary is simple: use Design while the solution is unsettled, Plan after the direction is selected, and neither for a clear implementation request.

Design invokes Explorer only when an unresolved local constraint can change the choice, and adds a sanitized Research question only for a named external or current claim that can change it; it does not run both evidence tracks by default. A genuine tradeoff receives 2–3 materially different alternatives; when evidence establishes one safe path, it records safe-path evidence and exclusions rather than inventing options. It performs one challenge pass and keeps user-owned choices in a finite frontier (normally no more than three). Once the direction is frozen, the controlled Design transaction creates one durable Design artifact; only then can Plan begin. Independent Plan Review runs only when the user requests it or a named material risk gate requires it. If the controlled writer is unavailable, Design stops rather than hand-writing a substitute. A Design, Plan, or approval never authorizes implementation.

Acknowledgment: v4 adopts Superpowers' hard gate, options, and specification self-check ideas. The one-pass challenge and finite decision frontier are Teamwork-specific local tailoring, not a claim to reproduce a Superpowers workflow.

## Quick start

### Codex Marketplace plugin (default)

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Start a new Codex task, then run:

```text
$teamwork-update
```

Codex uses the Marketplace plugin as the default installation path. Skills load directly from the plugin cache. On first full enablement, `$teamwork-update` explains the Codex agents, routing, managed global policy, notification choice, and verified legacy cleanup it proposes, then waits for approval. It does not create `~/.agents/skills` copies or overwrite content whose ownership is uncertain.

### Cursor, Claude Code, or development checkout installation

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

Install only one host when preferred:

```bash
./install.sh codex
./install.sh cursor
./install.sh claude
```

Cursor also requires `./install.sh cursor-policy-copy`, followed by a manual paste into **Cursor Settings → Rules → User Rules**. See the [Codex](CODEX.md), [Cursor](CURSOR.md), and [Claude Code](CLAUDE.md) guides for host-specific details.

## Initialize one project

Set up project instructions and work-record entry points for a repository:

```bash
./install.sh --project-root /path/to/project init-project
```

`init-project` changes only the selected project. It establishes Teamwork-managed project instructions, memory entry points, ignore rules, and local CodeGraph context when the CLI is available. It does not refresh global skills, agents, policy, routing, or notifications, and it does not install a Teamwork package copy inside the repository. Use `$teamwork-update` or `./install.sh all` separately for global updates.

## Discussion, implementation, review, and Goal

- A natural-language "ask me first" request asks questions without writing files. In an initialized writable project, an explicit `$grill-me`, save, resume, or record request uses the sole `docs/teamwork/discussion/current.md` record. An independently major discussion—public or installable capability/role, migration or release, permission, security, data, destructive, or cross-platform boundary—also opens the record automatically. Within one scope, persistence happens only for creation, a semantic decision/frontier change, and close/supersede; unchanged state is a no-op. "No files" or off-the-record always wins.
- Debug begins with the actual failure, reproduction, and evidence that distinguishes hypotheses; diagnosis-only authority makes no change. An originally authorized fix may change only the evidenced owner and rerun the same failing path. Research, Design, Plan, and Review are read-only by default; Plan turns a selected direction into executable work, while Review only returns an independent `ACCEPT`, `REVISE`, or `BLOCKED` verdict.
- Clear authorized implementation is result-first: change the canonical owner, reuse existing patterns, built-ins, or suitable dependencies, then add the smallest complete logic. Each Worker self-verifies its slice with proportional focused tests and the real path. After Root integrates and seals a candidate, one independent max Review runs only on user request or a named material risk gate; findings become one repair batch, followed by at most one delta recheck per candidate.
- `$teamwork-goal` applies only when you explicitly request persistence. It records the objective, success signal, scope, protected boundaries, budget, and attempts before work; it does not claim cross-turn persistence without durable state, and completes only when the real signal and every named boundary pass.
- The installer deletes only entries verified as Teamwork-generated. Never delete an entire `.agents`, `.codex`, `.cursor`, or `.claude` directory; installation stops on unknown or modified same-name content.
- After enabling Codex notifications, restart Codex and trust only Teamwork's `Stop` and `PermissionRequest` handlers in `/hooks`. Do not use trust-all.
- `./scripts/check-update.sh --readiness` checks Teamwork-managed files and configuration. It cannot perform Cursor User Rules or hook-trust actions, and it cannot guarantee that natural language selects the same skill every time.

## Updates

For a Codex Marketplace installation:

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Start a new task and run `$teamwork-update`. This is the default Codex update path. For a checkout installation:

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

When upgrading from v3.4.2, rerun the applicable install command or `$teamwork-update` so the installer can remove only the Router/Execute and legacy-role files it can prove it owns. Recognition exists solely for safe migration; it is not a v4 compatibility alias. v4 has no Router, Execute, or legacy-role aliases.

To hear about releases, open [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork) and choose **Watch → Custom → Releases**.

## Learn more

- [Changelog](CHANGELOG.en.md) — user-visible changes, upgrade actions, and limits.
- [Codex](CODEX.md), [Cursor](CURSOR.md), and [Claude Code](CLAUDE.md) — host-specific setup and troubleshooting.
- [Repository architecture](docs/architecture.md) — sources, generated directories, dependency boundaries, and stable commands.
- [Contributing](CONTRIBUTING.md) — change and verification requirements.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues) — report a problem or suggest an improvement.
