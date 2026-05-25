# Teamwork

[中文](README.md)

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork is a **Codex-only skill package**. Codex native capabilities are the execution substrate: native goals, `update_plan`, subagents, review, sandbox approvals, automations, MCP, and plugins still do the work. Teamwork adds the collaboration policy that makes complex coding-agent work more reliable: evidence first, reusable artifacts, stage-routed proactive dispatch, reviewed execution, and goal iteration that does not stop early.

After Teamwork activates, the main agent acts as the orchestrator. Simple tasks still stay in Codex native flow; non-lightweight research, plan, execute, review, and goal work proactively evaluates subagent dispatch instead of waiting for user or plan authorization.

## Core Advantages

| Advantage | What Teamwork Adds |
|---|---|
| Evidence first | Important claims must come from source, diffs, logs, tests, artifacts, or primary external sources. File names, README prose, comments, stale summaries, and `latest` labels are treated as claims until corroborated. |
| Better native goals | Unclear autonomous requests first get a chat-window `Goal Proposal`. After human approval, its `Native Codex Goal Text` is used with Codex native goal state. Failed attempts return to research + plan adequacy instead of early block. |
| Artifact memory | `research/`, `plans/`, and `reports/` preserve reusable evidence, execution memos, rolling attempts, verification, review, and routing decisions so work does not repeat or bloat the chat context. |
| Retrieval headers | Durable artifacts start with type, status, updated date, search keys, abstract, and linked artifacts so future agents can find the right memory before full-text search. |
| Stage-routed dispatch | Teamwork uses subagent-first orchestration after activation. Research / plan / execute / review / goal stages proactively evaluate Explorer, Designer, Judge, Worker, or Reviewer dispatch for non-lightweight work; plan routing is guidance and forecasting, not the sole authorization source. |

## Skill Map

`using-teamwork` is the automatic lean entrypoint and router. Stage skills stay lightweight and load only the references needed for the active stage; subagent detail is progressively disclosed through focused references instead of one large `subagent-routing` reference.

| User Intent | Skill | Output |
|---|---|---|
| Investigate causes, compare options, refresh stale assumptions | `teamwork-research` | Direct evidence, external calibration, reusable research artifact when warranted |
| Plan or prepare a non-trivial change | `teamwork-plan` | Lightweight checklist or durable execution memo |
| Execute an accepted, approved, continued, or resumed plan | `teamwork-execute` | Minimal scoped edits and focused verification |
| Review a plan, diff, artifact, or result | `teamwork-review` | Evidence-based verdict with dissent and required fixes |
| Update version, release metadata, or skill topology | `teamwork-update` | Synchronized `VERSION`, manifest, docs, install, and validation |
| Iterate until a verifiable target is reached | `teamwork-goal` | Goal Proposal, native goal handoff, iteration loop, rolling report when needed |

Subagent references are split by responsibility: `dispatch-policy` defines when to dispatch plus caps/economics and native Codex dispatch-field mapping, `subagent-prompt-contract` defines prompt shape, and `subagent-packets` defines Worker / Reviewer handoff packets. Plan `Dispatch Guidance:` is advice; the active stage still owns actual dispatch through stage-routed proactive dispatch.

## Codex Native Policy Map

| Codex Capability | Teamwork Policy |
|---|---|
| Native goal | Source of truth for autonomous target and lifecycle. Teamwork designs the goal, evidence, scope, retry policy, and acceptance checks before `create_goal`. |
| `update_plan` | Visible progress only. It is not a durable execution spec, review target, or completion proof. |
| Subagents | Stage-routed proactive dispatch. After Teamwork activates, the main agent is the orchestrator; non-lightweight research, plan, execute, review, and goal work proactively evaluates and dispatches subagents. Plan `Dispatch Guidance:` or `Subagent Routing` is guidance, not the only authorization. Explorer/Reviewer default max 3; Worker has no fixed cap, but >3 requires ownership, integration, and verification rationale. |
| Review | Codex review output can be evidence, but completion still maps to requirements, diff, tests, artifacts, and acceptance criteria. |
| Sandbox/permissions | Use Codex native approval and sandbox model. Teamwork only requires boundaries and risks to be explicit. |
| Automations/heartbeat | Use native Codex automation or thread heartbeat for recurring checks or later continuation. Do not encode schedules in Teamwork artifacts. |
| MCP/plugins | Prefer native Codex tools and connectors. Teamwork requires sources and limitations to be recorded when they affect decisions. |

Package version uses `VERSION` as the source of truth and must match
`.codex-plugin/plugin.json`. Version, release metadata, or skill surface updates
use `teamwork-update`.

## Goal Proposal

For unclear autonomous work, Teamwork returns this in chat before creating a native Codex goal:

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
- Native Codex Goal Text: <concise text prepared for create_goal>
```

The proposal is a human review gate. The approved `Native Codex Goal Text` is what should be written into native Codex goal state.

## Artifacts

Artifacts are evidence memory, not a replacement for native Codex goal state. Create them only when they reduce repeated work or anchor cross-turn, cross-agent, high-risk, ambiguous, public/shared, explicitly planned, or goal-mode work.

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

```bash
./install.sh
```

Equivalent explicit form:

```bash
./install.sh codex
```

Use `--link` during local development:

```bash
./install.sh --link
```

Validate this repository:

```bash
./scripts/validate.sh
```

Behavior lives in `skills/*/SKILL.md`; `README.md` and `CODEX.md` are concise runtime summaries.
