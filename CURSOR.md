# Cursor Usage

Teamwork is a platform-native augmentation layer for Cursor. Cursor native
capabilities remain the substrate: editing, shell, MCP, permissions, `Task`
subagents, browser automation, and verification. Teamwork defines when and how
those capabilities should be combined for evidence-heavy, reviewed, delegated, or
autonomous work. After Teamwork activates, the main agent upgrades from native
flow only when evidence, planning, dispatch, review, memory, or goal
convergence improves correctness, continuity, or cost.

## Install

```bash
./install.sh cursor
# or refresh every platform:
./install.sh all
```

Project-local skills (clone-and-use in this repo):

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
Behavior lives in `skills/`; this file is a concise runtime summary.

**Discovery**: Cursor sessions should load Teamwork from `~/.cursor/skills/` or
the project `.cursor/skills/`. Stale copies under `~/.claude/skills/` (especially
the retired `teamwork` umbrella skill) can preempt routing; run `./install.sh all`
after upgrades.

## Subagent Dispatch

Teamwork keeps conceptual roles (Explorer, Designer, Judge, Worker, Reviewer) and
model classes (`cheap-fast`, `balanced`, `coding`, `frontier`, `inherited`)
platform-neutral. At dispatch time, decide with
`skills/using-teamwork/references/dispatch-policy.md` and translate native
fields through Cursor mapping in
`skills/using-teamwork/references/platform-dispatch-mapping.md`:

Teamwork activation is standing authorization for stage-routed dispatch when it
adds value; the user does not need to say "fan out subagents". Dispatch
independent Explorer, Designer, Judge, Worker, or Reviewer tracks when they can
improve evidence, elapsed time, context isolation, ownership clarity, or review
quality. Use a fresh Reviewer for required acceptance when available; otherwise
label residual unreviewed risk.
Each subagent is a bounded packet producer; close, block, or abandon its Actual
Dispatch Log entry after integration before claiming acceptance.

For broad research, keep recall broad but context transport narrow: use source census,
capped Explorer packets, and artifact-backed evidence ledgers instead of returning
raw search output, long matrices, or copied source bodies to the main thread.
Treat compaction as continuity support, not audit evidence.

- Explorer -> `subagent_type:"explore"`
- Worker -> `subagent_type:"generalPurpose"` or `shell` for shell-only tracks
- Reviewer -> `subagent_type:"code-reviewer"`
- Designer/Judge -> `subagent_type:"generalPurpose"` with role in prompt

Model classes map to Cursor `Task` models: `composer-2.5-fast` only for
opt-in `cheap-fast`, `gpt-5.5-medium` for `balanced` and `coding` when listed,
and `claude-opus-4-7-thinking-high` for `frontier`. Use only models listed in
the active `Task` tool schema; if `gpt-5.5-medium` is unavailable, choose the
strongest non-frontier model rather than collapsing normal work to fast.

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

## Teamwork Memory

When `docs/teamwork/index.json` exists and durable memory is relevant, Teamwork
routes read it before historical artifacts. Stages report `Memory Delta` only
when durable memory was checked or changed.

## Router

`using-teamwork` is the automatic lean entrypoint. Stage skills load focused
references only as needed.
