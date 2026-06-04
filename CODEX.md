# Codex Usage

This is the Codex runtime profile and reference runtime of Teamwork. Codex native capabilities remain the substrate: goals, `update_plan`, custom agents, review, sandbox approvals, permission profiles, automations, MCP, plugins, diagnostics, Appshots/browser evidence, Computer Use, and remote/Windows support. Teamwork defines when and how those capabilities should be combined for evidence-heavy, reviewed, delegated, or autonomous work. After Teamwork activates, the main agent acts as orchestrator; native Codex goals are the autonomous control plane, and Teamwork custom agents are the default collaboration network for non-lightweight stages when standing authorization exists.

Install:

```bash
./install.sh
# or refresh every platform:
./install.sh all
# agents-only refresh when skills/global policy should not change:
./install.sh codex-agents
```

The behavior contract lives in `skills/`. `using-teamwork` is the automatic lean entrypoint and router. It is intentionally broad so it can load for coding-agent work and then choose native flow or a Teamwork route. `teamwork-init` owns project instruction setup and slimming. Stage skills stay lightweight and load focused references only as needed; Codex-specific depth lives in `codex-deep-collaboration.md`, dispatch decisions in `dispatch-policy.md`, native field mapping in `platform-dispatch-mapping.md`, and swarm-scale orchestration in `workflow-orchestration.md`. `VERSION` is the package version source of truth and must match `.codex-plugin/plugin.json`. Treat names, comments, README claims, summaries, and tool output as evidence to verify, not facts by themselves.

## Native Capability Policy

