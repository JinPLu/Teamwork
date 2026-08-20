# Claude Code compatibility adapter

Claude Code is an explicit compatibility and development target, not part of
the default Codex Update or validation path.

```bash
./install.sh claude
```

`claude` installs the Skills, helper roles, and the managed global policy.
The policy is written to `~/.claude/CLAUDE.md`. To print the same block
without writing it, run `./install.sh claude-policy`. Invoke Skills with
`/name` in Claude Code (for example `/teamwork-collaborate`); Codex uses
`$name`.

The adapter exposes the same focused Skills and seven optional helper roles.
Agent availability and adapter freshness never block ordinary work. It creates
no project document schema, Case lifecycle, mandatory Writer workflow, or
migration state.

## Roles and host modes

AskUserQuestion handles bounded Collaborate batches. Task/Agent dispatches
the seven optional helpers. Built-in Explore handles live local search, with
thoroughness quick, medium, or very thorough. Plan mode and the host Plan
subagent are not substitutes for Teamwork Planner. Plan mode is a read-only
permission boundary; do not write project files during that phase.
AskUserQuestion batches collect input and do not by themselves complete a
Skill checkpoint. After the user approves exiting Plan, write permission
returns; deliver the accepted result in that same response cycle. Writer
is a Task/Agent helper role, not a Skill. Root owns document delivery and may
write the Skill template directly or delegate to Writer when that does not
delay the current checkpoint write. Teamwork Skills add purpose-specific
contracts and checkpoint documents under `docs/teamwork/`. The adapter exposes the same focused Skills
and seven optional helper roles: Researcher, Debugger, Challenger, Planner,
Reviewer, Worker, and Writer. Claude installs 7 roles; Teamwork Explorer is
omitted so it does not sit beside the built-in Explore. Debugger stays because
Claude has no diagnosis role. Claude still installs Debug, Goal, and Debugger.
Cursor omits those Skills and the Debugger role; a Cursor install that
refreshes this Claude skill root still installs the full Claude set. Do not name a custom agent `Explore`; that
identifier overrides the built-in.

When both same-named Teamwork skill copies exist under `~/.cursor/skills/` and
`~/.claude/skills/`, which copy a dual-host session reads is not guaranteed—
keep both in sync via the installers.

`--profile` remaps Claude agent pins (`performance-first` / `cost-first`).
Default Update does not touch Claude.

## Project documents

After the method's user-facing result exists, Root owns delivery of the
checkpoint document as plain Markdown under `docs/teamwork/` (for example
`plans/`, `debug/`, `reviews/`) using `YYYY-MM-DD-<slug>.md` for a new subject
and reusing the path for the same stable identity. Write in the same response
cycle as that result. Writer is optional and must not delay the current
checkpoint write. That is durable project memory, not a Case lifecycle,
document schema, JSON index, or migration gate. When the current environment
cannot write, report the exact expected path and that the document was not
delivered. A write failure is visible and does not undo the completed result.
Invoking a host plan or question UI is not durable memory; a user-accepted
reusable result is. A temporarily read-only Plan delays that delivery until
write permission returns.
