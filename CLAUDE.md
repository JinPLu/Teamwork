# Claude Code Usage

This is the Claude Code runtime profile of Teamwork. Claude Code native capabilities are the execution substrate: editing, shell, MCP, permissions, `Task` subagents, TodoWrite, and verification. Teamwork defines when and how those capabilities should be combined for evidence-heavy, reviewed, delegated, or autonomous work. After Teamwork activates, the main agent upgrades from native flow only when evidence, planning, dispatch, review, memory, or goal convergence improves correctness, continuity, or cost.

## Install

```bash
./install.sh claude
./install.sh claude --profile cost-first
./install.sh claude-agents
# print the bootstrap block for manual review:
./install.sh claude-policy
# or refresh every platform:
./install.sh all
```

Project-local agents in a checkout:

```bash
./install.sh project
```

Local development with symlinks:

```bash
./install.sh --link claude
./install.sh --link claude-agents
./install.sh --link all
```

Skills install to `~/.claude/skills/`. Subagents install from
`templates/claude-agents/` to `~/.claude/agents/` (or `.claude/agents/` via
`project`). `./install.sh claude` also writes the Teamwork-managed block into
`~/.claude/CLAUDE.md`. Behavior lives in `skills/`; this file is a concise
runtime summary.

## Native Capability Policy

