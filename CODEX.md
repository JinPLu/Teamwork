# Codex Usage

This repository exposes a router skill plus workflow subskills:

```text
skills/teamwork/SKILL.md
skills/teamwork-design/SKILL.md
skills/teamwork-execute/SKILL.md
skills/teamwork-review/SKILL.md
```

Install globally:

```bash
./install.sh codex
```

Codex plugin metadata lives in:

```text
.codex-plugin/plugin.json
```

The detailed behavior contract lives in the skill files. In particular, treat
names, version labels, comments, README claims, summaries, and tool output as
evidence to verify, not as facts or final verdicts by themselves.

## Codex Runtime Mapping

- Planning/checklists: use `update_plan` for visible multi-step state.
- Autonomous convergence: use native Codex goals only when explicitly
  requested, or continue an active goal. Ordinary research, planning, review,
  and one-shot execution do not need a goal.
- Subagents: use Codex multi-agent support for independent research, judge,
  worker, and review tracks. The main agent owns synthesis, conflict
  resolution, and the final recommendation.
- Review: use `codex review --uncommitted`, `--base`, or `--commit` when a real
  git diff exists and a separate native review is useful. Treat the result as
  evidence, not automatic approval.
- MCP: use configured MCP servers before ad hoc network fallback when the task
  needs external tool or documentation access.
- Network/web: use only when allowed or when current external information is
  required; prefer primary sources.
- Sandbox: request escalation only for required blocked commands, with narrow
  justification and prefix rule where appropriate. Do not bypass approvals.

## External Information Policy

1. Prefer repository files, local artifacts, command help, and configured MCP
   servers.
2. Use MCP before generic network access when a server exists for the domain.
3. If MCP, network, credentials, or filesystem access require approval, request
   it through Codex. Do not mine local proxy or token files unless the user
   explicitly authorizes that source.
4. If web or network access is disabled or forbidden, report the limit and
   continue only with local evidence.

When editing the workflow, keep the full instructions in the skill files. Do
not duplicate skill bodies into Codex-specific docs.
