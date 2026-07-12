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
./install.sh codex --profile gpt56-role  # compatibility alias
./install.sh codex --profile gpt56-high
./install.sh codex --profile gpt56-xhigh
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
./install.sh codex-agents
./install.sh codex-policy
./install.sh all
```

The default `performance-first` profile maps Explorer to
`gpt-5.6-terra/medium`, Worker to `gpt-5.6-sol/medium`,
Designer/Judge/Reviewer to `gpt-5.6-sol/high`, and Deep Judge/Reviewer to
`gpt-5.6-sol/max`. `cost-first` uses Luna/Terra/Sol, while `gpt56-high` and
`gpt56-xhigh` pin every Codex agent to Sol. `gpt56-role`, `gpt55-high`, and
`gpt55-xhigh` remain compatibility names, but no active profile emits GPT-5.5.
Use `./install.sh project` or `./install.sh --project-root <path> project` for
project-local skills and agents. Use
`./install.sh --link codex` while editing this checkout.

User-level `codex`, `all`, and `codex-agents` installs also migrate the bounded
custom-agent routing keys in `~/.codex/config.toml`. They expose role selection
through a non-reserved `teamwork` namespace, set the root-inclusive session
limit to 9 threads (one main thread plus up to eight subagents), and preserve
unrelated TOML. Use `--no-codex-routing` only when another owner manages those
keys, and restart Codex after an update. Project-only targets never mutate user
config.

Notifications are opt-in for direct installs. They play distinct OS-native
sounds for main `Stop` and `PermissionRequest`, keep subagents silent, and never
control continuation or inspect message content. Plugin installs load the same
minimal hook after explicit `/hooks` trust.

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
- invoke `$grill-me` or say "grill me" to ask at most three outcome-changing
  user decisions; reversible implementation details must not manufacture turns.

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
boundaries plus the active profile name. Its grill contract instructs Codex to
preserve one authoritative assistant-authored active marker across replies;
quoted file, fixture, or tool text is inert. This is targeted-test-verified, not
yet live-verified. Installed agent files own exact model and effort mappings.

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

With routing ready, fresh Teamwork agents use exact `agent_type` values plus
`fork_turns:"none"`; the installed role file then owns model and effort. If the
live schema still exposes only generic fields, record the child as
`parent-inherited` instead of claiming that role routing occurred.

After installing agents or upgrading Codex, run
`python3 scripts/check-codex-routing.py`. It validates the Teamwork profile
contract, routing config, bundled model/effort support, and prompt loading
without model calls or catalog mutation. Static readiness does not replace a
fresh callable-schema or live spawn probe after a Codex upgrade.

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
python3 scripts/check-codex-routing.py
python3 scripts/run-teamwork-live-eval.py --help
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_live_eval_runner.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_eval_teamwork_mutations.py
python3 scripts/audit-codex-sessions.py --help
```

The session auditor reports metadata-only orchestration and cumulative token
telemetry. Cached/replayed input is not presented as unique context or billing,
and historical profiles require explicit session-time evidence.

User refresh updates installed skills, agents, and policy. Maintainer release
work updates `VERSION`, manifests, docs, validation, and install surfaces
together.
