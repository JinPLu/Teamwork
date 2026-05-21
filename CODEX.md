# Codex Usage

Teamwork in Codex is a workflow layer over native Codex capabilities. It does
not emulate Claude hooks or create a separate agent framework.

Install:

```bash
./install.sh codex
```

The behavior contract lives in `skills/`. Treat names, comments, README claims,
summaries, and tool output as evidence to verify, not facts by themselves.

## Codex Runtime Mapping

- Planning: use `update_plan` only as visible transient progress. It is not a
  durable execution or review artifact. Anchor work to the active objective,
  execution memo, verification target, and review result.
- Research calibration: first establish the local project mainline from repo evidence, then
  use external calibration from official docs, papers, release notes, upstream
  issues, or other primary sources when outside knowledge can prevent local
  dead-end attempts.
- Subagents: use Codex multi-agent support for independent work. For
  non-lightweight tasks, split independent tracks first, dispatch useful
  Explorer/Worker/Reviewer agents early, and keep the main thread on
  non-overlapping work. Explorer and Worker map to native agent types; Designer,
  Judge, and Reviewer are `default` agents with role-specific prompts.
- Model routing: use capability tiers, not fixed model IDs. `fast` maps to low
  reasoning, `standard` to medium, and `high reasoning` to high.
- Goals: use native Codex goals only when explicitly requested or when
  continuing an active goal. Ordinary research, planning, review, and one-shot
  execution do not need a goal.
- Review: `codex review --uncommitted`, `--base`, or `--commit` can be evidence
  for real diffs, never automatic approval.
- Sandbox: request approval for required blocked commands with narrow
  justification. Do not bypass permissions.

Derive native Codex fields from `skills/teamwork/SKILL.md` at dispatch time.
Do not copy `agent_type`, `fork_context`, or `reasoning_effort` into Claude
instructions.

## Artifacts

Use durable Markdown plan artifacts for cross-agent execution, cross-turn work,
high-risk or ambiguous changes, public/shared behavior changes, explicit
repository plans, and all goal-mode execution. Treat them as compact execution
memos, not process logs.

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

For non-trivial research, search existing artifacts before re-searching. Update
or cite applicable files and record both local evidence and external
calibration sources.

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

Use final reports only for non-trivial conclusions that should survive the
conversation:

```text
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

Small, low-risk edits may use a concise chat/native plan instead of a
repository artifact.

It is not Codex goal state and not Claude `.claude/teamwork-goals/` runtime state. The Markdown plan remains the shared execution and review source of truth.

## External Information Policy

1. Use repo files, logs, tests, artifacts, and prior research to understand
   project reality and current progress.
2. Use MCP before generic network access when a relevant server exists.
3. Use web or other external sources for non-trivial research where current
   platform, model, dependency, upstream, or field practice could affect the
   answer.
4. If web, MCP, credentials, or filesystem access require approval, request it
   through Codex. Do not mine local proxy or token files unless explicitly
   authorized.
5. If access is unavailable, record the limitation in the research artifact and
   continue only to the local-evidence boundary.

When editing workflow behavior, update the relevant `skills/*/SKILL.md` first.
