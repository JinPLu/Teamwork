# Cursor Usage

Teamwork is a platform-native augmentation layer for Cursor. Cursor native
capabilities remain the substrate: editing, shell, MCP, permissions, `Task`
subagents, custom agents under `~/.cursor/agents/`, browser automation, and
verification. Teamwork defines when and how those capabilities should be combined
for evidence-heavy, reviewed, delegated, or autonomous work. After Teamwork
activates, the main agent upgrades from native flow only when evidence, planning,
dispatch, review, memory, or goal convergence improves correctness, continuity,
or cost.

## Install

```bash
./install.sh cursor
./install.sh cursor --profile cost-first
# agents-only refresh when skills should not change:
./install.sh cursor-agents
# print the bootstrap block for Cursor User Rules:
./install.sh cursor-policy
# or refresh every platform:
./install.sh all
```

Project-local skills and agents:

```bash
./install.sh project
```

Local development with symlinks:

```bash
./install.sh --link cursor
./install.sh --link all
./install.sh --link project
```

Skills install to `~/.cursor/skills/` (global) or `.cursor/skills/` (project).
Custom role agents install to `~/.cursor/agents/` (global) or
`.cursor/agents/` (project). Behavior lives in `skills/`; this file is a concise
runtime summary.

**Discovery**: Cursor sessions should load Teamwork from `~/.cursor/skills/` or
the project `.cursor/skills/`. Stale copies under `~/.claude/skills/` (especially
the retired `teamwork` umbrella skill) can preempt routing; run `./install.sh all`
after upgrades.

## Global Policy

Cursor has no documented home-file path for User Rules. `./install.sh
cursor-policy` prints the Teamwork bootstrap block to paste into Cursor Settings
→ Rules → User Rules. Project `AGENTS.md` or a Cursor-labeled section holds only
local facts, required values, protected boundaries, or opt-outs.

## Subagent Dispatch

Teamwork keeps conceptual roles (Explorer, Designer, Judge, Worker, Reviewer) and
model classes (`cheap-fast`, `balanced`, `coding`, `frontier`, `inherited`)
platform-neutral. At dispatch time, decide and translate native Cursor fields
with `skills/using-teamwork/references/subagent-dispatch.md`.

Teamwork activation is standing authorization for stage-routed dispatch when it
adds value; the user does not need to say "fan out subagents". Dispatch
independent Explorer, Designer, Judge, Worker, or Reviewer tracks when they can
improve evidence, elapsed time, context isolation, ownership clarity, or review
quality. Use a fresh Reviewer for required acceptance when available; otherwise
label residual unreviewed risk.

Prefer installed Teamwork custom agents from `~/.cursor/agents/` or
`.cursor/agents/` by agent `name`. Built-in fallback when unavailable:

- Explorer -> `subagent_type:"explore"`
- Worker -> `subagent_type:"generalPurpose"` or `shell` for shell-only tracks
- Reviewer -> `subagent_type:"code-reviewer"`
- Designer/Judge -> `subagent_type:"generalPurpose"` with role in prompt

Each subagent is a bounded packet producer; close, block, or abandon its Actual
Dispatch Log entry after integration before claiming acceptance.

For broad research, keep recall broad but context transport narrow: use source census,
capped Explorer packets, and artifact-backed evidence ledgers instead of returning
raw search output, long matrices, or copied source bodies to the main thread.
Treat compaction as continuity support, not audit evidence.

## Profile And Models

`./install.sh cursor --profile performance-first|cost-first` renders installed
Cursor agents. `performance-first` is default: Explorer/Designer use
`claude-sonnet-4-6`, Worker uses `composer-2.5-fast`, Judge/Reviewer/Deep
variants use `claude-opus-4-8-thinking-high`. `cost-first` downshifts routine
roles to `composer-2.5-fast`; review tiers stay on
`claude-opus-4-8-thinking-high`. Use only models listed in the active `Task`
tool schema.

## Goal Mode

Cursor has no native `create_goal`. Goal-mode work uses the same controller loop,
Stop Rules, and Research + Plan Adequacy Gate as Codex:

1. Return a chat-only `Goal Proposal` when the target is unclear.
2. After approval, initialize `docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md`
   with `Status: active` and put the Goal Text in the report Abstract.
3. Drive `research -> plan -> execute -> verify -> review -> append report row`
   from chat until verification and execution review pass, or budget/blocker stops.
4. Mark completion by setting the report `Status: accepted`.

The rolling report is the durable goal surface on Cursor. See
`skills/using-teamwork/references/goal-iteration.md` for the full loop.

For repeated failures or unknown-cause regressions inside that loop, route through
`teamwork-debug` before retrying speculative fixes.

## Teamwork Memory

When `docs/teamwork/index.json` exists and durable memory is relevant, Teamwork
routes read it before historical artifacts. Stages report `Memory Delta` only
when durable memory was checked or changed.

## Router

`using-teamwork` is the automatic lean entrypoint. It routes unclear source or
repro setup to research, reproducible failures to `teamwork-debug`, accepted
fixes to execute, and keeps Debug as a stage rather than a new role. Stage
skills load focused references only as needed.
