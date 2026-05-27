# Codex Usage

This is the Codex runtime profile of Teamwork. Codex native capabilities remain the substrate: goals, `update_plan`, subagents, review, sandbox approvals, automations, MCP, and plugins. Teamwork defines when and how those capabilities should be combined for evidence-heavy, reviewed, delegated, or autonomous work. After Teamwork activates, the main agent acts as the orchestrator: simple tasks can stay native, while non-lightweight research, plan, execute, review, and goal work proactively evaluates subagent dispatch.

Install:

```bash
./install.sh
```

The behavior contract lives in `skills/`. `using-teamwork` is the automatic lean entrypoint and router. It is intentionally broad so it can load for coding-agent work and then choose native flow or a Teamwork route. `teamwork-init` owns project instruction setup and slimming. Stage skills stay lightweight and load focused references only as needed; subagent detail is split across `dispatch-policy`, `subagent-prompt-contract`, and `subagent-packets` instead of one large routing reference. `VERSION` is the package version source of truth and must match `.codex-plugin/plugin.json`. Treat names, comments, README claims, summaries, and tool output as evidence to verify, not facts by themselves.

## Native Capability Policy

- Goals: native Codex goal state is the source of truth for autonomous target and lifecycle. For unclear targets, first return a chat-window `Goal Proposal`; after human approval or edits, call `create_goal` with the `Native Codex Goal Text`.
- Planning and execution: route non-trivial implementation requests to `teamwork-plan` before edits only after evidence is sufficient; unclear root/source/API/failure/evidence/risk routes to `teamwork-research` first. Plan `Dispatch Guidance:` or durable `Subagent Routing` is routing guidance, not the only dispatch authorization. Route accepted, approved, resumed, or continued plans to `teamwork-execute` for bounded edits, focused verification, and a record of actual dispatch used. `update_plan` is visible transient progress. Durable execution memory lives in `docs/teamwork/plans/` only when artifact triggers apply.
- Project initialization: use `teamwork-init` to audit or slim `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, MCP policy, appendix navigation, and Teamwork artifact integration. Keep reusable workflow in Teamwork and project facts in project instructions.
- Subagents: use stage-routed proactive dispatch. After Teamwork activates, the main agent is the orchestrator; non-lightweight research, plan, execute, review, and goal stages evaluate and dispatch Explorer, Designer, Judge, Worker, or Reviewer subagents when parallel evidence gathering, design scrutiny, implementation, or review is cheaper or safer than serial main-agent work. If `spawn_agent` is not active but `tool_search` exists, discover it before claiming subagents are unavailable. Explorer/Reviewer default max 3. Worker has no fixed cap; >3 Workers require ownership map, integration order, verification plan, and a rationale that parallel is cheaper than serial. Non-lightweight acceptance requires a fresh Reviewer; if subagents are unavailable after discovery or explicitly disabled, label the result unreviewed.
- Review: `codex review --uncommitted`, `--base`, or `--commit` can support a verdict. Completion still requires direct mapping to requirements, diffs, tests, artifacts, or acceptance evidence.
- Sandbox and permissions: use Codex native approval flows. Teamwork should identify destructive risk, credentials, unclear ownership, or protected boundaries before dispatch or execution.
- Automations and heartbeats: use Codex native automation/thread heartbeat for recurring checks or later continuation. Teamwork artifacts do not store schedules.
- MCP and plugins: prefer native Codex tools and connectors. Record source limits when unavailable access affects research or acceptance.
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

Use them for goal-mode, failed iteration, cross-agent execution, cross-turn work, high-risk or ambiguous changes, public/shared behavior, external calibration, and explicit repository-plan requests. Execution or report artifacts should record the actual dispatch decision and subagents used, including why main-agent continuity was chosen when no dispatch happened. Small low-risk edits can stay in native Codex chat/progress.

For failed goal iterations, refresh research and check whether the active plan was under-informed, stale, wrong-scope, over-strict, or deviated from during execution before retrying. Revise and review the durable plan when new evidence changes the path.

## Subagent Mapping

Use focused subagent references at dispatch time: `skills/using-teamwork/references/dispatch-policy.md` for when to dispatch, cap/economics rules, native Codex dispatch fields, and role-specific model classes; `skills/using-teamwork/references/subagent-prompt-contract.md` for prompt shape and `Native Fields`; and `skills/using-teamwork/references/subagent-packets.md` for Worker / Reviewer handoff packets. Plan `Dispatch Guidance:` is advisory; the active stage owns the actual dispatch decision and should record what it did when execution/report artifacts are warranted:

- Explorer -> `agent_type:"explorer"`.
- Worker -> `agent_type:"worker"`.
- Designer, Judge, Reviewer -> `agent_type:"default"` with the conceptual role in the prompt.
- `fast`, `standard`, and `high reasoning` map to low, medium, and high reasoning effort.
- Model policy prefers fewer, stronger models: Explorer may use `cheap-fast` only for narrow read-only evidence work; Judge/Reviewer default to `frontier`; Worker defaults to `coding` or inherited; high-risk, public-behavior, or adequacy-gate work does not use `cheap-fast`.

Do not encode native dispatch fields in ordinary plans unless they are part of the routing guidance. Preserve native flow for simple tasks where orchestration overhead would not improve correctness.
