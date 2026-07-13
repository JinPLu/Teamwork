# Teamwork

[中文](README.md) · [Changelog](CHANGELOG.en.md) · [Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)

**Help Codex, Cursor, and Claude Code gather evidence before acting and finish complex research or engineering work with checkable results.**

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**. It does not replace shell, MCP, browser, permissions, or test tools. It adds task routing, evidence constraints, controlled delegation, cross-turn memory, and acceptance loops on top of those native capabilities.

![Teamwork workflow](assets/teamwork-workflow-gpt-image-2.png)

## What It Solves

| Common failure | Teamwork response |
|---|---|
| Research stops at one source | Expand from the seed to primary sources, neighboring evidence, and relevant counter-evidence |
| Research, implementation, and review blur into one long chat | Route by risk into research, debug, plan, execute, review, or goal work |
| Parallel subagents become disconnected chats | Split only independent tracks; the main agent owns scope, integration, and final verification |
| Missing paths, ports, models, or config get invented | Required values must come from the user, project, source, config, tests, or an accepted plan |
| “Done” has no proof | Support conclusions with sources, logs, tests, diffs, artifacts, or fresh review |

Small requests stay on the platform's native fast path. Teamwork adds structure only when it improves correctness, continuity, or acceptance.

## Quick Start

Prerequisites: a working Codex, Cursor, or Claude Code installation; the repository installer runs through Bash.

For Codex:

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
./scripts/check-update.sh --no-fetch
```

After installation, ask for the outcome in natural language—there are no workflow names to memorize:

```text
Research this field, its key papers, and the existing code, then propose an executable plan.
Find the root cause of this CI failure; confirm it with logs and a reproduction before fixing it.
Execute the accepted plan and verify it; record failures until it passes or reaches a real blocker.
Strictly review this output for false success, defensive fallback, and AI bloat.
Grill me: challenge only outcome-changing decisions; stop when none remain, and skip language or file-count trivia.
```

## Choose An Install

| Platform | Command | Installed surface |
|---|---|---|
| Codex | `./install.sh codex` | `~/.codex/skills/`, `~/.codex/agents/`, a marked `~/.codex/AGENTS.md` block, and bounded role-routing keys in `~/.codex/config.toml` |
| Cursor | `./install.sh cursor` | `~/.cursor/skills/` and `~/.cursor/agents/`; follow the terminal prompt for User Rules |
| Claude Code | `./install.sh claude` | `~/.claude/skills/`, `~/.claude/agents/`, and a marked Teamwork block in `~/.claude/CLAUDE.md` |
| All three | `./install.sh all` | All user-level surfaces above |

The defaults are `--copy` and `performance-first`: Codex uses GPT-5.6 Terra/Sol, while Cursor and Claude Code use their current native models. `cost-first` also uses current low-cost models; legacy `gpt55-*` names remain aliases but no longer call GPT-5.5. Use the built-in help for advanced targets:

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications --profile cost-first codex
```

`--notifications` adds user-level main-turn completion and permission-request
sounds for Codex/Claude Code; subagents stay silent and normal installs preserve
existing notification settings. `--no-notifications` removes only Teamwork's
handlers. Codex plugin users explicitly trust them through `/hooks`. Cursor is
not claimed supported until its local hook path is live-verified.

User-level Codex installs atomically migrate custom-agent routing so fresh
subagents can select each role's model and effort through `agent_type`. They set
the root-inclusive session limit to 9 threads (one main thread plus up to eight
subagents); restart Codex after a change. Use `--no-codex-routing` only when
another system owns those keys. Project-only installs never mutate user config.

Native question input belongs to the current host, not Teamwork installation
state. Use `request_user_input` when the runtime exposes it and fall back to a
concise text question otherwise. Teamwork never changes user configuration,
switches modes, or enables an experimental feature just to ask a question.

For project-local installation or full project initialization:

```bash
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project init-project
```

`project` installs project-local skills and agents. `init-project` also configures project instructions, the `docs/teamwork/` memory entrypoint, and CodeGraph when available. When developing this repository, use `./install.sh --link codex` so the installed surface follows the checkout.

The installer manages only Teamwork-owned directories, agent files, bounded policy blocks, and bounded Codex routing keys. Each platform still owns its permissions, MCP, browser, and test configuration. See the [Codex](CODEX.md), [Cursor](CURSOR.md), and [Claude Code](CLAUDE.md) guides for platform details.

## When To Use It

Good fits include:

- literature or field research, API/library selection, competitor research, and historical decision lookup;
- evidence-backed option comparison, experiment design, and engineering implementation;
- reproducible failures, flaky tests, CI, crashes, and UI symptom diagnosis;
- subagent research, implementation, or review that splits into independent tracks;
- cross-turn work or iteration until tests pass, a target is met, or a real blocker is confirmed.

