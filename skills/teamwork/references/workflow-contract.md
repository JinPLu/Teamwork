# Workflow Contract

Use this reference whenever a Teamwork stage is active. Keep stage `SKILL.md`
files focused on stage-specific behavior; this file owns shared judgment rules.

## Assumptions And Boundaries

- State assumptions before they affect behavior, scope, verification, public
  contracts, data contracts, architecture, protected claims, or user constraints.
- Stop and ask, or route to research, when an assumption would change public
  behavior, protected contracts, architecture, or user intent.
- Prefer the smallest producer-side change that satisfies the goal.
- Avoid speculative abstraction, unrelated cleanup, formatting churn, broad
  refactors, or downstream cleanup unless direct evidence requires it.

## Evidence Interpretation Contract

Treat names, comments, README prose, issue text, summaries, labels such as
`latest` or `v2`, and historical notes as claims until corroborated.

Label important evidence:

- `observed`: directly inspected source, diff, config, log, command output,
  test result, artifact, or primary external source.
- `inferred`: conclusion drawn from observed evidence.
- `claimed`: narrative, naming, summary, or user statement that still needs a
  direct evidence cross-check.

Before important decisions, cross-check at least one direct evidence category:
source call path, test behavior, configuration, command output, artifact
properties, git diff, or primary external evidence.

## Context & Cost Discipline

- Use local files, diffs, logs, tests, artifacts, and prior Teamwork artifacts
  first to establish the actual project state.
- For non-trivial research, use external calibration from official docs,
  papers, release notes, upstream issues, or other primary sources when current
  platform, dependency, model, API, upstream, or field practice can affect the
  answer.
- Load references only when their condition applies. Do not paste large logs or
  raw subagent transcripts into the main context; ask for condensed evidence,
  confidence, dissent, and open questions.
- Default to at most 3 parallel research or review subagents unless the user
  gives a larger budget.

## Progress Anchors And Artifacts

`update_plan` and task widgets are transient UI-only checklist state. They are
not durable execution specs, review targets, or completion evidence.

Use artifacts only when they will reduce repeated work or anchor cross-turn,
cross-agent, high-risk, ambiguous, public/shared, explicitly planned, or
goal-mode work:

- `docs/teamwork/research/`: reusable investigation findings.
- `docs/teamwork/plans/`: execution memo and active plan anchor.
- `docs/teamwork/reports/`: reusable task conclusions and goal rolling memory.

Do not create artifacts for ordinary native-flow work or to record every
thought. Search existing research artifacts before starting new non-trivial
research and record reuse/update/new disposition when goal-mode checkpointing.

## Subagent Collaboration Model

Subagents provide independent context, parallel evidence, isolated execution, or
fresh review. The main agent owns scope, synthesis, conflict resolution,
verification, and final acceptance.

When Teamwork is active, the user has granted standing authorization for
automatic subagent delegation on independent non-lightweight tracks. Do not ask
for extra "fan out" confirmation unless dispatch needs credentials,
destructive actions, unclear write ownership, or another approval-gated
capability.

For non-lightweight work, split independent tracks first. Use subagents when 2
or more tracks can run without blocking the next local step; keep work local
when continuity, tight coupling, or overlapping ownership makes delegation
unsafe.
