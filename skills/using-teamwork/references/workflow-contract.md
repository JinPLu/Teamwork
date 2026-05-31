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
- Use role-specific Dispatch Economics. Explorer/Reviewer tracks are capped by
  context cost; Worker tracks are capped by ownership clarity, integration
  cost, and verification shape.
- Treat subagent dispatch as the default substrate for non-lightweight
  Teamwork work when the active platform or loaded instructions authorize
  subagents. Codex standing authorization must come from the user's prompt or a
  loaded project/global instruction. Teamwork activation decides dispatch economics
  after that authorization exists. The main agent remains the
  orchestrator and keeps raw evidence, implementation detail, and fresh review
  outside the main context whenever an independent track exists.
- Missing currently active subagent tools is not enough to stay local. On
  Codex, if `tool_search` is available, discover `spawn_agent` before recording
  an unavailable-tool exception. On Cursor or Claude Code, use the `Task` tool
  when present.

## Workflow Pattern Selection

Choose the smallest workflow pattern that preserves correctness:

- Treat work as non-lightweight when it is multi-file, unfamiliar, ambiguous,
  repeated-failure, public/shared behavior, protected-boundary, cross-turn,
  delegated, or completion acceptance work.
- Fixed sequence with clear steps: use a lightweight plan.
- Distinct categories of work: route by stage instead of forcing one loop.
- Independent evidence questions: default to parallel Explorer tracks.
- Ambiguous design or high-risk plan quality: use Designer or Judge prompts
  before execution.
- Unpredictable or multi-file implementation: use an orchestrator/Worker
  pattern with disjoint ownership or worktree isolation.
- Clear acceptance plus retry need: use a review or goal loop with explicit
  verification and stop rules.

## Platform Native Policy Map

Native platform capabilities remain the execution substrate. Teamwork adds route
policy, evidence requirements, durable artifacts, and acceptance gates; it does
not replace native state or tool semantics.

### Codex

Use native tools for editing, shell, MCP/app access, sandbox approvals,
`update_plan`, goals, `spawn_agent`, automations, review commands, and
verification.

### Cursor

Use native tools for editing, shell, MCP/app access, permissions, `Task`
subagents, browser automation, and verification. Goal-mode convergence stays in
chat unless the user explicitly uses another native goal surface.

### Claude Code

Use native tools for editing, shell, MCP/app access, permissions, `Task`
subagents (user-defined under `~/.claude/agents/`, fallback `general-purpose`),
TodoWrite progress, and verification. Goal-mode has no native goal surface; use
a chat-only `Goal Proposal` plus a rolling report under `docs/teamwork/reports/`
as durable goal state.

## Progress Anchors And Artifacts

Visible progress tools (Codex `update_plan`, Cursor TodoWrite, Claude Code
TodoWrite, chat checklist) are transient UI-only state. They are not durable
execution specs, review targets, or completion evidence.

Use artifacts only when they will reduce repeated work or anchor cross-turn,
cross-agent, high-risk, ambiguous, public/shared, explicitly planned, or
goal-mode work:

- `docs/teamwork/research/`: reusable investigation findings.
- `docs/teamwork/plans/`: execution memo and active plan anchor.
- `docs/teamwork/reports/`: reusable task conclusions and goal rolling memory.

Do not create artifacts for ordinary native-flow work or to record every
thought. Search existing research artifacts before starting new non-trivial
research and record reuse/update/new disposition in goal-mode reports.

## Subagent Collaboration Model

Subagents provide independent context, parallel evidence, isolated execution, or
fresh review. The main agent is the orchestrator: it owns scope, synthesis,
conflict resolution, integration, final verification, and final acceptance.

Same-context self-review is not acceptance for non-lightweight work. A fresh
Reviewer subagent is required before claiming non-lightweight execution is
complete, reviewed, or accepted. If subagents are unavailable, authorization is
missing, or dispatch is explicitly forbidden, report the work as
verified-but-unreviewed and name the residual risk instead of presenting it as
accepted.

Subagent authorization has two layers: platform permission to spawn, and
Stage-Routed Proactive Dispatch deciding when spawning is worthwhile. Once a
Teamwork stage is active and subagents are authorized, that stage may dispatch
non-destructive Explorer, Designer, Judge, Worker, or Reviewer tracks that fit
the stage contract. A plan's `Dispatch Guidance:` or durable `Subagent Routing`
is routing guidance, not the only authorization source. The execution stage
must re-evaluate the split from the accepted plan, source ownership, and
current workspace evidence before editing. For non-lightweight Teamwork work
with independent tracks, dispatch is the expected path; serial local work needs
one of the allowed exception reasons.

Ask again only when dispatch needs credentials, destructive actions, unclear
write ownership, protected-boundary changes, unavailable tools, missing Codex
standing authorization, or another approval-gated capability. Otherwise,
dispatch proactively when an independent track can improve cost, elapsed time,
context isolation, or quality.

For non-lightweight work, split before implementation steps and record either
the chosen subagent tracks or the continuity rationale. If you keep work local,
state the reason: tight coupling, overlapping ownership, small scope,
unavailable tool, urgent critical-path dependency, or higher context cost than
benefit.
