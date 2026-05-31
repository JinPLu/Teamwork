# Platform Dispatch Mapping

Use when translating Teamwork roles into native subagent fields. Dispatch
decisions stay in `dispatch-policy.md`.

## Platform Dispatch Fields

- Codex: `agent_type`, `model`, `reasoning_effort`, `fork_context`.
- Cursor: `subagent_type`, `model`; no `reasoning_effort` or `fork_context`.
- Claude Code: `subagent_type` (user-defined agent name under
  `~/.claude/agents/` or `general-purpose`); `model` lives on the agent
  definition.

## Codex Mapping

- Explorer -> `agent_type:"teamwork_explorer"`.
- Worker -> `agent_type:"teamwork_worker"`.
- Designer -> `agent_type:"teamwork_designer"`.
- Judge -> `agent_type:"teamwork_judge"`.
- Reviewer -> `agent_type:"teamwork_reviewer"`.
- Fallback when custom agents are unavailable: Explorer -> `agent_type:"explorer"`;
  Worker -> `agent_type:"worker"`; Designer, Judge, Reviewer ->
  `agent_type:"default"` with role in prompt.
- `fast` -> `reasoning_effort:"low"`.
- `standard` -> `reasoning_effort:"medium"`.
- `high reasoning` -> `reasoning_effort:"high"`.

## Codex Model Mapping

- `cheap-fast` -> `gpt-5.4-mini`; opt-in only for trivial read-only output
  under explicit latency/quota pressure.
- `balanced` -> `gpt-5.4`.
- `coding` -> `gpt-5.3-codex`.
- `frontier` -> `gpt-5.5`.
- `inherited` -> omit `model`; record why inheritance beats Role Profile.

## Codex Native Field Presets

Use Teamwork custom agents when installed. For built-in fallbacks:

- Explorer default: `agent_type:"explorer"`, `model:"gpt-5.4"`, `reasoning_effort:"medium"`.
- Worker default: `agent_type:"worker"`, `model:"gpt-5.3-codex"`, `reasoning_effort:"medium"`.
- Designer default: `agent_type:"default"`, `model:"gpt-5.4"`, `reasoning_effort:"medium"`; prompt says `Conceptual Role: Designer`.
- Judge default: `agent_type:"default"`, `model:"gpt-5.5"`, `reasoning_effort:"high"`; prompt says `Conceptual Role: Judge`.
- Reviewer default: `agent_type:"default"`, `model:"gpt-5.5"`, `reasoning_effort:"high"`.

Do not combine `fork_context:true` with `agent_type`, `model`, or
`reasoning_effort`; full-history forks inherit parent routing.

## Cursor Mapping

- Explorer -> `subagent_type:"explore"`.
- Worker -> `subagent_type:"generalPurpose"`; use `shell` for shell-only tracks.
- Reviewer -> `subagent_type:"code-reviewer"`.
- CI failure investigation -> `subagent_type:"ci-investigator"` when focused.
- Designer, Judge -> `subagent_type:"generalPurpose"` with role in prompt.

## Cursor Task Parameters

- `readonly: true` -> Explorer, Judge, and Reviewer by default.
- `run_in_background: true` -> long Explorer or Worker tracks.
- `resume: <id>` -> continue the same Reviewer or Explorer.
- `resume: "self"` -> full-history fork on Cursor.
- `subagent_type: "best-of-n-runner"` -> parallel Worker experiments.

## Cursor Model Mapping

- `cheap-fast` -> `composer-2.5-fast`.
- `balanced` -> `gpt-5.5-medium` when listed.
- `coding` -> `gpt-5.5-medium` when listed.
- `frontier` -> `claude-opus-4-7-thinking-high`.
- `inherited` -> omit `model`.

## Claude Code Mapping

Claude Code subagents are user-defined under `~/.claude/agents/`.

- Explorer -> `subagent_type:"explore"` if defined, else `general-purpose`.
- Worker -> `subagent_type:"general-purpose"` or user-defined `worker`.
- Reviewer -> `subagent_type:"code-reviewer"` if defined, else `general-purpose`.
- Designer, Judge -> `subagent_type:"general-purpose"` with role in prompt.

## Claude Code Task Parameters

- `subagent_type` -> agent name in `~/.claude/agents/`, `.claude/agents/`, or
  `general-purpose`.
- `description` -> short user-visible label.
- `prompt` -> full task prompt with Native Fields, Owned Scope, and Required
  Output Schema.
- Model and tool allowlist live on the agent definition, not per `Task` call.

## Claude Code Model Mapping

- `cheap-fast` -> `claude-haiku`.
- `balanced` -> `claude-sonnet`.
- `coding` -> `claude-sonnet` or inherited from a strong coding parent.
- `frontier` -> `claude-opus`.
- `inherited` -> omit `model` in agent frontmatter.