- Goals: native Codex goal state is the source of truth for autonomous target and lifecycle. For unclear targets, first return a chat-window `Goal Proposal`; after human approval or edits, call `create_goal` with the `Native Codex Goal Text`.
- Planning and execution: route non-trivial implementation requests to `teamwork-plan` before edits only after evidence is sufficient; unclear root/source/API/failure/evidence/risk routes to `teamwork-research` first. Plan `Dispatch Guidance:` or durable `Subagent Routing` is routing guidance, not the only dispatch authorization. Route accepted, approved, resumed, or continued plans to `teamwork-execute` for bounded edits, focused verification, and a record of actual dispatch used. `update_plan` is visible transient progress. Durable execution memory lives in `docs/teamwork/plans/` only when artifact triggers apply.
- Project initialization: use `teamwork-init` to audit or slim `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, MCP policy, appendix navigation, Teamwork artifact integration, and any project override to the installed Codex profile. Keep reusable workflow in Teamwork and project facts in project instructions. Ask about `performance-first` versus `cost-first` only when the project should differ from the global install default.
- Subagents: Codex requires an explicit request or loaded standing instruction before `spawn_agent` is used. When that authorization exists, Teamwork dispatches proactively for non-lightweight work: Explorer for evidence, Designer/Judge for design and plan adequacy, Worker for independent owned implementation, and Reviewer for fresh-context acceptance. The main agent remains orchestrator and owns scope, integration, verification, and Memory Delta. If `spawn_agent` is not active but `tool_search` exists, discover it before claiming subagents are unavailable. Explorer/Reviewer default max 3. Worker has no fixed cap; >3 Workers require ownership map, integration order, verification plan, and a rationale that parallel is cheaper than serial. Skipping non-lightweight dispatch requires `Dispatch Exception:`. Non-lightweight acceptance requires a fresh Reviewer; if subagents are unavailable, authorization is missing, or dispatch is explicitly disabled, label the result unreviewed.
- Review: `codex review --uncommitted`, `--base`, or `--commit` can support a verdict. Completion still requires direct mapping to requirements, diffs, tests, artifacts, or acceptance evidence.
- Sandbox and permissions: use Codex native approval flows and permission profiles. Teamwork should identify destructive risk, credentials, unclear ownership, filesystem/network boundaries, or protected boundaries before dispatch or execution.
- Automations and heartbeats: use Codex native automation/thread heartbeat for recurring checks or later continuation. Teamwork artifacts do not store schedules.
- Diagnostics and visual evidence: prefer `codex doctor` and `/status` before ad hoc setup debugging when CLI, remote, or connection state matters. Use browser annotations, Appshots, Computer Use, or remote/Windows evidence when visual, desktop, or OS-specific behavior is part of acceptance.
- MCP and plugins: prefer native Codex tools, connectors, and plugins. Record source limits when unavailable access affects research or acceptance.
- Version updates: use `teamwork-update`; update `VERSION` and `.codex-plugin/plugin.json` together.

## Evidence And Artifacts

Use repo files, logs, tests, diffs, artifacts, and prior Teamwork artifacts before new research. Use external calibration from official docs, papers, release notes, upstream issues, or other primary sources when current platform, model, dependency, API, or field practice can affect the result.

Artifacts are evidence memory:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

Every durable artifact starts with a retrieval header: `Artifact Type`,
`Status`, `Last Updated`, `Search Keys`, `Abstract`, and `Linked Artifacts`.
Search these headers first, then full text across research, plans, and reports.
The abstract is a retrieval aid, not completion proof.

Use them for goal-mode, failed iteration, cross-agent execution, cross-turn work, high-risk or ambiguous changes, public/shared behavior, external calibration, and explicit repository-plan requests. Execution or report artifacts should record the actual dispatch decision and subagents used, including the allowed exception when no dispatch happened. Small low-risk edits can stay in native Codex chat/progress.

When `docs/teamwork/index.json` exists and durable memory is relevant, Teamwork
routes read it before historical artifacts. Stages report `Memory Delta` only
when durable memory was checked or changed.

For failed goal iterations, refresh research and check whether the active plan was under-informed, stale, wrong-scope, over-strict, or deviated from during execution before retrying. Revise and review the durable plan when new evidence changes the path.

## Codex Subagent Authorization

`./install.sh codex` maintains a Teamwork-managed block in global
`~/.codex/AGENTS.md`. That block is the preferred portable standing
authorization for subagents and the default remote-execution assumption. Use a
project `CODEX.md` or Codex-labeled `AGENTS.md` section only for repository
exceptions or opt-outs:

```md
For Codex in this repository, this is the user's explicit standing request to
use sub-agents, delegation, and parallel agent work when Teamwork dispatch
policy says it is appropriate. The user does not need to repeat "use
subagents" in each prompt.
```

Keep project authorization short. Detailed dispatch economics stay in
`dispatch-policy.md` and the installed global policy.

## Init Mode

`./install.sh codex --profile performance-first|cost-first` sets the global
Codex profile and generates the installed Teamwork custom agents.
`performance-first` is the Pro/20x default and uses `gpt-5.5` with high
reasoning for Explorer, Designer, Worker, Judge, and Reviewer. `cost-first`
downshifts routine Explorer/Designer/Worker dispatches but keeps Judge,
Reviewer, high-risk, public, and failed-goal work on frontier/high reasoning.
Project init records only explicit overrides; model-changing overrides require
refreshing user or project Codex agents with `install.sh --profile`.

## Subagent Mapping

Use focused subagent references at dispatch time: `skills/using-teamwork/references/dispatch-policy.md` for when to dispatch, `platform-dispatch-mapping.md` for native fields and model classes, `workflow-orchestration.md` for large workflow-class runs, `subagent-prompt-contract.md` for prompt shape, and `subagent-packets.md` for handoff packets. Plan `Dispatch Guidance:` is advisory; the active stage owns the actual dispatch decision and should record what it did when execution/report artifacts are warranted:

- Preferred custom agents -> `agent_type:"teamwork_explorer"`, `"teamwork_worker"`, `"teamwork_designer"`, `"teamwork_judge"`, or `"teamwork_reviewer"`.
- Built-in fallback -> Explorer uses `agent_type:"explorer"`, Worker uses `agent_type:"worker"`, and Designer/Judge/Reviewer use `agent_type:"default"` with the conceptual role in the prompt.
- `fast`, `standard`, and `high reasoning` map to low, medium, and high reasoning effort.
- Prefer installed Teamwork custom agents from `~/.codex/agents` or `.codex/agents`: `teamwork_explorer`, `teamwork_worker`, `teamwork_designer`, `teamwork_judge`, and `teamwork_reviewer`. In performance-first mode they pin all role models directly to `gpt-5.5` with high reasoning. If custom agents are unavailable, fall back to built-in `explorer`, `worker`, or `default` with explicit model overrides from `dispatch-policy.md`; do not let subagents inherit an unintended parent model by accident. Without custom agents, Designer/Judge/Reviewer appear as `default` subagents in Codex UI because Codex has no native role-specific agent types for them. `cheap-fast` is opt-in only for explicit cost-first trivial read-only work under latency or quota pressure.
- Subagents are bounded packet producers. After each packet returns, the orchestrator integrates it and closes, blocks, or abandons the dispatch in the Actual Dispatch Log before final acceptance.

Do not encode native dispatch fields in ordinary plans unless they are part of the routing guidance. Preserve native flow only for quick facts, tiny obvious edits, destructive/credential-sensitive work, tightly coupled critical-path work, unavailable tools, missing authorization, explicit user opt-out, or cases where subagent context cost exceeds value.
