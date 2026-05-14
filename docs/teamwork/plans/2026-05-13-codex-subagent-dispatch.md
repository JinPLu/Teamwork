# Codex Subagent Dispatch Routing Fix

## Goal

Strengthen Teamwork's skill-only routing rules so they reflect actual Codex
subagent dispatch behavior, especially the difference between full-history
inheritance and explicit non-fork routing.

## Evidence Summary

- Observed current Codex session tool schema: `spawn_agent` supports
  `agent_type`, `model`, and `reasoning_effort` for explicit subagent dispatch.
- Observed current Codex session tool schema and user-provided task evidence:
  full-history `fork_context:true` agents inherit the parent agent type, model,
  and reasoning effort and reject override fields.
- Observed current Codex session tool schema: available model overrides list
  `xhigh` as a supported reasoning effort, so Teamwork may reserve it for
  explicitly high-risk final gates while keeping normal `high reasoning` mapped
  to `reasoning_effort:"high"`.
- Observed current session dispatch: a non-fork Judge review using
  `agent_type:"default"`, `fork_context:false`, and `reasoning_effort:"high"`
  was accepted by Codex and returned a review result.
- Therefore Teamwork instructions must distinguish inheritance-only full-history
  forks from non-fork dispatch where role and effort overrides are valid.

Current Codex schema evidence captured for review:

```text
spawn_agent fields include: agent_type, fork_context, model, reasoning_effort
Available agent_type values include: default, explorer, worker
Available reasoning_effort values include: low, medium, high, xhigh
fork_context:true: use when the new agent should have exactly the same context
as the parent; user-provided task evidence says full-history forked agents
inherit parent type/model/effort and reject override fields.
```

## Requirements Mapping

- Codex dispatch tiers map to schema-supported `reasoning_effort` values:
  verify platform support from the current Codex session tool schema and verify
  the repository encodes the mapping by inspecting `skills/teamwork/SKILL.md`,
  `CODEX.md`, and `README.md`.
- Conceptual Teamwork roles map to real Codex `agent_type` values: verify by
  inspecting `skills/teamwork/SKILL.md` and routing examples in
  `skills/teamwork-design/SKILL.md`.
- Full-history fork rules reject override fields: verify by inspecting
  `skills/teamwork/SKILL.md`, `skills/teamwork-execute/SKILL.md`, and
  `skills/teamwork-review/SKILL.md`.
- Subagent Routing entries include conceptual role, Codex `agent_type`,
  `fork_context`, `reasoning_effort`, model handling, and context handoff:
  verify by inspecting `skills/teamwork-design/SKILL.md`.
- Validation catches regressions in the Codex dispatch guidance: verify with
  `./scripts/validate.sh`.

## Scope

- In scope: Markdown workflow instructions, concise `CODEX.md` and `README.md`
  guidance, and focused validation checks in `scripts/validate.sh`.
- Out of scope: `bin/raoctl.py`, install behavior, manifests, hooks, or user
  Codex configuration.
- Sacred boundaries: keep Teamwork model-ID agnostic; do not hard-code `gpt-*`
  model choices; treat `fast` as a Teamwork capability tier rather than Codex
  `service_tier:"fast"`.

## Implementation Steps

- [x] Update `skills/teamwork/SKILL.md` with a Codex Dispatch Mapping section:
  `fast -> reasoning_effort:"low"`, `standard -> "medium"`,
  `high reasoning -> "high"`, and `xhigh` only for explicitly high-risk final
  gates.
- [x] Map Teamwork roles to Codex agent types: `Explorer -> explorer`,
  `Worker -> worker`, and `Designer`, `Judge`, and `Reviewer -> default` with
  the conceptual role stated in the prompt.
- [x] Document context rules: use `fork_context:true` only when full history is
  required and omit `agent_type`, `model`, and `reasoning_effort`; use
  `fork_context:false` or omit it when role or effort overrides are required,
  passing needed context in the prompt or `items`.
- [x] Update `skills/teamwork-design/SKILL.md` so every Subagent Routing entry
  includes conceptual role, Codex `agent_type`, `fork_context`,
  `reasoning_effort`, `model: omitted unless explicitly required`, and context
  handoff strategy.
- [x] Update `skills/teamwork-execute/SKILL.md` and
  `skills/teamwork-review/SKILL.md` to reject illegal or misleading routing,
  especially full-history fork plus override fields, nonexistent agent types
  such as `judge`, and claimed high-reasoning routing that inherits a lower
  parent effort.
