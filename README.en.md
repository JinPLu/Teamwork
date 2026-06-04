# Teamwork

[中文](README.md)

**Turn Codex subagents into a role-based engineering team with memory, evidence discipline, and acceptance loops.**

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**.
It does not replace Codex, Cursor, or Claude Code editing, shell, MCP, browser,
permission, or verification tools. Those native capabilities are the execution substrate.
Teamwork adds four things:

1. Custom role-based subagent dispatch, so complex work is cheaper, faster, and higher quality.
2. Evidence-first rules that tell the model not to be overconfident: prove first, conclude second.
3. Durable discussion / research, plan, and report memory, so long-running goals do not forget and goal execution stays grounded.
4. Verification, fresh review, and failure recovery loops, so "done" means reviewable evidence rather than model narration.

![Teamwork workflow banner](assets/teamwork-hero.png)

## Core Value

### 1. Role-Based Subagents: Cheaper, Faster, Better

Plain multi-agent work can become several loose chat windows. Teamwork turns
subagents into bounded engineering roles:

- `Explorer` gathers evidence and external constraints without dumping raw context back into the main thread.
- `Designer` compares options and states boundaries, success criteria, and rejected paths.
- `Judge` reviews plans before execution and finds evidence gaps, acceptance gaps, and risky assumptions.
- `Worker` owns one implementation slice and returns changes plus verification evidence.
- `Reviewer` fresh-reviews diffs, tests, artifacts, and PR/CI evidence.

The payoff is practical:

| Benefit | Why |
|---|---|
| Cheaper | Not every task needs the same long context or strongest model; dispatch follows role, risk, and task type. |
| Faster | Independent research, implementation, and review can run in parallel while the main agent orchestrates. |
| Better quality | Every subagent returns a packet; important claims need evidence; non-lightweight results need fresh review. |

### 2. Evidence First: Less Model Overconfidence

The dangerous failure mode is not only that a model does not know something.
It is that the model does not know, but still sounds certain. Teamwork treats
names, README prose, issues, summaries, `latest`, and `v2` labels as claims
until the agent finds direct evidence.

- Important conclusions are labeled `observed` / `inferred` / `claimed`.
- Key decisions map to source, config, logs, tests, diffs, artifacts, or primary sources.
- When root cause, API behavior, env / paths / hyperparameters, or external constraints are unclear, research or fail fast comes before edits.
- Planning and review check evidence adequacy, assumption safety, and acceptance gaps.

This is not ceremony. It keeps model confidence inside the boundary of what the
evidence can support.

### 3. Task Memory: Long Goals Stop Forgetting

Complex coding-agent work rarely finishes in one pass. It starts with
discussion, moves into research and planning, then execution, verification, and
often failure recovery. If all of that only lives in chat context, it disappears.

Teamwork preserves the important state in artifacts:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

- `research` records discussion / research conclusions, evidence, options, and remaining uncertainty.
- `plans` record executable scope, boundaries, acceptance criteria, dispatch guidance, and stop rules.
- `reports` record important task conclusions or, in goal mode, each attempt, verification result, failure reason, and next decision.

That makes `Goal Text` more than a target sentence: it can stay connected to
evidence, budget, stop rules, and prior attempts. After failure, Teamwork
returns to research + plan adequacy instead of repeating the same guess.

### 4. Acceptance Loops: Done Should Be Reviewable

Teamwork connects planning, execution, verification, and review. Plans state
scope, verification, and stop rules. Execution summaries state what changed,
what evidence supports it, and what remains uncovered. Reviews return severity,
evidence, and required action.

For multi-item state, Teamwork encourages short tables:

| Moment | Table Shows |
|---|---|
| Plan | Step / Scope / Owner / Verification / Stop rule |
| Execution result | Requirement / Change / Evidence / Status |
| Review | Severity / Finding / Evidence / Required action |
| Goal iteration | Attempt / Hypothesis / Verification / Result / Next step |

The point is not presentation polish. It lets humans scan scope, evidence,
risk, and next steps quickly.

## How Agent Behavior Changes

