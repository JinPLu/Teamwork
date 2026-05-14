# Claude Code Usage

This repository exposes a router skill plus workflow subskills:

```text
skills/teamwork/SKILL.md
skills/teamwork-goal/SKILL.md
skills/teamwork-design/SKILL.md
skills/teamwork-execute/SKILL.md
skills/teamwork-review/SKILL.md
```

Install globally:

```bash
./install.sh claude
```

Claude Code plugin metadata lives in:

```text
.claude-plugin/plugin.json
```

The plugin exposes `/teamwork:*` commands, `/rao:*` compatibility aliases, and
a Stop hook backed by `bin/raoctl.py`. Goal state is project-local under
`.claude/teamwork-goals/` and can record `active_plan_artifact`.

Auto-completion requires the configured completion promise, such as
`<promise>RAO_GOAL_COMPLETE</promise>`, plus a structured
`<completion_audit>` block in the same final assistant message. The audit must
include a `plan_artifact` matching runtime state. `/teamwork:complete` and
`/rao:complete` are manual overrides and are logged as manual completion.

When editing the workflow, keep the full instructions in the skill files. Do
not duplicate skill bodies into `CLAUDE.md`.
