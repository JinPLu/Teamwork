# Subagent Dispatch

Dispatch decisions, role-to-model mapping, and platform field reference.
Prompt and packets → `subagent-contract.md`. Swarm orchestration → `workflow-orchestration.md`.

## When To Dispatch

Dispatch when tracks are independent, isolatable, or parallel:

- **Explore**: Explorer for codebase orientation, artifact lookup, or evidence beyond a quick literal read.
- **Research**: Explorer tracks for external calibration, stale assumptions, option comparison, or broad source census.
- **Design**: Designer for ambiguous decisions; Judge for durable, risky, or delegated plans.
- **Execute**: Worker per independent owned slice with disjoint files or components.
- **Review**: fresh Reviewer for non-trivial execution, high-risk diffs, delegated work, public contracts, release, security, or goal mode.

Skip dispatch for quick facts, tiny obvious edits, tightly coupled critical-path work, unavailable tools, missing authorization, explicit user opt-out, or when subagent context cost exceeds value. When skipping affects review or acceptance, record the reason.

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

Main agent owns closure. Dispatch states: `dispatched -> returned -> closed`, `blocked`, or `abandoned-after-discovery`. Record Closure Evidence after integrating each packet. Before final response, no delegated track may remain open.

## Platform Fields

Codex uses `agent_type`; Cursor uses `subagent_type`; Claude Code uses `Task`.

**Codex** — role dispatch: `agent_type`, `model`, `reasoning_effort`, `fork_context:false`. Full-history fork: `fork_context:true` only (no other fields).

| Role | agent_type | Fallback |
|---|---|---|
| Explorer | `teamwork_explorer` | `explorer` |
| Worker | `teamwork_worker` | `worker` |
| Designer | `teamwork_designer` | `default` + role in prompt |
| Judge | `teamwork_judge` | `default` + role in prompt |
| Reviewer | `teamwork_reviewer` | `default` + role in prompt |
| Deep Judge | `teamwork_deep_judge` | `default` + role in prompt |
| Deep Reviewer | `teamwork_deep_reviewer` | `default` + role in prompt |

Reasoning effort: `fast`→low, `standard`→medium, `high reasoning`→high, `deep reasoning`→xhigh.

**Cursor** — prefer custom agents from `~/.cursor/agents/` by `name`; fallback `subagent_type`, `model`; no `reasoning_effort` or `fork_context`.

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

**Claude Code** — prefer custom agents from `~/.claude/agents/` by `name`; fallback `Task` with `general-purpose` and role in prompt. Model, `effort`, tool allowlist, and `isolation: worktree` live on the agent definition, not per Task call.

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

| Class | Codex performance-first | Codex cost-first | Cursor perf-first | Cursor cost-first | Claude perf-first | Claude cost-first |
|---|---|---|---|---|---|---|
| `cheap-fast` | opt-in only | gpt-5.4-mini | composer-2.5-fast | composer-2.5-fast | haiku med | haiku med |
| `balanced` | gpt-5.5 med | gpt-5.4 med | claude-sonnet-4-6 | composer-2.5-fast | sonnet med | haiku med |
| `coding` | gpt-5.5 med | gpt-5.4 med | composer-2.5-fast | composer-2.5-fast | sonnet med | haiku med |
| `frontier` | gpt-5.5 high | gpt-5.5 high | claude-opus-4-8-thinking-high | claude-opus-4-8-thinking-high | opus high | opus high |
| `deep reasoning` | gpt-5.5 xhigh | gpt-5.5 xhigh | claude-opus-4-8-thinking-high | claude-opus-4-8-thinking-high | opus xhigh | opus xhigh |
| `inherited` | omit model | omit model | inherit | inherit | inherit | inherit |

Role defaults: Explorer→`balanced` (use `frontier` for broad/ambiguous/high-risk); Designer→`balanced` (use `frontier` for architecture or public contracts); Judge→`frontier` high reasoning; Worker→`coding` or `inherited`; Reviewer→`frontier` high reasoning.

`performance-first` is the default on all platforms. `./install.sh --profile` renders installed agents for Codex, Cursor, and Claude Code.

Use `cheap-fast` only under explicit latency/quota pressure for trivial read-only evidence. Never for Judge, Reviewer, architecture Designer, public behavior, failed-goal adequacy, or performance-first projects.

## Economics

- **Explorer/Reviewer default max 3** parallel; cap raw evidence in packets; use artifact pointers for overflow.
- Workers: no fixed cap; dispatch per independent track. Before dispatching **more than 3 Workers**, state ownership map, integration order, verification target, and why parallel beats serial.
- Use batch dispatch or worktree isolation when ownership or merge cost is unclear.

## Codex Control Plane

- Native Codex goal state is the source of truth for autonomous lifecycle.
- Use `Goal Proposal` only when objective, scope, verification, or stop rules need human review before `create_goal`.
- Use `update_plan` for visible progress only; durable state lives in Teamwork artifacts.
- Confirm authorization via project rules or `AGENTS.md`; use `tool_search` for `multi-agent spawn_agent` when available.
