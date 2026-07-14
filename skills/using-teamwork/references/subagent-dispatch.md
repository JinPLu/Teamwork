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

For structural code questions, prefer CodeGraph before Explorer fanout only
when it is available and its index is healthy for the relevant files.

## Roles

- **Explorer**: gathers evidence; read-only.
- **Designer**: decides architecture and plan shape; read-only.
- **Judge**: reviews plan adequacy before execution; read-only.
- **Worker**: implements owned slices; workspace-write.
- **Reviewer**: checks completed work; read-only.

## Lifecycle

A subagent returns one self-contained internal result, then stops. It does not monitor,
expand scope, chain agents, or resume after return. The sole exception is one
parent-directed corrective recheck in the same initial Judge/Reviewer thread;
that thread may inspect only its prior finding IDs, claimed fixes, and
fix-introduced regressions or new direct evidence. It cannot dispatch, monitor,
or request another recheck. Give materially new work to a fresh agent with a
fresh internal brief.

The main agent records review-relevant outcomes and owns integration,
verification, and acceptance.

## Platform Fields

Inspect the live schema. A ready Codex install exposes a non-reserved `teamwork`
namespace with `agent_type`; select the installed role with `fork_turns:"none"`
and a self-contained internal brief.
The config checker proves local state only. If fields remain generic, label the
child `parent-inherited` and put its role and stop rule in `message`.

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

**Cursor** - prefer `~/.cursor/agents/` names; otherwise use supported
`subagent_type` and model fields. It has no `reasoning_effort` or `fork_context`.

| Role | Custom agent | Fallback subagent_type |
|---|---|---|
| Explorer | `explore` | `explore` |
| Worker | `worker` | `generalPurpose` or `shell` |
| Designer | `designer` | `generalPurpose` + role in prompt |
| Judge | `judge` | `generalPurpose` + role in prompt |
| Reviewer | `code-reviewer` | `code-reviewer` |
| Deep Judge | `deep-judge` | `generalPurpose` + role in prompt |
| Deep Reviewer | `deep-reviewer` | `code-reviewer` + role in prompt |

Use `readonly:true` for read-only roles, `run_in_background:true` for long
tracks, and `resume:"self"` only for a full-history fork.

**Claude Code** - prefer `~/.claude/agents/` names; otherwise use `Task` with
`general-purpose`. Model, effort, tools, and isolation live on the agent definition.

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

Exact model identifiers belong in installed definitions, schemas, or platform
docs. Omit unsupported fields. Diagnostics record session profile and child
model separately; never infer history from the current install marker.

Use `cheap-fast` only under explicit latency/quota pressure for trivial
read-only evidence; never for risk review, architecture, public behavior,
failed-goal adequacy, or performance-first projects.

## Economics

Choose wave size from independent ownership, evidence value, runtime limits,
and integration cost. Integrate returned work before opening dependent tracks;
do not impose a universal first-wave or Worker count.
## Codex Control Plane

- Native Codex goal state is the source of truth for autonomous lifecycle.
- Use `Goal Proposal` only when objective, scope, verification, or stop rules need human review before `create_goal`.
- Use `update_plan` for visible progress only; durable state lives in Teamwork artifacts.
- Confirm authorization via project rules or `AGENTS.md`; use `tool_search` for `multi-agent spawn_agent` when available.
