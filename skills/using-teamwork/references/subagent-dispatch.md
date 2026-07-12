# Subagent Dispatch

Dispatch, role mapping, and platform fields. Prompt/result shape ->
`subagent-contract.md`; swarm orchestration -> `workflow-orchestration.md`.

## When To Dispatch

Stay native for small, clear work. Dispatch only when a bounded independent
track's evidence, latency, or isolation value exceeds coordination cost:

- **Explore/Research**: Explorer for orientation, artifact lookup, external
  calibration, stale assumptions, or evidence beyond a quick read.
- **Design**: Designer for ambiguous decisions; Judge for durable, risky, or delegated plans.
- **Execute**: Worker per independent owned slice with disjoint files, components, artifacts, or verification targets.
- **Review**: Reviewer when independent acceptance reduces material risk; fresh
  context only for the high-risk cases in `workflow-contract.md`.

Skip dispatch for quick facts, obvious edits, tightly coupled work, unavailable
tools, missing authority, user opt-out, or excessive context cost.

Use CodeGraph before Explorer fanout for structural code questions.

## Roles

- **Explorer**: gathers evidence; read-only.
- **Designer**: decides architecture and plan shape; read-only.
- **Judge**: reviews plan adequacy before execution; read-only.
- **Worker**: implements owned slices; workspace-write.
- **Reviewer**: checks completed work; read-only.

## Lifecycle

A subagent returns one self-contained packet, then stops. It does not monitor,
expand scope, chain agents, or resume after return. Give materially new work to
a fresh agent and packet.

The main agent records review-relevant outcomes and owns integration,
verification, and acceptance.

## Platform Fields

Inspect the live schema. A ready Teamwork Codex install exposes a non-reserved `teamwork`
namespace with `agent_type`; select the installed role and use
`fork_turns:"none"` with a self-contained fresh packet. The config checker proves
local state only. Nine threads permit eight subagents; dispatch remains
value-gated. If generic fields remain, label the child `parent-inherited`; put
role, evidence bar, and stop rule in `message`.

**Codex custom-agent runtimes** - use the exact installed role when `agent_type`
is callable. A full-history fork intentionally bypasses fresh role overrides.

| Role | agent_type | Fallback |
|---|---|---|
| Explorer | `teamwork_explorer` | `explorer` |
| Worker | `teamwork_worker` | `worker` |
| Designer | `teamwork_designer` | `default` + role in prompt |
| Judge | `teamwork_judge` | `default` + role in prompt |
| Reviewer | `teamwork_reviewer` | `default` + role in prompt |
| Deep Judge | `teamwork_deep_judge` | `default` + role in prompt |
| Deep Reviewer | `teamwork_deep_reviewer` | `default` + role in prompt |

Effort: `fast`->low, `standard`->medium, `high reasoning`->high, `deep reasoning`->max.

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

`performance-first` defaults to this Codex mapping: Explorer=`gpt-5.6-terra` medium;
Worker=`gpt-5.6-sol` medium; Designer/Judge/Reviewer=`gpt-5.6-sol` high; Deep
Judge/Reviewer=`gpt-5.6-sol` max. `gpt56-role` aliases it.
`cost-first` uses Luna/Terra/Sol on Codex. `gpt56-high` and `gpt56-xhigh` pin
all Codex roles to Sol; legacy `gpt55-*` names alias GPT-5.6. Cursor uses
Composer 2.5/Sonnet 4.6/Opus 4.8; Claude uses current `haiku`/`sonnet`/`opus` aliases.
`./install.sh --profile <profile> <target>` renders installed agents for Codex,
Cursor, and Claude Code.

`performance-first` and `gpt56-role` use `max` for Deep scrutiny. Treat `ultra`
as a separate experiment requiring explicit cost, ownership, and acceptance
evidence.

Exact model identifiers belong in installed agent definitions, runtime schemas,
or platform docs, not in ordinary plans. When a schema does not support a field,
omit it and express the role, evidence bar, and packet contract in the prompt.
Diagnostics record the profile active at session time and the actual child model
separately; never infer a historical profile from the current install marker.

Use `cheap-fast` only under explicit latency/quota pressure for trivial
read-only evidence; never for risk review, architecture, public behavior,
failed-goal adequacy, or performance-first projects.

## Economics

- The first wave defaults to at most two agents with disjoint ownership.
  Integrate and assess their packets before opening another wave.
- Workers have no fixed prompt-level cap; runtime limits, disjoint ownership,
  integration cost, and the accepted plan bound the wave.
## Codex Control Plane

- Native Codex goal state is the source of truth for autonomous lifecycle.
- Use `Goal Proposal` only when objective, scope, verification, or stop rules need human review before `create_goal`.
- Use `update_plan` for visible progress only; durable state lives in Teamwork artifacts.
- Confirm authorization via project rules or `AGENTS.md`; use `tool_search` for `multi-agent spawn_agent` when available.
