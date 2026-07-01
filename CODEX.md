# Codex Usage

Teamwork for Codex is the reference adapter for this open-source skill package.
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
./install.sh codex --profile gpt55-xhigh
./install.sh codex-agents
./install.sh codex-policy
./install.sh all
```

Use `./install.sh project` or `./install.sh --project-root <path> project` for
project-local skills and agents. Use `./install.sh --project-root <path>
--profile gpt55-xhigh project-codex-agents` when only Codex subagent model
definitions need the xhigh override. Use `./install.sh --link codex` while
editing this checkout.

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

The global Codex bootstrap block installed by `./install.sh codex` authorizes
subagents when Teamwork dispatch policy says they are worthwhile, sets the
profile, applies think-first discipline to non-trivial or evidence-sensitive
work, minimizes optional commentary, and states the no-silent-defaults rule for
required values.

## Subagents

Codex subagents are used for independent tracks, not as a default reflex.
Typical roles:

- Explorer: evidence gathering, source/literature census, artifact lookup;
- Designer: option comparison and plan shape;
- Judge: plan adequacy before high-risk execution;
- Worker: owned implementation or verification slice;
- Reviewer: fresh-context acceptance review.

The main agent remains responsible for user questions, scope, integration,
verification, and final response. Every subagent returns one packet, then stops;
no delegated track may remain open at completion.

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

Use durable artifacts for broad research, goal-mode work, failed iteration,
delegated execution, high-risk or public behavior, and explicit repository plans.
Do not store volatile chat progress in project instructions.

## Goal Mode

The Codex runtime profile uses native Codex goals as the autonomous control
plane. If the target is unclear, first return a chat `Goal Proposal`; after user
approval, use native goal state for lifecycle and Teamwork artifacts for
evidence, plan, attempts, and acceptance. Failed attempts should refresh
research or plan adequacy before another retry.

## Updates

Use `teamwork-update` for both user refreshes and maintainer releases.

```bash
./scripts/check-update.sh --project <path>
./scripts/validate.sh
```

User refresh updates installed skills, agents, and policy. Maintainer release
work updates `VERSION`, manifests, docs, validation, and install surfaces
together.
