# Simplify Codex Dispatch Routing

## Goal

Simplify Teamwork plan routing so ordinary plans describe conceptual roles,
scope, model tier, context strategy, ordering, and why each agent is needed.
Codex-native dispatch fields remain documented in the router and are derived
at dispatch time unless a native override is itself part of the decision.

## Evidence Summary

- Observed current dirty diff: `skills/teamwork-design/SKILL.md`,
  `skills/teamwork-review/SKILL.md`, and `scripts/validate.sh` currently
  require ordinary plans to spell out `agent_type`, `fork_context`,
  `reasoning_effort`, and model handling.
- Observed `skills/teamwork/SKILL.md`: the router already contains the detailed
  Codex Dispatch Mapping for Teamwork tiers, Codex agent types, and fork
  inheritance.
- User-provided evidence: Codex skills guidance favors progressive disclosure,
  and Codex native agent settings are runtime dispatch concerns rather than
  fields that every plan template should expose.
- Inferred direction: keep native mapping and hard gates in one durable source,
  while reducing ordinary plan-writing burden.

## Requirements Mapping

- Router remains the detailed native mapping source: verify
  `skills/teamwork/SKILL.md` still contains `Codex Dispatch Mapping`, role to
  agent-type mapping, tier to reasoning-effort mapping, and fork inheritance.
- Design plans become shorter: verify `skills/teamwork-design/SKILL.md`
  requires role, scope, tier, context strategy, order, and why, and no longer
  has the long native-field routing template.
- Execute and review retain hard gates: verify illegal native dispatch such as
  nonexistent agent types, full-history fork plus overrides, or inherited low
  effort claiming high reasoning remains rejected.
- User docs stay concise: verify `README.md` and `CODEX.md` point to the router
  instead of copying the full mapping table.
- Validation prevents regression: verify `scripts/validate.sh` checks the
  router mapping, hard gates, concise docs, and absence of the long design
  template or normal `xhigh` design option.

## Scope

- In scope: `skills/*/SKILL.md` workflow instructions, `scripts/validate.sh`,
  `CODEX.md`, `README.md`, and this durable plan artifact.
- Out of scope: runtime Python, installers, hooks, manifests, and user Codex
  configuration.
- Sacred boundaries: keep Teamwork model-ID agnostic, keep role separation
  between design, execute, and review, and preserve illegal routing hard gates.

## Implementation Steps

- [x] 1. Add this durable plan artifact as the execution and review source of
  truth.
- [x] 2. Keep detailed Codex dispatch mapping centralized in
  `skills/teamwork/SKILL.md`.
- [x] 3. Simplify `skills/teamwork-design/SKILL.md` routing requirements and
  template to conceptual routing fields.
- [x] 4. Update `skills/teamwork-review/SKILL.md` so plan review checks
  conceptual routing sufficiency, while native-field checks apply to explicit
  native fields or actual dispatch evidence.
- [x] 5. Update `skills/teamwork-execute/SKILL.md` so Worker handoffs require
  file ownership, tier, context strategy, and verification; native Codex fields
  are checked immediately before delegated dispatch.
- [x] 6. Shorten `CODEX.md` and `README.md` Codex dispatch prose to point to
  the router mapping.
- [x] 7. Adjust `scripts/validate.sh` to remove mandatory design-template
  native-field greps and add regression checks against reintroducing the long
  native-field template or normal `xhigh` design option.

## Verification

- Focused: `./scripts/validate.sh` must print
  `OK: Teamwork skill package validates`.
- Whitespace: `git diff --check` must report no whitespace errors.
- Text check:
  `rg -n "Codex Dispatch Mapping|fork_context:true|reasoning_effort|agent_type" skills CODEX.md README.md scripts/validate.sh`.
- Stress scenarios:
  - Ordinary documentation plan: short Subagent Routing without native fields
    should satisfy plan review.
  - Full-history review: plan can use `context strategy: full-history
    inheritance`; dispatch/review must know native overrides are invalid.
  - Illegal native routing: explicit `agent_type:"judge"` or
    `fork_context:true` with `reasoning_effort:"high"` must still be rejected.

## Expected Results

- Detailed native mapping is concentrated in the router and safety gates.
- `teamwork-design` no longer forces every routing entry to include
  `agent_type`, `fork_context`, `reasoning_effort`, or `model`.
- Validation passes while guarding against both illegal native examples and
  reintroduction of the long design template.

## Risks

- Over-simplification could hide dispatch constraints. Mitigation: keep the
  router mapping and execute/review hard gates.
- Grep validation could become brittle. Mitigation: check section names,
  policy phrases, and targeted negative patterns rather than whole paragraphs.

## Stop Rules

- Stop if validation requires runtime, installer, hook, manifest, or user
  configuration changes.
- Stop if a safety hard gate must be removed to make validation pass.

## Worker Handoff

Implement only the files listed in scope. Preserve existing style and do not
touch runtime code, installers, hooks, manifests, or user config.

## Review Handoff

Check the diff, validation output, whitespace check, focused text checks, and
stress scenarios. Confirm ordinary routing is simpler and illegal native
dispatch remains blocked.

## Subagent Routing

- Judge: needed | scope: plan review | tier: high reasoning | context:
  targeted handoff | order: before implementation | why: non-lightweight
  workflow instruction change.
- Worker: main agent | scope: listed Markdown and validation files | tier:
  standard | context: accepted plan plus local files | order: serial | why:
  edits are coupled but bounded.
- Reviewer: needed | scope: diff, validation, regressions, stress scenarios |
  tier: high reasoning | context: targeted handoff | order: after verification
  | why: fresh execution review.
