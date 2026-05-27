# Teamwork

[中文](README.md)

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork is a **Codex + Cursor + Claude Code skill package**. Each platform's native capabilities are the execution substrate: Codex provides native goals, `update_plan`, and `spawn_agent`; Cursor provides `Task` subagents, MCP, browser automation, and permissions; Claude Code provides `Task` subagents (user-defined under `~/.claude/agents/`), TodoWrite, MCP, and permissions. Teamwork adds the collaboration policy that makes complex coding-agent work more reliable: evidence first, reusable artifacts, stage-routed proactive dispatch, reviewed execution, and goal iteration that does not stop early.

After Teamwork activates, the main agent acts as the orchestrator. Simple tasks stay in native platform flow; non-lightweight research, plan, execute, review, and goal work proactively evaluates subagent dispatch instead of waiting for user or plan authorization.

## Core Advantages

| Advantage | What Teamwork Adds |
|---|---|
| Evidence first | Important claims must come from source, diffs, logs, tests, artifacts, or primary external sources. File names, README prose, comments, stale summaries, and `latest` labels are claims; `implement/fix` routes to research first when root/source/API/failure/evidence/risk is unclear. |
| Better platform goals | Unclear autonomous requests first get a chat-window `Goal Proposal`. After approval, Codex calls `create_goal` with the Goal Text; Cursor and Claude Code initialize a rolling report as durable goal state and drive the controller loop from chat. Failed attempts return to research + plan adequacy instead of early block. |
| Artifact memory | `research/`, `plans/`, and `reports/` preserve reusable evidence, execution memos, rolling attempts, verification, review, and routing decisions so work does not repeat or bloat the chat context. |
| Retrieval headers | Durable artifacts start with type, status, updated date, search keys, abstract, and linked artifacts so future agents can find the right memory before full-text search. |
| Stage-routed dispatch | Teamwork uses subagent-first orchestration after activation. Research / plan / execute / review / goal stages proactively evaluate Explorer, Designer, Judge, Worker, or Reviewer dispatch for non-lightweight work. Codex uses `spawn_agent`; Cursor and Claude Code use `Task`. On Codex, if `spawn_agent` is inactive but `tool_search` exists, tools must be discovered before being called unavailable. Non-lightweight acceptance needs a fresh Reviewer, and self-review is not acceptance. |

## Skill Map

`using-teamwork` is the automatic lean entrypoint and router. Stage skills stay lightweight and load only the references needed for the active stage; subagent detail is progressively disclosed through focused references instead of one large `subagent-routing` reference.

| User Intent | Skill | Output |
|---|---|---|
| Initialize or slim project agent rules | `teamwork-init` | Project rule layering, MCP/CodeGraph boundaries, appendix, and artifact integration plan |
| Investigate causes, compare options, refresh stale assumptions | `teamwork-research` | Direct evidence, external calibration, reusable research artifact when warranted |
| Plan or prepare a non-trivial change | `teamwork-plan` | Lightweight checklist or durable execution memo |
| Execute an accepted, approved, continued, or resumed plan | `teamwork-execute` | Minimal scoped edits and focused verification |
| Review a plan, diff, artifact, or result | `teamwork-review` | Evidence-based verdict with dissent and required fixes |
| Update version, release metadata, or skill topology | `teamwork-update` | Synchronized `VERSION`, manifest, docs, install, and validation |
| Iterate until a verifiable target is reached | `teamwork-goal` | Goal Proposal, native goal handoff, iteration loop, rolling report when needed |

Subagent references are split by responsibility: `dispatch-policy` defines when to dispatch, caps/economics, Codex/Cursor/Claude Code dispatch fields, and role-specific model class; `subagent-prompt-contract` defines prompt shape plus `Native Fields`; and `subagent-packets` defines Worker / Reviewer handoff packets. Plan `Dispatch Guidance:` is advice; the active stage still owns actual dispatch through stage-routed proactive dispatch.

## Platform Native Policy Map

