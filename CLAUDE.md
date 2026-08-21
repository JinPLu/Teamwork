@AGENTS.md

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

AskUserQuestion handles bounded Collaborate batches. Task/Agent dispatches the
seven optional helpers: Researcher, Debugger, Challenger, Planner, Reviewer,
Worker, and Writer. Writer is a Task/Agent helper role, not a Skill. Built-in
Explore handles live local search, with thoroughness quick, medium, or very
thorough; do not name a custom agent `Explore`, because that identifier
overrides the built-in. Plan mode and the host Plan subagent are not
substitutes for Teamwork Planner. Debugger stays because this host has no
diagnosis mode. Claude still installs Debug, Goal, and Debugger.

The managed block in `~/.claude/CLAUDE.md` owns the host mapping: which native
surface is an editable candidate, which signal is acceptance, and which host
paths are machine-local rather than Teamwork persistence — the plan file under
`~/.claude/plans/` and auto memory under
`~/.claude/projects/<project>/memory/`. Accepted reusable results persist under
<!-- BEGIN GENERATED: kind-root -->
`docs/teamwork/<kind>/`
<!-- END GENERATED: kind-root -->
. This host reads `CLAUDE.md` and not `AGENTS.md`, so `init-project` also
writes a small managed `@AGENTS.md` import and the project block is loaded
through it.

A Cursor install that refreshes this Claude skill root still installs the full
Claude set. When both same-named Teamwork skill copies exist under
`~/.cursor/skills/` and `~/.claude/skills/`, which copy a dual-host session
reads is not guaranteed—keep both in sync via the installers.

Claude agents pin models by job and ignore `--profile`: Reviewer runs Opus at
max effort; Researcher, Debugger, Challenger, and Planner run Opus at xhigh;
Worker runs Sonnet at high; Writer runs Sonnet at medium. The pins are defaults,
not locks: `CLAUDE_CODE_SUBAGENT_MODEL` and a per-dispatch model both override
them, and an unpinned role would inherit the session model and effort. Default
Update does not touch Claude.