- Goals: Claude Code has no native `create_goal` surface. Goal-mode work uses the same controller loop, Stop Rules, and Research + Plan Adequacy Gate as Cursor: a chat-only `Goal Proposal` for approval, then a rolling report under `docs/teamwork/reports/` as durable goal state.
- Planning and execution: route non-trivial implementation requests to `teamwork-plan` before edits only after evidence is sufficient; unclear source, evidence, or repro surface routes to `teamwork-research` first; reproducible or likely reproducible failures that need runtime evidence route to `teamwork-debug`; accepted root-cause fixes route to `teamwork-execute`. Plan `Dispatch Guidance:` or durable `Subagent Routing` is routing guidance, not the only dispatch authorization. Route accepted, approved, resumed, or continued plans to `teamwork-execute` for bounded edits, focused verification, and a record of actual dispatch used. TodoWrite is visible transient progress. Durable execution memory lives in `docs/teamwork/plans/` only when artifact triggers apply.
- Project initialization: use `teamwork-init` to initialize or slim `AGENTS.md`, `CLAUDE.md`, `docs/teamwork/`, CodeGraph policy/index when available, MCP policy, appendix navigation, and Teamwork artifact integration. Missing Teamwork-managed global/project surfaces are installed directly; keep reusable workflow in Teamwork and project facts in project instructions.
- Subagents: Teamwork activation is standing authorization for stage-routed dispatch through Claude Code's `Task` tool; the user does not need to say "fan out subagents". After Teamwork activates, the main agent orchestrates and dispatches Explorer, Designer, Judge, Worker, or Reviewer subagents for independent evidence, design, implementation, or review tracks when they have clear evidence, elapsed-time, context-isolation, ownership, or fresh-review value. Prefer installed Teamwork agents under `~/.claude/agents/` by `name`; fall back to built-in `Explore`, `general-purpose`, or role-in-prompt when unavailable. Explorer/Reviewer default max 3. Worker has no fixed cap; >3 Workers require ownership map, integration order, verification plan, and a rationale that parallel is cheaper than serial. Worker agents use `isolation: worktree` when installed. If required fresh review is unavailable after discovery or explicitly disabled, label the result unreviewed.
- Subagent lifecycle: subagents return one packet and stop. The main agent closes, blocks, or abandons each Actual Dispatch Log entry after integration before final acceptance.
- Review: Claude Code does not ship a built-in review command. Use a `Task` dispatch to a Reviewer subagent (custom `code-reviewer` or `deep-reviewer` agent, or `general-purpose` with reviewer role in the prompt). Completion still requires direct mapping to requirements, diffs, tests, artifacts, or acceptance evidence.
- Permissions: use Claude Code native approval and tool-permission flows. Teamwork should identify destructive risk, credentials, unclear ownership, or protected boundaries before dispatch or execution.
- MCP and plugins: prefer native Claude Code tools and connectors. Record source limits when unavailable access affects research or acceptance.
- Version updates: use `teamwork-update`; update `VERSION`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json` together, then refresh Teamwork-managed skills, agents, and global policy.

## Bootstrap Policy

`./install.sh claude` maintains a Teamwork-managed block in global
`~/.claude/CLAUDE.md`. `./install.sh claude-policy` prints the same block for
manual review. The block is a short bootstrap policy: subagent authorization,
act-by-default posture, Claude model profile, no-silent-defaults safety, and
remote-execution baseline. Keep project `CLAUDE.md` or a Claude-labeled
`AGENTS.md` section only for repository facts, exceptions, required values,
protected boundaries, or opt-outs.

## Init Mode

`./install.sh claude --profile performance-first|cost-first` sets the global
Claude profile and generates installed Teamwork subagents.
`performance-first` is default: routine Explorer/Designer/Worker use `sonnet`
with medium effort; Judge/Reviewer use `opus` with high effort; Deep
Judge/Reviewer use `opus` with xhigh effort. `cost-first` downshifts routine
roles to `haiku` with medium effort; review tiers stay frontier. Project init
records only explicit overrides; model-changing overrides require refreshing
agents with `install.sh --profile`.

## Evidence And Artifacts

Use repo files, logs, tests, diffs, artifacts, and prior Teamwork artifacts before new research. Use external calibration from official docs, papers, release notes, upstream issues, or other primary sources when current platform, model, dependency, API, or field practice can affect the result.

For broad research, keep recall broad but context transport narrow: use source census,
capped Explorer packets, and artifact-backed evidence ledgers instead of returning
raw search output, long matrices, or copied source bodies to the main thread.
Treat compaction as continuity support, not audit evidence.

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

Use them for goal-mode, failed iteration, cross-agent execution, cross-turn work, high-risk or ambiguous changes, public/shared behavior, external calibration, and explicit repository-plan requests. Execution or report artifacts should record the actual dispatch decision and subagents used, including the allowed exception when no dispatch happened. Small low-risk edits can stay in native Claude Code chat with TodoWrite progress.

When `docs/teamwork/index.json` exists and durable memory is relevant, Teamwork
routes read it before historical artifacts. Stages report `Memory Delta` only
when durable memory was checked or changed.

For failed goal iterations, refresh research and check whether the active plan was under-informed, stale, wrong-scope, over-strict, or deviated from during execution before retrying. Revise and review the durable plan when new evidence changes the path.

## Subagent Mapping

Teamwork keeps conceptual roles (Explorer, Designer, Judge, Worker, Reviewer) and model classes (`cheap-fast`, `balanced`, `coding`, `frontier`, `inherited`) platform-neutral. At dispatch time, use `skills/using-teamwork/references/subagent-dispatch.md` for the decision and native Claude Code field mapping. Very large work may use `workflow-orchestration.md` and map to Claude Code dynamic workflows when available:

- Explorer -> `explore`
- Worker -> `worker` (worktree isolation when installed)
- Designer -> `designer`
- Judge -> `judge`
- Reviewer -> `code-reviewer`
- Deep Judge -> `deep-judge`
- Deep Reviewer -> `deep-reviewer`

Model class and `effort` are set on the Claude Code agent definition
(`~/.claude/agents/<name>.md` frontmatter), not per `Task` call. Map model
classes at agent-definition time: `cheap-fast` -> `haiku`; `balanced` or
`coding` -> `sonnet`; `frontier` -> `opus`. Use `inherited` (omit `model`) when
parent reasoning is appropriate.

Plan `Dispatch Guidance:` is advisory; the active stage owns the actual dispatch decision and should record what it did when execution/report artifacts are warranted. Preserve native flow only for simple tasks where orchestration overhead would not improve correctness.

## Router

`using-teamwork` is the automatic lean entrypoint. It routes runtime diagnosis to
`teamwork-debug` as a first-class stage without adding a new role. Stage skills
load focused references only as needed.
