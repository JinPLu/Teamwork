# Teamwork

[中文](README.md)

**A personalized research-collaboration layer for deep research, planning, coding, review, and verifiable progress.**

Teamwork is a **Codex-first Codex + Cursor + Claude Code skill package**.
It turns Codex, Cursor, and Claude Code from one-off chat assistants into a
personal research collaboration agent for long-running projects. It does not
replace editors, shell, MCP, browser, permission, or test tools; those native
capabilities still execute the work. Teamwork solves the layer above them: how
complex tasks gather evidence, split work, preserve context, and prove progress.

Coding is one of the main execution surfaces, but Teamwork research, planning,
review, and memory are not coding-only. They also fit literature review, field
research, option comparison, experiment design, source synthesis, and long-term
project follow-through.

![Teamwork workflow explainer](assets/teamwork-workflow-gpt-image-2.png)

## Why It Exists

The hard part of personal research and engineering work is usually not that the
model cannot answer. It is that the agent:

- stops research at one paper, README, or search result;
- mixes research, design, implementation, experiments, and review in one long chat;
- lets parallel subagents become disconnected chats;
- invents defaults for missing env, paths, ports, model names, hyperparameters, or source data;
- forgets research, plans, failed attempts, and acceptance evidence across long runs;
- ends with "done" instead of sources, experiments, tests, logs, diffs, artifacts, or fresh review.

Teamwork turns those risks into workflow constraints: research before planning,
fan out only when tracks are independent, ask/research/block when required state
is missing, and attach verification evidence to non-lightweight results.

## Core Advantages

| User Problem | Plain Agent / Simple Subagents | Teamwork |
|---|---|---|
| Shallow research | Stops at the seed source | Expands from seed source to source census, primary sources, neighboring sources, counter-evidence, and open questions |
| Uncontrolled delegation | Parallel chats drift apart | Only independent tracks fan out; Explorer, Designer, Judge, Worker, and Reviewer return packets for the main agent to integrate |
| Weak evidence | Treats titles, summaries, filenames, `latest`, or `v2` labels as facts | Maps important claims to papers, docs, source, config, logs, tests, diffs, artifacts, or primary sources |
| Fake fallback | Defensive defaults hide missing state | Required values must come from the user, project files, source, tests, or an accepted plan; otherwise ask, research, or stop |
| Repeated guessing | Failure just triggers another guess | Records hypothesis, verification, failure class, and next step, then refreshes research or plan adequacy when needed |
| Unreviewable done | Completion is self-reported | Execution returns verification evidence; important outcomes enter review or goal loops |

The point is not more process. It is to make evidence, delegation, memory, and
acceptance inspectable when the task is too large for a single linear chat.

## When To Use It

If the task crosses papers, pages, code, data, turns, tools, or agents, or if an agent has already
started guessing, retrying, and claiming success without proof, Teamwork is worth installing.

Good fit:

- Research a field, paper, API, library, competitor, historical decision, or project corpus before planning.
- Compare research/engineering directions, design experiments, synthesize evidence, or drive long-running projects.
- Code, debug reproducible failures, flaky tests, CI failures, crashes, or UI symptoms and prove root cause.
- Fan out subagents across research, design, implementation, or review while keeping one main integrator.
- Run strict review, deslop passes, AI-output cleanup, code-quality cleanup, or PR/CI review.
- Iterate until tests pass, a target is met, budget is exhausted, or a real blocker appears.

Skip it for:

- One-line facts, tiny obvious edits, or local syntax questions.
- Tightly coupled critical paths where subagent context cost exceeds value.
- Sensitive, destructive, or explicitly human-confirmed operations.

## How To Use It

Keep asking in natural language. Users do not need workflow labels:

```text
Research this field, key papers, and the existing code first, then propose a plan.
Fan out subagents to compare directions, then recommend one executable path.
Execute the plan; record failure reasons and evidence until tests pass.
Strictly review this output for fake success, defensive fallback, and AI bloat.
```

`using-teamwork` decides whether to stay on the native fast path or route into
research, debug, plan, execute, review, goal, init, or update. Small work stays
direct; complex work loads the extra rules, subagents, and artifacts only when useful.

## Quick Install

Codex default install:

```bash
./install.sh              # same as ./install.sh codex
./install.sh codex --profile cost-first
./install.sh codex --profile gpt55-xhigh
```

Other platforms:

```bash
./install.sh cursor|claude|all
./install.sh cursor-agents|claude-agents
./install.sh cursor-policy-copy|cursor-policy|claude-policy
```

Project installs and local development:

```bash
./install.sh project
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project --profile gpt55-xhigh project-codex-agents
./install.sh --project-root /path/to/project init-project
./install.sh --link codex
```

`project` installs project-local skills/agents; `init-project` runs full project
initialization. The Codex global policy matches reasoning depth to non-trivial
or evidence-sensitive work, reads sources and verifies when needed, and
minimizes optional progress narration. `teamwork-init` owns project rules,
AGENTS/CODEX/CURSOR/CLAUDE, `docs/teamwork/`, and CodeGraph setup. `teamwork-update` and
`./scripts/check-update.sh` refresh skills/agents/policy and check installed
surfaces plus version drift.

## How It Works

Teamwork skills trigger only when needed:

| Capability | Trigger |
|---|---|
| `teamwork-research` | sources, evidence, options, external constraints, or repro surface are unclear |
| `teamwork-debug` | logs, CI, crashes, flaky runs, or UI symptoms need runtime evidence |
| `teamwork-plan` | boundaries, acceptance, dispatch guidance, or stop rules are needed |
| `teamwork-execute` | execute an accepted plan, checklist, scope, or known root-cause fix |
| `teamwork-review` | fresh review, strict quality, deslop, PR/CI review, or completion acceptance |
| `teamwork-goal` | keep going, until green/done, or budgeted iteration |

When work needs durable state, artifacts live at:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

## Version And Validation

`VERSION` matches the plugin manifests. Before refresh or release:

```bash
./scripts/check-update.sh --project /path/to/project
./scripts/validate.sh
```

## Read More

- [CODEX.md](CODEX.md): Codex usage, Goal Mode, and custom-agent mapping.
- [CURSOR.md](CURSOR.md): Cursor usage.
- [CLAUDE.md](CLAUDE.md): Claude Code usage.
- `skills/*/SKILL.md`: workflow skill behavior.
- `skills/using-teamwork/references/`: dispatch, packet, artifact, review, and goal details.