| Without Teamwork | With Teamwork |
|---|---|
| The main agent explores while editing | `using-teamwork` routes work into research, plan, execute, review, goal, or update |
| Subagents have no stable boundary | Role subagents have fixed responsibilities, inputs, output packets, and closure conditions |
| The model treats summaries as facts | Important conclusions are labeled `observed` / `inferred` / `claimed` and mapped to direct evidence |
| Done means "the agent says so" | Non-lightweight results default to fresh review; same-context self-review is not acceptance |
| Results hide in long prose | Plans, execution results, reviews, and goal iterations use short tables for human review |
| Failed attempts vanish after a few turns | Reports record attempts, verification, failure class, and next decision |
| Long tasks depend on user reminders | Artifacts and goal loops preserve context, budget, stop rules, and acceptance evidence |

## When To Use It

Good fit:

- Non-lightweight coding-agent work where subagents should share research, design, implementation, or review.
- Work that needs clearer tradeoffs between cost, speed, and quality.
- Work where overconfident model claims need to be grounded in checkable evidence.
- Cross-turn discussion, research, plans, reports, failed attempts, or acceptance evidence that should be reused.
- Work where plans, execution results, and reviews need to be easy for humans to audit.
- Goal-directed work that should iterate until a verifiable target is reached.

Not a fit: one-line facts, tiny obvious edits, sensitive or destructive
operations, tightly coupled critical paths, or work where subagent context cost
exceeds the benefit.

## Quick Install

Codex-first default install:

```bash
./install.sh              # same as ./install.sh codex
./install.sh codex --profile cost-first
```

Install for other platforms:

```bash
./install.sh cursor
./install.sh claude          # Claude Code skills only
./install.sh claude-agents   # Claude Code agents only
./install.sh all             # all supported skills + Codex/Claude agents
```

Local development or project installs:

```bash
./install.sh project         # writes gitignored .cursor/.codex/.claude
./install.sh --link codex
./install.sh --link all
./install.sh --link project
```

Codex installs use `performance-first` by default: routine Explorer /
Designer / Worker roles use role-optimized models, while high-risk Judge /
Reviewer profiles stay on stronger model tiers. `cost-first` downshifts only
routine roles, not high-risk review.

## Included Skills

- `using-teamwork`: automatic entrypoint and stage router.
- `teamwork-research`: evidence gathering, root-cause investigation, option comparison, external calibration.
- `teamwork-plan`: turns evidence into executable scope, boundaries, acceptance, and dispatch guidance.
- `teamwork-execute`: implements accepted plans and records changes, verification, and deviations.
- `teamwork-review`: fresh-context plan or execution review with `accept` / `revise` / `blocked`.
- `teamwork-goal`: convergence loop for verifiable targets.
- `teamwork-init`: project agent instructions, AGENTS/CODEX/CURSOR/CLAUDE slimming, and setup.
- `teamwork-update`: version, manifest, release surface, and package-update hygiene.

## Platform Positioning

Codex is the reference runtime: native goals are the autonomous control plane,
and `teamwork_*` custom agents are the primary collaboration network for
non-lightweight work. `./install.sh codex` writes the default global
`~/.codex/AGENTS.md` standing authorization, so users usually do not need to
repeat "use subagents" in every prompt.

Cursor and Claude Code are adapters: they reuse the same Teamwork protocol
while keeping their own native capabilities. Cursor uses Task subagents;
Claude Code skills and agents install through the matching installer targets,
with rolling reports carrying goal mode.

## Version And Validation

`VERSION` is the package version source of truth and must match
`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`. Version,
manifest, and release-surface updates use `teamwork-update`.

Validate the repository:

```bash
./scripts/validate.sh
```

## Read More

- [CODEX.md](CODEX.md): Codex runtime profile, Goal Text, and custom-agent mapping.
- [CURSOR.md](CURSOR.md): Cursor adapter.
- [CLAUDE.md](CLAUDE.md): Claude Code adapter.
- `skills/*/SKILL.md`: stage skill behavior.
- `skills/using-teamwork/references/`: dispatch, packet, artifact, review, and goal details.
