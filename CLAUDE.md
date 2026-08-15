# Claude Code compatibility adapter

Claude Code is an explicit compatibility and development target, not part of
the default Codex Update or validation path.

```bash
./install.sh claude
```

`claude` installs the Skills, helper roles, and the managed global policy.
The policy is written to `~/.claude/CLAUDE.md`. To print the same block
without writing it, run `./install.sh claude-policy`.

The adapter exposes the same focused Skills and seven optional helper roles.
Agent availability and adapter freshness never block ordinary work. It creates
no project document schema, Case lifecycle, mandatory Writer workflow, or
migration state.

## Roles and host modes

AskUserQuestion handles bounded Collaborate batches. Task/Agent dispatches
the seven optional helpers. Built-in Explore handles live local search, with
thoroughness quick, medium, or very thorough. Plan mode and the host Plan
subagent are not substitutes for Teamwork Planner. Teamwork Skills add
purpose-specific contracts and checkpoint documents under `docs/teamwork/`.
The adapter exposes the same focused Skills and seven optional helper roles:
Researcher, Debugger, Challenger, Planner, Reviewer, Worker, and Writer.
Claude installs 7 roles; Teamwork Explorer is omitted so it does not sit
beside the built-in Explore. Debugger stays because Claude has no diagnosis
role. Do not name a custom agent `Explore`; that identifier overrides the
built-in.

`--profile` remaps Claude agent pins (`performance-first` / `cost-first`).
Default Update does not touch Claude.

## Project documents

At semantic checkpoints, Skills ask Writer to persist plain Markdown under
`docs/teamwork/` (for example `plans/`, `debug/`, `reviews/`) using
`YYYY-MM-DD-<slug>.md` for a new subject and reusing the path for the same
stable identity. That is durable project memory, not a Case lifecycle, document
schema, JSON index, or migration gate. Writer failure never blocks the primary
method; incomplete document delivery is reported when a checkpoint fired.
