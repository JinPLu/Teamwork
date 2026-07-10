# Subagent Dispatch

Dispatch, role mapping, and platform fields. Prompt/result shape ->
`subagent-contract.md`; swarm orchestration -> `workflow-orchestration.md`.

## When To Dispatch

Dispatch when tracks are independent, isolatable, or parallel:

- **Explore**: Explorer for project/source orientation, artifact lookup, literature/source census, or evidence beyond a quick literal read.
- **Research**: Explorer tracks for external calibration, stale assumptions, option comparison, or broad source census.
- **Design**: Designer for ambiguous decisions; Judge for durable, risky, or delegated plans.
- **Execute**: Worker per independent owned slice with disjoint files, components, artifacts, or verification targets.
- **Review**: Reviewer when independent acceptance reduces material risk; fresh
  context only for the high-risk cases in `workflow-contract.md`.

Skip dispatch for quick facts, obvious edits, tightly coupled work, unavailable
tools, missing authorization, user opt-out, or context cost above value. Record
the reason only when it affects review or acceptance.

Use CodeGraph before Explorer fanout for structural code questions.

## Roles

- **Explorer**: gathers evidence; read-only.
- **Designer**: decides architecture and plan shape; read-only.
- **Judge**: reviews plan adequacy before execution; read-only.
- **Worker**: implements owned slices; workspace-write.
- **Reviewer**: checks completed work; read-only.

Deep Judge and Deep Reviewer are severity profiles of Judge and Reviewer, not separate roles.

## Lifecycle

A dispatched subagent returns one packet, then stops. It does not monitor, reopen scope, chain new subagents, or continue after returning its packet.

Main agent records returned packets and blockers in the Actual Dispatch Log for
review. Integration, final verification, and acceptance remain main-thread
responsibilities.

## Platform Fields

Codex uses `agent_type`; Cursor uses `subagent_type`; Claude Code uses `Task`.

**Codex** - role dispatch: `agent_type`, optional model/profile fields supported by the runtime, `reasoning_effort`, `fork_context:false`. Full-history fork: `fork_context:true` only (no other fields).

| Role | agent_type | Fallback |
|---|---|---|
| Explorer | `teamwork_explorer` | `explorer` |
| Worker | `teamwork_worker` | `worker` |
| Designer | `teamwork_designer` | `default` + role in prompt |
| Judge | `teamwork_judge` | `default` + role in prompt |
| Reviewer | `teamwork_reviewer` | `default` + role in prompt |
| Deep Judge | `teamwork_deep_judge` | `default` + role in prompt |
| Deep Reviewer | `teamwork_deep_reviewer` | `default` + role in prompt |

Reasoning effort: `fast`->low, `standard`->medium, `high reasoning`->high, `deep reasoning`->xhigh.

**Cursor** - prefer custom agents from `~/.cursor/agents/` by `name`; fallback `subagent_type` and runtime-supported model fields; no `reasoning_effort` or `fork_context`.

| Role | Custom agent | Fallback subagent_type |
|---|---|---|
| Explorer | `explore` | `explore` |
| Worker | `worker` | `generalPurpose` or `shell` |
| Designer | `designer` | `generalPurpose` + role in prompt |
| Judge | `judge` | `generalPurpose` + role in prompt |
| Reviewer | `code-reviewer` | `code-reviewer` |
| Deep Judge | `deep-judge` | `generalPurpose` + role in prompt |
| Deep Reviewer | `deep-reviewer` | `code-reviewer` + role in prompt |

Use `readonly:true` for Explorer/Judge/Reviewer; `run_in_background:true` for long tracks; `resume:"self"` for full-history fork; `best-of-n-runner` for parallel Worker experiments.

**Claude Code** - prefer custom agents from `~/.claude/agents/` by `name`; fallback `Task` with `general-purpose` and role in prompt. Model, `effort`, tool allowlist, and `isolation: worktree` live on the agent definition, not per Task call.

| Role | Custom agent | Fallback |
|---|---|---|
| Explorer | `explore` | `Explore` or `general-purpose` |
| Worker | `worker` | `general-purpose` |
| Designer | `designer` | `general-purpose` + role in prompt |
| Judge | `judge` | `general-purpose` + role in prompt |
| Reviewer | `code-reviewer` | `general-purpose` + role in prompt |
| Deep Judge | `deep-judge` | `general-purpose` + role in prompt |
| Deep Reviewer | `deep-reviewer` | `general-purpose` + role in prompt |

## Model Classes

| Class | Intended use | Performance-first expectation | Cost-first expectation |
|---|---|---|---|
| `cheap-fast` | trivial read-only evidence under explicit latency/quota pressure | fast inexpensive model | fast inexpensive model |
| `balanced` | routine Explorer/Designer work | strong mid/frontier model, medium effort | cheaper strong model, medium effort |
| `coding` | Worker implementation slices | coding-optimized model or inherited parent | cheaper coding model or inherited parent |
| `frontier` | Judge, Reviewer, public contracts, ambiguous architecture | frontier model, high effort | keep frontier for risk review |
| `deep reasoning` | failed-goal recovery, security/destructive/release acceptance | frontier model, deepest effort | frontier model, deepest effort |
| `inherited` | simple local continuation where parent context is the value | omit model override | omit model override |

Role defaults: Explorer->`balanced` (use `frontier` for broad/ambiguous/high-risk); Designer->`balanced` (use `frontier` for architecture or public contracts); Judge->`frontier` high reasoning; Worker->`coding` or `inherited`; Reviewer->`frontier` high reasoning.

`performance-first` is the default on all platforms. `gpt56-role` is the
role-tiered Codex profile: Explorer=`gpt-5.6-terra` medium;
Worker=`gpt-5.6-sol` medium; Designer/Judge/Reviewer=`gpt-5.6-sol` high; Deep
Judge/Reviewer=`gpt-5.6-sol` max. `gpt55-high` and `gpt55-xhigh` remain explicit
all-agent GPT-5.5 overrides. `gpt56-role` keeps Cursor and Claude Code on their
native performance-first model tiers; legacy profiles retain their existing
adapter behavior.
`./install.sh --profile <profile> <target>` renders installed agents for Codex,
Cursor, and Claude Code.

`gpt56-role` uses `max` for Deep single-task scrutiny. Treat `ultra` as a
separate orchestration experiment, not as a silent substitute for `max`; adopt
it only with explicit nesting, cost, ownership, and acceptance evidence.

Exact model identifiers belong in installed agent definitions, runtime schemas,
or platform docs, not in ordinary plans. When a schema does not support a field,
omit it and express the role, evidence bar, and packet contract in the prompt.

Use `cheap-fast` only under explicit latency/quota pressure for trivial read-only evidence. Never for Judge, Reviewer, architecture Designer, public behavior, failed-goal adequacy, or performance-first projects.

## Economics

- Start with the smallest useful Explorer/Reviewer set. Before dispatching more
  than 3 parallel agents of any role, state the ownership map, integration
  order, verification target, and why parallel beats serial.
- Workers have no fixed prompt-level cap; runtime limits, disjoint ownership,
  integration cost, and the accepted plan bound the wave.
- Use batch dispatch or worktree isolation when ownership or merge cost is unclear.

## Codex Control Plane

- Native Codex goal state is the source of truth for autonomous lifecycle.
- Use `Goal Proposal` only when objective, scope, verification, or stop rules need human review before `create_goal`.
- Use `update_plan` for visible progress only; durable state lives in Teamwork artifacts.
- Confirm authorization via project rules or `AGENTS.md`; use `tool_search` for `multi-agent spawn_agent` when available.