- [x] Sync concise guidance in `CODEX.md` and `README.md`.
- [x] Extend `scripts/validate.sh` with grep checks for
  `Codex Dispatch Mapping`, `fork_context:true` inheritance,
  `fork_context:false` explicit routing, `reasoning_effort`, `agent_type`, and
  the role-to-agent-type mapping.
- [x] Add practical negative validation checks that reject documented
  `agent_type:"judge"` or `agent_type:"reviewer"` examples and reject any
  endorsement of full-history fork plus override fields.

## Verification

- Focused: run `./scripts/validate.sh`.
- Whitespace: run `git diff --check`.
- Text checks:
  `rg -n "fork_context|reasoning_effort|agent_type|Full-history|Codex Dispatch Mapping" skills CODEX.md README.md scripts/validate.sh`.
- Schema evidence check: inspect this plan artifact's captured schema excerpt;
  expected result is that it lists `agent_type`, `fork_context`, `model`,
  `reasoning_effort`, `default`, `explorer`, `worker`, `low`, `medium`, `high`,
  and `xhigh`.
- Manual scenarios:
  - Full-history fork with overrides is documented as invalid.
  - Non-fork subagent with explicit effort is documented as valid.
  - Judge and Reviewer do not use nonexistent Codex agent types.
  - Skill-only install behavior remains unchanged.

## Expected Results

- `./scripts/validate.sh` prints `OK: Teamwork skill package validates`.
- `git diff --check` reports no whitespace errors.
- Focused text checks show the Codex dispatch rules in the skill docs, concise
  user docs, and validation script.
- Validation fails if the docs introduce `agent_type:"judge"` or
  `agent_type:"reviewer"` examples, or if they endorse full-history fork plus
  override routing.

## Risks

- Over-specifying Codex behavior could make the docs brittle. Mitigation: encode
  only stable dispatch fields and keep model IDs omitted unless explicitly
  required.
- Validation grep checks could be too narrow or too broad. Mitigation: check
  section names and exact policy phrases rather than entire paragraphs.

## Stop Rules

- Stop if local evidence contradicts the plan's Codex dispatch assumptions.
- Stop if implementing the plan requires runtime, installer, hook, manifest, or
  user configuration changes.
- Stop if validation failures point to unrelated broken state that cannot be
  distinguished from this edit.

## Worker Handoff

Execute only the documentation and validation changes above. Do not change
runtime Python, installer behavior, manifests, hooks, or user Codex config.

## Review Handoff

Check the diff, validation output, whitespace check, focused text checks, and
manual scenarios. Confirm no illegal full-history fork plus override routing is
endorsed and no nonexistent Codex `agent_type` such as `judge` is introduced.

## Subagent Routing

- Explorer: skipped | scope: evidence already supplied in accepted plan and
  corroborated by local files | Teamwork model tier: `fast` or `standard` if
  needed | Codex `agent_type`: `explorer` if needed | `fork_context`: omitted |
  `reasoning_effort`: `low` or `medium` if needed | `model`: omitted unless
  explicitly required | context handoff: targeted file paths and questions |
  ordering: skipped | why: current work is direct doc and validation editing.
- Designer: skipped | scope: direction already selected by accepted plan |
  Teamwork model tier: `high reasoning` if reopened | Codex `agent_type`:
  `default` | `fork_context`: omitted | `reasoning_effort`: `high` if reopened
  | `model`: omitted unless explicitly required | context handoff: plan
  artifact and constraints | ordering: skipped | why: implementation direction
  is already fixed.
- Judge: needed | scope: plan review before implementation | Teamwork model
  tier: `high reasoning` | Codex `agent_type`: `default` | `fork_context`:
  `false` or omitted | `reasoning_effort`: `high` | `model`: omitted unless
  explicitly required | context handoff: plan artifact path and relevant source
  paths | ordering: serial before implementation | why: non-lightweight
  workflow instruction change requires a distinct plan-review pass.
- Worker: main agent | scope: listed Markdown and validation files | Codex
  Teamwork model tier: `standard` | `agent_type`: `worker` if delegated |
  `fork_context`: omitted | `reasoning_effort`: `medium` | `model`: omitted
  unless explicitly required | context handoff: accepted plan and exact file
  ownership | ordering: serial | why: edits are coupled across docs and
  validation but small enough for the main agent worker stage.
- Reviewer: needed | scope: diff, validation, whitespace, text checks, manual
  scenarios | Teamwork model tier: `high reasoning` | Codex `agent_type`:
  `default` | `fork_context`: `false` or omitted | `reasoning_effort`: `high`
  or `xhigh` only if final gate is deemed explicitly high-risk | `model`:
  omitted unless explicitly required | context handoff: plan artifact, diff,
  and verification output | ordering: serial after verification | why:
  completion requires a distinct execution-review pass.
