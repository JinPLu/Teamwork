# Claude Code Usage

This repository exposes a router skill plus workflow subskills:

```text
skills/teamwork/SKILL.md
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

The plugin also exposes `/rao:*` commands and a Stop hook backed by
`bin/raoctl.py`. Goal state is project-local under
`.claude/teamwork-goals/`.

Auto-completion requires the configured completion promise, such as
`<promise>RAO_GOAL_COMPLETE</promise>`, plus a structured
`<completion_audit>` block in the same final assistant message. `/rao:complete`
is a manual override and is logged as manual completion.

When editing the workflow, keep the full instructions in the skill files. Do
not duplicate skill bodies into `CLAUDE.md`.
