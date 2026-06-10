# Teamwork

[中文](README.md)

**Turn Codex subagents into a role-based engineering team with memory, evidence discipline, and acceptance loops.**

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**.
It does not replace Codex, Cursor, or Claude Code editing, shell, MCP, browser,
permission, or verification tools. Those native capabilities are the execution substrate.
Teamwork adds four things:

1. Fan-out dispatch to custom role-based subagents, so complex work is cheaper, faster, and higher quality.
2. Evidence-first rules that tell the model not to be overconfident and not to silently fall back.
3. Durable discussion / research, plan, and report memory, so long-running goals do not forget and goal execution stays grounded.
4. Verification, fresh review, and failure recovery loops, so "done" means reviewable evidence rather than model narration.

![Teamwork workflow banner](assets/teamwork-hero.png)

## Core Value

### 1. Fan-Out Role Subagents: Cheaper, Faster, Better

Plain multi-agent work can become several loose chat windows. Teamwork keeps
fan-out bounded: the main agent splits only worthwhile independent tracks into engineering roles:

- `Explorer` gathers evidence and external constraints without dumping raw context back into the main thread.
- `Designer` compares options and states boundaries, success criteria, and rejected paths.
- `Judge` reviews plans before execution and finds evidence gaps, acceptance gaps, and risky assumptions.
- `Worker` owns one implementation slice and returns changes plus verification evidence.
- `Reviewer` fresh-reviews diffs, tests, artifacts, and PR/CI evidence.

The payoff is practical:

| Benefit | Why |
|---|---|
| Cheaper | Not every task needs the same long context or strongest model; dispatch follows role, risk, and task type. |
| Faster | Independent evidence, design, worker, and review tracks can fan out in parallel while the main agent orchestrates. |
| Better quality | Every subagent has fixed inputs, output packets, and closure conditions; important claims need evidence; non-lightweight results need fresh review. |

### 2. Evidence First: Less Overconfidence, No Silent Fallbacks

The dangerous failure mode is not only that a model does not know something.
It is that the model does not know, but still sounds certain. Another common
failure is planning or executing before human requirements, scope, or acceptance
are clear; even completed work can be wrong. Teamwork also rejects invented
defaults for missing env, paths, hyperparameters, or execution modes. It treats
names, README prose, issues, summaries, `latest`, and `v2` labels as claims
until the agent finds direct evidence; missing required inputs must fail fast.

- Important conclusions are labeled `observed` / `inferred` / `claimed`.
- Key decisions map to source, config, logs, tests, diffs, artifacts, or primary sources.
- When requirements, acceptance, root cause, API behavior, env / paths / hyperparameters, providers, or external constraints are unclear, ask, research, or fail fast before edits.
- Planning and review check evidence adequacy, assumption safety, and acceptance gaps.

This is not ceremony. It keeps model confidence and default-making inside the
boundary of what the evidence can support.

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
| Subagents have no stable boundary | Independent tracks fan out to role subagents with fixed responsibilities, inputs, output packets, and closure conditions |
| The model treats summaries as facts | Important conclusions are labeled `observed` / `inferred` / `claimed` and mapped to direct evidence |
| Done means "the agent says so" | Non-lightweight results default to fresh review; same-context self-review is not acceptance |
| Results hide in long prose | Plans, execution results, reviews, and goal iterations use short tables for human review |
| Failed attempts vanish after a few turns | Reports record attempts, verification, failure class, and next decision |
| Long tasks depend on user reminders | Artifacts and goal loops preserve context, budget, stop rules, and acceptance evidence |

## When To Use It

Good fit:

- Non-lightweight coding-agent work that should fan out research, design, implementation, or review across subagents.
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

## How The Skills Work

`using-teamwork` is the only broad entrypoint: it tries the native fast path first, then escalates only for unclear requirements, missing evidence, planning, fan-out, review, or goal loops.

| Skill | Use It For | Teamwork Capability |
|---|---|---|
| `teamwork-research` | root cause, evidence, options, external constraints | Evidence / Root Cause |
| `teamwork-plan` | explicit plan/design or non-lightweight implementation boundaries | Design Synthesis / Planning Synthesis |
| `teamwork-execute` | accepted plans after go ahead / continue / do it | Staged Execution / Verification Before Claims |
| `teamwork-review` | review, diff, acceptance, PR/CI feedback | Review Reception / Fresh Review |
| `teamwork-goal` | keep going, until it passes, budgeted iteration | Goal Recovery / Convergence |
| `teamwork-init` | AGENTS/CODEX/CURSOR/CLAUDE and instruction slimming | Instruction Slimming |
| `teamwork-update` | version, manifests, install surface, release hygiene | Package Hygiene |

These are Teamwork-owned progressive abilities. Lightweight work does not show internal capability names; complex work loads references, artifacts, packets, or subagents only when needed.

## Platform Positioning

Codex is the reference runtime: native goals are the autonomous control plane, and `teamwork_*` custom agents are the primary collaboration network for non-lightweight work.
`./install.sh codex` writes the global bootstrap policy; `./install.sh codex-policy` prints the App Personalization copy. Full workflow rules stay in skills/references; project files keep local facts and exceptions.

Cursor and Claude Code are adapters: they reuse the same Teamwork protocol
while keeping their own native capabilities. Cursor uses Task subagents;
Claude Code skills and agents install through the matching installer targets,
with rolling reports carrying goal mode.

## Version And Validation

`VERSION` is the package version source of truth and must match `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`. Version, manifest, install-surface refresh, and release-surface updates use `teamwork-update`; it refreshes Teamwork-managed skills, agents, and Codex global policy, with `./install.sh project` for local installs.

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
