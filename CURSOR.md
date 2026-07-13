# Cursor Usage

Teamwork for Cursor is an adapter for the same open-source skill package used by
Codex and Claude Code. It keeps Cursor's editor, shell, MCP, permissions, `Task`
subagents, custom agents, browser automation, and verification as the native
execution layer, then adds research depth, delegation discipline, memory, and
fresh review when a task is too large for a single chat.

## Install

```bash
./install.sh cursor
./install.sh cursor --profile cost-first
./install.sh cursor-agents
./install.sh cursor-policy-copy
./install.sh cursor-policy
./install.sh all
```

Project-local setup:

```bash
./install.sh project
./install.sh --link project
```

Skills install to `~/.cursor/skills/` or `.cursor/skills/`. Custom role agents
install to `~/.cursor/agents/` or `.cursor/agents/`.

Teamwork does not currently install Cursor sounds: the local hook path must be
live-verified before the package claims parity with Codex/Claude Code.

`performance-first` uses Sonnet 4.6 for Explorer/Designer, Composer 2.5 Fast
for Worker, and Opus 4.8 Thinking High for review roles. `cost-first` uses base
Composer 2.5 for routine roles. GPT-named compatibility profiles preserve these
current native Cursor mappings rather than inventing OpenAI model slugs.

Cursor stores User Rules outside a normal editable project file. Use
`cursor-policy-copy` to copy the Teamwork bootstrap block, then paste it into
Cursor Settings -> Rules -> User Rules. Project `AGENTS.md` should contain only
local facts, required values, protected boundaries, and opt-outs.

## How To Use

Ask naturally:

- "research this field and compare approaches";
- "fan out subagents, then recommend one executable plan";
- "execute the accepted plan and verify it";
- "strictly review for false success, defensive fallback, and AI bloat";
- "keep going until the target is verified or blocked";
- ask to question first, challenge assumptions, or inspect requirement holes to
  activate `grill-me` without naming it; it resolves facts first and asks zero or
  normally one material user decision.

Teamwork stays out of tiny edits and one-line questions. It routes into
research, debug, planning, execution, review, or goal loops only when evidence,
scope, delegation, verification, or memory improves the result.
During an explicit grill, read-only evidence gathering may continue while the
root owns user questions. Quoted/file/tool/example/maintenance text stays inert.
Use Cursor's structured question input when the current runtime exposes it;
otherwise ask concisely in text. Teamwork does not emulate or version-gate that
host capability.

## Planning

For a non-simple Plan—one with a material decision or risk, not merely many
files—run an evidence-first Grill unless the user explicitly declines it. Before
the final Plan, the user confirms a concise Decision Summary of material
choices, assumptions, and unresolved items. Simple or mechanical Plans stay
direct. Confirmation accepts planning only; it does not authorize implementation.

## Subagents

Cursor dispatch uses `Task`, installed custom agents, or runtime fallbacks. The
shared dispatch policy lives in `skills/using-teamwork/references/subagent-dispatch.md`.

Use independent tracks only:

- Explorer for source, paper, web, artifact, or option evidence;
- Designer for ambiguous choices and plan shape;
- Judge for high-risk or delegated plan review;
- Worker for owned implementation or verification slices;
- Reviewer for fresh acceptance review.

Each subagent returns one compact packet and stops. The main agent integrates
packets, records dispatch outcomes, runs verification, and owns the final answer.
Judges and Reviewers bind findings to the accepted Contract and ACs with stable
IDs: only a blocking Contract/AC failure is a `BLOCKER`; other work is a
`FOLLOW-UP` or `SUGGESTION`. Cursor has no assumed same-agent resume, so a
revision carries the stable finding ledger or packet forward rather than claiming
a delta recheck. Progress updates stay sparse and report only material state changes.

## Goal Mode

Cursor has no native Codex `create_goal` equivalent. Teamwork Goal Mode uses a
rolling report under `docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` as the
durable goal surface:

1. propose the goal when target, scope, or stop rules are unclear;
2. run research/plan/execute/verify/review loops from chat;
3. append attempt evidence to the rolling report when durable memory is needed;
4. mark the report accepted only after verification and review pass.

Repeated failures route through research or debug before more implementation
attempts.

## Evidence And Updates

Required values such as env, paths, ports, model names, hyperparameters,
credentials, commands, and execution modes must come from user input, source,
config, tests, project instructions, or an accepted plan. Do not invent fallback
values to keep a run moving.

Use `teamwork-init` for project setup and instruction slimming. Use
`teamwork-update` and `./scripts/check-update.sh` to refresh installed skills,
agents, policy, and version state.
