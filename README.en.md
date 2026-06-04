# Teamwork

[中文](README.md)

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**:
a validated collaboration protocol for coding agents. Each platform's native capabilities are the execution substrate
for editing, shell, MCP, permissions, browser work, and verification; Teamwork adds stage routing, role dispatch,
evidence packets, fresh review, reusable memory, and goal convergence until a
verifiable result or a real blocker is reached.

![Teamwork workflow banner](assets/teamwork-hero.png)

## Why Teamwork

- Non-lightweight work moves from one-agent guessing into bounded stages:
  evidence, design, plan, execute, review, and goal.
- Important conclusions must map to source, diffs, logs, tests, artifacts, or
  primary sources; names and summaries are only claims.
- Subagents are bounded packet producers: they return once, while the main
  agent integrates, closes dispatch tracks, verifies, and delivers.
- Goal loops iterate until the target is met, budget is exhausted, progress
  stalls, or a real blocker appears.
- Durable artifacts and optional index/current memory reduce repeated research
  across turns.

## Core Capabilities

| Capability | What Teamwork Does |
|---|---|
| Evidence first | Maps key claims to direct evidence and labels `observed` / `inferred` / `claimed`. |
| Stage router | `using-teamwork` routes `teamwork-init`, research, plan, execute, review, update, and goal work. |
| Role workflow | Explorer gathers evidence, Designer chooses, Judge reviews plans, Worker executes slices, Reviewer fresh-reviews results. |
| Proactive dispatch | After authorization, independent non-lightweight work dispatches roles by default; skips need `Dispatch Exception`. |
| Packet contracts | Every role returns a fixed packet with scope, evidence, verification, risk, and closure data. |
| Goal convergence | Codex uses native goals and Goal Text; Cursor/Claude Code use rolling reports. |
| Artifact memory | Research, plans, and reports preserve reusable evidence, plans, conclusions, and failed attempts. |
| Validation | `./scripts/validate.sh` locks skill topology, manifests, packet fields, templates, and doc contracts. |

## Workflow And Roles

Common path:

```text
research -> design/plan -> execute -> verify -> review -> report or goal update
```

| Role | Responsibility | Output |
|---|---|---|
| Explorer | Gather evidence, refresh assumptions, run web/deep research or source audit | Evidence packet |
| Designer | Compare options, define constraints and success criteria, recommend a direction | Decision packet |
| Judge | Review pre-execution plan evidence, boundaries, guardrails, and acceptance gaps | `accept` / `revise` / `blocked` |
| Worker | Implement accepted scope with TDD, root-cause, and verification evidence | Completion packet |
| Reviewer | Fresh-context review of diffs, tests, artifacts, PR/CI evidence | Verdict packet |

Deep Judge and Deep Reviewer are high-risk review profiles for failed goals,
security, destructive risk, public contracts, or release acceptance.

## Good Fit / Not A Fit

Good fit:

- Coding-agent work that needs investigation, planning, execution,
  verification, and review to stay connected.
- Codex subagents that proactively handle exploration, implementation, review,
  and research instead of waiting for the user to push each step.
- Cross-turn evidence, plans, results, or failed attempts that should be reused.
- Goal-directed work that should iterate until a verifiable target is reached.

Not a fit: one-line facts, tiny obvious edits, sensitive/destructive
operations, tightly coupled critical paths, or work where subagent context cost
exceeds the benefit.

## Install

Codex-first default install:

```bash
./install.sh              # same as ./install.sh codex
./install.sh codex --profile cost-first
```

Adapter and all-platform installs:

```bash
./install.sh cursor
./install.sh claude          # Claude Code skills only
./install.sh claude-agents   # Claude Code agents only
./install.sh all             # all supported skills + Codex/Claude agents
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

Codex installs use `performance-first` by default. It generates role-optimized
Codex agents; `cost-first` downshifts only routine Explorer / Designer /
Worker while keeping high-risk Judge / Reviewer on stronger model tiers.

## Platform Positioning

Codex is the reference runtime: native goals are the autonomous control plane,
and `teamwork_*` custom agents are the primary collaboration network for
non-lightweight work. Codex calls `spawn_agent` only when the user prompt or
loaded global/project rules provide standing authorization.

Cursor and Claude Code are adapters: they reuse the same Teamwork protocol
while keeping their own native capabilities. Cursor uses Task subagents; Claude
Code skills install through `./install.sh claude`, while `explore`, `worker`,
and `code-reviewer` agents install through `./install.sh claude-agents`, `all`,
or `project`, with rolling reports for goal mode.

## Memory And Version

Teamwork artifacts:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

`VERSION` is the package version source of truth and must match
`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`; version,
manifest, and release-surface updates use `teamwork-update`.

## Read More

- [CODEX.md](CODEX.md): Codex runtime profile, Goal Text, and custom-agent mapping.
- [CURSOR.md](CURSOR.md): Cursor adapter.
- [CLAUDE.md](CLAUDE.md): Claude Code adapter.
- `skills/*/SKILL.md`: stage skill behavior.
- `skills/using-teamwork/references/`: dispatch, packet, artifact, review, and goal details.

Validate the repository:

```bash
./scripts/validate.sh
```