| Platform Capability | Teamwork Policy |
|---|---|
| Codex goal | Source of truth for autonomous target and lifecycle. Teamwork designs the goal, evidence, scope, retry policy, and acceptance checks before `create_goal`. |
| Cursor goal | Without native goal state, goal-mode uses chat iteration plus durable reports; do not force `create_goal`. |
| Claude Code goal | Same as Cursor: no native goal state; goal-mode uses chat iteration plus rolling reports. |
| `update_plan` / TodoWrite | Visible progress only. It is not a durable execution spec, review target, or completion proof. |
| Subagents | Stage-routed proactive dispatch. After Teamwork activates, the main agent is the orchestrator; non-lightweight research, plan, execute, review, and goal work proactively evaluates and dispatches subagents. Codex uses `spawn_agent` and prefers `teamwork_*` custom agents; Cursor and Claude Code use `Task` (Claude Code's `subagent_type` references a user-defined agent under `~/.claude/agents/`; fall back to `general-purpose` when no specialized agent exists). Plan `Dispatch Guidance:` or `Subagent Routing` is guidance, not the only authorization. On Codex, if `spawn_agent` is missing from active tools but `tool_search` exists, discover it first. Skipped required dispatch must emit `Dispatch Exception:`. Explorer/Reviewer default max 3; Worker has no fixed cap. Non-lightweight review may skip a fresh Reviewer only when subagent discovery fails or the user opts out, and must be labeled `unreviewed`. Model policy prefers fewer, stronger models: Codex custom agents pin role models directly; fallback dispatch passes explicit Role Profile models; `cheap-fast` is only for explicit latency/quota pressure on trivial read-only work. |
| Review | Platform review output can be evidence, but completion still maps to requirements, diff, tests, artifacts, and acceptance criteria. |
| Sandbox/permissions | Use native approval and sandbox model for the active platform. Teamwork only requires boundaries and risks to be explicit. |
| Automations/heartbeat | Codex uses native automation or thread heartbeat for recurring checks or later continuation. Do not encode schedules in Teamwork artifacts. |
| MCP/plugins | Prefer native tools and connectors. Teamwork requires sources and limitations to be recorded when they affect decisions. |
| Project instructions | `teamwork-init` initializes or slims `AGENTS.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md`, migrating reusable workflow into Teamwork while leaving project facts in the project. |

Package version uses `VERSION` as the source of truth and must match
`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`. Version, release
metadata, or skill surface updates use `teamwork-update`.

## Goal Proposal

For unclear autonomous work, Teamwork returns this in chat before platform goal handoff:

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, sacred boundaries>
- Iteration Budget: <default 3 if unspecified, or user-specified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested research/plan/report paths and why>
- Subagent Routing: <suggested tracks to split, or why main-agent continuity is better>
- Goal Text: <concise target for platform goal handoff>
```

The proposal is a human review gate. Codex writes the Goal Text into `create_goal`; Cursor and Claude Code write it into the rolling report Abstract and start the controller loop.

## Artifacts

Artifacts are evidence memory, not a replacement for the platform goal surface. Create them only when they reduce repeated work or anchor cross-turn, cross-agent, high-risk, ambiguous, public/shared, explicitly planned, or goal-mode work.

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

| Directory | Role | Review Question |
|---|---|---|
| `research/` | Reusable investigation and external calibration | What evidence was read, and which findings are observed/inferred/claimed? |
| `plans/` | Execution memo and review source of truth | Are goal, scope, steps, verification, risks, handoffs, and routing guidance clear? |
| `reports/` | Goal rolling memory and durable conclusions | What was tried, verified, reviewed, reused, and actually dispatched? |

Every durable artifact begins with `Artifact Type`, `Status`, `Last Updated`,
`Search Keys`, `Abstract`, and `Linked Artifacts`. The abstract helps retrieval;
completion still requires direct evidence from commands, diffs, tests,
artifacts, or inspected behavior.

These directories are gitignored unless the user intentionally asks to publish a specific artifact.

## Install

Install all platforms (recommended after upgrades):

```bash
./install.sh all
./install.sh codex-agents
./install.sh claude-agents
```

Per platform:

```bash
./install.sh codex
./install.sh cursor
./install.sh claude
./install.sh codex-agents
```

Project-local Cursor skills, Codex agents, and Claude agents in this checkout
(`.cursor/skills/`, `.codex/agents/`, and `.claude/agents/`, all gitignored):

```bash
./install.sh project
```

Claude Code Teamwork subagents (`explore`, `worker`, `code-reviewer`):

```bash
./install.sh claude-agents
```

Use `--link` during local development:

```bash
./install.sh --link all
./install.sh --link project
```

**Cursor note**: prefer `~/.cursor/skills/` or project `.cursor/skills/`. Stale
`~/.claude/skills/` copies (especially retired `teamwork`) can steal routing;
refresh with `./install.sh all`.

Validate this repository:

```bash
./scripts/validate.sh
```

Behavior lives in `skills/*/SKILL.md`; `README.md`, `CODEX.md`, `CURSOR.md`, and `CLAUDE.md` are concise runtime summaries.
