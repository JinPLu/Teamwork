# Codex Usage

Teamwork for Codex is the reference Codex runtime profile for this open-source
skill package.
It helps a personal research-collaboration agent do deeper research, controlled
delegation, coding, review, and long-running verification without turning every
prompt into a process exercise.

Codex native capabilities remain the execution substrate: goals, `update_plan`,
custom agents, review, sandbox approvals, permission profiles, automations, MCP,
plugins, browser/visual evidence, Computer Use, and remote execution. Teamwork
adds the decision layer: when to research, when to plan, when to fan out, when
to stop on missing required state, and how to attach evidence to completion.

`VERSION` is the package version source of truth. It should match
`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`.

## Install

```bash
./install.sh              # same as ./install.sh codex
./install.sh codex --profile cost-first
./install.sh codex --profile gpt56-role
./install.sh codex --profile gpt55-high
./install.sh codex --profile gpt55-xhigh
./install.sh codex-agents
./install.sh codex-policy
./install.sh all
```

Use `./install.sh project` or `./install.sh --project-root <path> project` for
project-local skills and agents. Use `./install.sh --project-root <path>
--profile gpt56-role project-codex-agents` for the role-tiered GPT-5.6 mapping;
use `--profile gpt55-high` or `--profile gpt55-xhigh` for explicit all-agent
GPT-5.5 overrides. Use
`./install.sh --link codex` while editing this checkout.

## How To Use

Ask normally. Teamwork routes only when the task benefits from extra structure:

- research a paper, field, API, project history, or source corpus before acting;
- compare options and produce a plan with scope, gates, and verification;
- implement an accepted plan or known root-cause fix;
- debug failures with runtime evidence instead of guessing;
- review output for false success, defensive fallback, weak evidence, or AI
  bloat;
- keep going until a goal is verified, budget is exhausted, or a real blocker
  appears.

Small facts, tiny edits, and obvious local fixes stay on Codex's native fast
path. Teamwork should improve correctness or continuity; it should not add
ceremony to simple work.

## Project Setup

Use `teamwork-init` when a repository needs Teamwork installed, instructions
slimmed, `AGENTS.md`/`CODEX.md`/`CURSOR.md`/`CLAUDE.md` aligned, CodeGraph policy
recorded, or `docs/teamwork/` created. Project instructions should hold local
facts, required values, protected boundaries, and acceptance checks. Reusable
workflow rules belong in Teamwork skills.

The global Codex bootstrap block installed by `./install.sh codex` stays small:
it records authorization, required-state, scope, evidence, and delegation
boundaries plus the active profile name. Installed agent files own exact model
and effort mappings.

## Subagents

Codex subagents are used for independent tracks, not as a default reflex.
Typical roles:

- Explorer: evidence gathering, source/literature census, artifact lookup;
- Designer: option comparison and plan shape;
- Judge: plan adequacy before high-risk execution;
- Worker: owned implementation or verification slice;
- Reviewer: fresh-context acceptance review.

The main agent remains responsible for user questions, scope, integration,
verification, and final response. Every subagent returns one bounded result,
then stops; add role-specific fields only when they affect the parent decision.

Advanced dispatch fields, role mapping, model classes, and lifecycle details
live in `skills/using-teamwork/references/subagent-dispatch.md`. Prompt and
packet contracts live in `subagent-contract.md`.

## Evidence And Memory

Teamwork treats repo files, source excerpts, papers, official docs, tests, logs,
diffs, screenshots, artifacts, and fresh review as evidence. Names, comments,
model summaries, and "latest" labels are claims until verified.

Reusable or cross-turn findings live in:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

Use durable artifacts when evidence or state needs cross-turn reuse, supports a
goal, records repeated failure, or justifies high-risk/public behavior.
Do not store volatile chat progress in project instructions.

## Goal Mode

Use native Codex goal state when the user explicitly requests that control
surface or accepts a Goal Proposal. Do not invent a numeric budget; use the
user/runtime budget or stop after repeated no-progress without a new strategy.

## Updates

Use `teamwork-update` for both user refreshes and maintainer releases.

```bash
./scripts/check-update.sh --project <path>
./scripts/validate.sh
python3 scripts/run-teamwork-live-eval.py --help
```

User refresh updates installed skills, agents, and policy. Maintainer release
work updates `VERSION`, manifests, docs, validation, and install surfaces
together.
