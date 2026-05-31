# Teamwork

[中文](README.md)

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**.
Each platform's native capabilities are the execution substrate; Teamwork adds
one collaboration protocol: evidence first, proactive dispatch, reusable memory,
fresh review, and goal loops that keep moving until there is verified evidence.

Codex is the 1.0 reference runtime. Native Codex goals are the autonomous
control plane, and `teamwork_*` custom agents are the default collaboration
network for non-lightweight work. Cursor and Claude Code use the same Teamwork
protocol as adapters.

## What It Is For

- Coding-agent work that needs investigation, planning, execution, verification,
  and review to stay connected.
- Codex subagents that proactively handle exploration, implementation, review,
  and research instead of waiting for the user to push each step.
- Cross-turn evidence, plans, results, or failed attempts that should be reused.
- Goal-directed work that should iterate until a verifiable target is reached.

Not for: one-line facts, tiny obvious edits, sensitive/destructive operations,
tightly coupled critical paths, or work where subagent context cost exceeds
the benefit.

## What Teamwork Adds

| Capability | Purpose |
|---|---|
| Evidence first | Important claims map to source, diffs, logs, tests, artifacts, or primary sources. |
| Proactive dispatch | Non-lightweight research / plan / execute / review / goal stages dispatch Explorer, Designer, Judge, Worker, or Reviewer by default. Skips need `Dispatch Exception`. |
| Goal control | Unclear goals get a `Goal Proposal`; Codex calls `create_goal` with the Goal Text, while Cursor/Claude Code use rolling reports. |
| Artifact memory | `docs/teamwork/research/YYYY-MM-DD-<slug>.md`, `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`, and `docs/teamwork/reports/YYYY-MM-DD-<slug>.md` preserve reusable evidence and conclusions. |
| Native index | Optional `docs/teamwork/index.json` / `current.md` points agents to current design, results, and progress without rereading history. |
| Memory Delta | Reported only when durable project memory was checked or changed, preventing documentation bloat. |

## Skill Map

`using-teamwork` is the automatic lean entrypoint and router:

| Intent | Skill |
|---|---|
| Initialize or slim project rules | `teamwork-init` |
| Investigate, compare, refresh assumptions | `teamwork-research` |
| Plan a non-trivial change | `teamwork-plan` |
| Execute an accepted plan | `teamwork-execute` |
| Review a plan, diff, or result | `teamwork-review` |
| Update version, manifests, release surface | `teamwork-update` |
| Iterate until a target is reached | `teamwork-goal` |

`VERSION` is the package version source of truth and must match
`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`; version or skill
surface updates use `teamwork-update`.

## Install

Recommended all-platform install:

```bash
./install.sh all
```

Per platform:

```bash
./install.sh codex          # Codex skills + custom agents + global policy
./install.sh cursor
./install.sh claude
./install.sh codex-agents   # only ~/.codex/agents/
./install.sh claude-agents  # only ~/.claude/agents/
```

Project-local install writes gitignored `.cursor/skills/`, `.codex/agents/`,
and `.claude/agents/`:

```bash
./install.sh project
```

Use symlinks for local development:

```bash
./install.sh --link codex
./install.sh --link all
./install.sh --link project
```

## Codex Authorization Model

Codex requires the user prompt or loaded project/global instructions to
explicitly authorize `spawn_agent`. `./install.sh codex` maintains the Teamwork
global policy block in `~/.codex/AGENTS.md`; once authorization exists,
Teamwork proactively dispatches independent non-lightweight stage work. The
main agent still owns scope, ownership, integration, verification, and delivery.

## Read More

- [CODEX.md](CODEX.md): Codex runtime profile and custom-agent mapping.
- [CURSOR.md](CURSOR.md): Cursor adapter.
- [CLAUDE.md](CLAUDE.md): Claude Code adapter.
- `skills/*/SKILL.md`: behavior definitions.
- `skills/using-teamwork/references/`: dispatch, artifact, review, and goal details.

Validate the repository:

```bash
./scripts/validate.sh
```
