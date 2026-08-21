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
is a Task/Agent helper role, not a Skill. Teamwork Skills add purpose-specific
contracts and checkpoint documents under
<!-- BEGIN GENERATED: kind-root -->
`docs/teamwork/<kind>/`
<!-- END GENERATED: kind-root -->
. The adapter exposes the same focused Skills
and seven optional helper roles: Researcher, Debugger, Challenger, Planner,
Reviewer, Worker, and Writer.
<!-- BEGIN GENERATED: host-counts -->
Claude Code installs 7 roles and omits Explorer because that host already provides Explore. Cursor installs 6 roles and omits Explorer and Debugger, and does not install the Debug or Goal Skills; unknown-cause diagnosis uses host Debug. Codex retains the Explorer role, plus Debug, Goal, and Debugger.
<!-- END GENERATED: host-counts -->
Debugger stays because Claude has no diagnosis role. Claude still installs Debug, Goal, and Debugger.
A Cursor install that refreshes this Claude skill root still installs the
full Claude set. Do not name a custom agent `Explore`; that identifier
overrides the built-in.

When both same-named Teamwork skill copies exist under `~/.cursor/skills/` and
`~/.claude/skills/`, which copy a dual-host session reads is not guaranteed—
keep both in sync via the installers.

`--profile` remaps Claude agent pins (`performance-first` / `cost-first`).
Default Update does not touch Claude.