Skip it for one-line facts, obvious tiny edits, local syntax questions, or tightly coupled work where delegation costs more than it helps. Sensitive, destructive, paid, or public actions still follow platform permissions and user confirmation.

## How It Works

`using-teamwork` is the lightweight router. It loads a dedicated skill only when the current task needs it:

| Skill | Responsibility |
|---|---|
| `grill-me` | Challenge, ground, and classify unknowns, then ask only user-owned outcome decisions through native/structured input |
| `teamwork-research` | Verify sources, external constraints, options, and the repro surface |
| `teamwork-debug` | Use reproduction, logs, hypotheses, and instrumentation to establish root cause |
| `teamwork-plan` | Deeply integrate Codex Plan mode with evidence, sourced values, scope, phases, acceptance, and stop conditions |
| `teamwork-execute` | Implement and verify an accepted scope |
| `teamwork-review` | Check diffs, evidence, quality, and completion claims |
| `teamwork-goal` | Iterate on an explicit target until complete or genuinely blocked |

`grill-me` is an interaction skill, not a Teamwork stage. It activates when the user explicitly asks to be questioned, challenged, or grilled, and a non-simple Plan with a material decision or risk also enters an evidence-first Grill before its Decision Summary is confirmed. Ordinary clarification stays native; explicit negative interview intent suppresses questioning, and quoted, file, tool, example, or maintenance text is inert. The skill inspects discoverable facts, lets the agent own safe reversible implementation choices, and asks only unresolved user decisions that materially change public behavior, compatibility, acceptance, cost, risk, or irreversible action. It asks one decision at a time, without quotas or repeated questions. It uses `request_user_input` when callable and concise text otherwise. Ending a grill or confirming a Plan never grants execution authority.

`teamwork-init` owns project setup; `teamwork-update` owns install refresh and release hygiene.

In Codex Plan mode, the native mode owns the question UI and final plan item,
while `teamwork-plan` owns one shared quality gate. It inspects owners, config,
tests, and facts before asking; reconciles answers afterward; and maps each
requirement to a phase with owned surface, inputs, outputs, dependencies,
verification, and stop conditions. Execution-critical values must come from the
user, repository, or a justified derivation. Unresolved values stay visible;
plan length alone never establishes readiness.

For a non-simple Plan—one with a material decision or risk, not merely many
files—run an evidence-first Grill unless the user explicitly declines it. Before
the final Plan, confirm a concise Decision Summary of material choices,
assumptions, and unresolved items. Simple or mechanical Plans stay direct.
Confirmation accepts planning only; it does not authorize implementation.

Across hosts, Judge and Reviewer findings use stable IDs and bind to the accepted
Contract and ACs: only a blocking Contract/AC failure is a `BLOCKER`; other work
is a `FOLLOW-UP` or `SUGGESTION`. Same-agent delta rechecks are used only where
the runtime supports resume; otherwise the stable finding ledger or packet is
carried forward. Progress updates are sparse and state-changing.

Durable artifacts are created only when cross-turn reuse is valuable, under:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

## Update And Verify

After updating the checkout, rerun the same install target and check installed-surface consistency:

```bash
git pull --ff-only
./install.sh codex
./scripts/check-update.sh --no-fetch
```

To include a project-local installation in the check:

```bash
./scripts/check-update.sh --project /path/to/project
```

[`VERSION`](VERSION) is the package version source of truth and stays aligned with the plugin manifests. Before repository changes or a release, run:

```bash
./scripts/validate.sh
python3 scripts/check-codex-routing.py
python3 scripts/eval-teamwork.py --split dev
python3 scripts/run-teamwork-live-eval.py --help
python3 scripts/audit-codex-sessions.py --help
```

`check-codex-routing.py` performs read-only checks of the Teamwork agent
contract, routing config, model/effort support in the current bundled catalog,
and prompt loading. It does not call a model or mutate the catalog; after a
Codex upgrade, use a fresh schema/live spawn probe for behavioral proof.

## Documentation

- [CODEX.md](CODEX.md): Codex installation, project setup, subagents, Goal Mode, and model profiles.
- [CURSOR.md](CURSOR.md): Cursor installation, User Rules, Task subagents, and goal records.
- [CLAUDE.md](CLAUDE.md): Claude Code installation, Task subagents, and goal records.
- [CHANGELOG.en.md](CHANGELOG.en.md): user-visible release changes.
- [CONTRIBUTING.md](CONTRIBUTING.md): issue reports, change scope, and required verification.
- [`skills/*/SKILL.md`](skills/): source definitions for workflow behavior.

Report problems and suggestions through [GitHub Issues](https://github.com/JinPLu/Teamwork/issues).
