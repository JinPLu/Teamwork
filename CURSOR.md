# Cursor Usage

Teamwork is a platform-native augmentation layer for Cursor. Cursor native
capabilities remain the substrate: editing, shell, MCP, permissions, `Task`
subagents, browser automation, and verification. Teamwork defines when and how
those capabilities should be combined for evidence-heavy, reviewed, delegated, or
autonomous work.

## Install

```bash
./install.sh cursor
```

Local development with symlinks:

```bash
./install.sh --link cursor
```

Skills install to `~/.cursor/skills/`. Behavior lives in `skills/`; this file is
a concise runtime summary.

## Subagent Dispatch

Teamwork keeps conceptual roles (Explorer, Designer, Judge, Worker, Reviewer) and
model classes (`cheap-fast`, `balanced`, `coding`, `frontier`, `inherited`)
platform-neutral. At dispatch time, translate them through Cursor mapping in
`skills/using-teamwork/references/dispatch-policy.md`:

- Explorer -> `subagent_type:"explore"`
- Worker -> `subagent_type:"generalPurpose"` or `shell` for shell-only tracks
- Reviewer -> `subagent_type:"code-reviewer"`
- Designer/Judge -> `subagent_type:"generalPurpose"` with role in prompt

Model classes map to Cursor `Task` models such as `composer-2.5-fast`,
`gpt-5.5-medium`, and `claude-opus-4-7-thinking-high`.
Use only models listed in the active `Task` tool schema.

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

## Router

`using-teamwork` is the automatic lean entrypoint. Stage skills load focused
references only as needed.
