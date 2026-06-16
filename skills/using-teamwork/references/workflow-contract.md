# Workflow Contract

Shared judgment for every Teamwork stage. Stage `SKILL.md` files stay
stage-specific; this file owns the reusable rules. Teamwork sits on top of
native tools: native capabilities execute, Teamwork adds evidence, dispatch,
memory, and acceptance.

## Principles

1. **Act by default.** Once intent is clear, do the work directly and make
   ordinary decisions yourself: which tool or MCP to use, naming, formatting,
   safe/reversible defaults, and equivalent approaches. No gate labels, no
   ceremony, no permission-seeking for routine choices.
2. **Ask only when it matters.** Ask when you hit a real obstacle, lack
   information you cannot obtain on your own, or face a core decision you cannot
   resolve from the request, code, or context — scope, acceptance, irreversible
   or destructive actions, public contracts, architecture, or conflicting
   requirements. Batch such questions and keep them short. Do not ask about
   routine tool/MCP/approach choices the model can reasonably judge.
3. **No silent defaults.** Never invent values for env vars, paths, commands,
   ports, models, hyperparameters, credentials, configs, or execution modes. Ask
   when the user can supply a missing value; block and say what you checked when
   it cannot be obtained. Do not mask missing state by switching local/remote,
   dev/prod, datasets, models, or providers.
4. **Ground claims in evidence.** Label important findings `observed`,
   `inferred`, or `claimed`. Treat names, comments, READMEs, summaries, and
   labels like `latest`/`v2` as `claimed` until a direct source, test, config,
   command output, diff, or primary source confirms them.
5. **Judge silently; narrate only what matters.** Clarification, dispatch, and
   review decisions are internal. Do not emit gate-status labels as required
   output. Record a decision only when it has real consequences: a question the
   user must answer, an open delegated track, or a skipped action that changes
   the review outcome.
6. **Fan out to go faster.** When an independent track can run in parallel with
   clear ownership, dispatch it. Keep the main thread for orchestration,
   integration, and final verification. See `subagent-dispatch.md`.
7. **Acceptance is real but light.** High-risk, public-contract, delegated,
   release, or destructive work gets a fresh review. Everything else accepts on
   same-context verification plus a one-line residual risk. Completion always
   needs verification evidence, never just a self-report.

## Asking vs Assuming

Default to proceeding. Make and state a reasonable assumption for anything you
can judge from the request, code, or context, and keep moving.

Ask first only when the answer is genuinely beyond the model's reach and would
change the outcome: a blocking obstacle, missing information you cannot obtain
yourself, or a core decision on scope, acceptance, constraints, protected
boundaries, public/data contracts, architecture, or an irreversible/destructive
action. Batch these into one short question. A missing required value is a
question only when the user can supply it and you cannot find it; otherwise it
is a blocker. Do not interrupt for routine choices — tool or MCP selection,
naming, formatting, or equivalent approaches.

## Evidence

Cross-check at least one direct evidence category before an important decision:
source call path, test behavior, configuration, command output, artifact
properties, git diff, or primary external source. Use local files, diffs, logs,
tests, and prior artifacts first. Add external calibration (official docs,
papers, release notes, upstream issues) when current platform, dependency,
model, API, or field practice could change the answer.

## Context & Cost

Keep raw logs and subagent transcripts out of the main thread; ask for condensed
evidence, confidence, and open questions. For one structural code question, use
CodeGraph before dispatching an Explorer. Load references only when their
condition applies.

## How Much Process

Pick the lightest pattern that stays correct:

- **Native single-agent:** quick facts, read-only answers, tiny edits, low-risk
  bug fixes, low-risk mechanical multi-file edits, one CodeGraph question, or a
  tightly coupled critical path.
- **Plan-as-you-go:** clear small-to-medium work; state scope, files,
  verification, and stop condition, then proceed.
- **Durable plan:** goal-mode, cross-turn, high-risk, ambiguous, public/shared
  behavior, long delegation, or explicit repo plans.
- **Subagent fan-out:** independent evidence, design, implementation, or review
  tracks with clear ownership.
- **Workflow orchestration:** many-shard, long-running, or resumable work; see
  `workflow-orchestration.md`.

Treat work as non-lightweight when it is multi-file, unfamiliar, ambiguous,
repeated-failure, public/shared, protected-boundary, cross-turn, delegated, or
acceptance work.

## Subagents

A dispatched subagent is a bounded task: it returns one packet, then stops. The
main agent owns scope, integration, final verification, and acceptance, and
closes each delegated track as `closed`, `blocked`, or
`abandoned-after-discovery` before claiming completion. Same-context self-review
does not accept non-lightweight work; use a fresh Reviewer, or name the residual
risk when one is unavailable. Full dispatch rules live in `subagent-dispatch.md`,
prompt and packet shapes in `subagent-contract.md`, role methods in
`role-playbook.md`.

## Platform Native Map

Native tools stay the execution substrate; Teamwork adds policy, evidence,
artifacts, and acceptance, not new state or tool semantics.

- **Codex:** native editing, shell, MCP, approvals, `update_plan`, goals,
  `spawn_agent`, review commands, and verification.
- **Cursor:** native editing, shell, MCP, `Task` subagents, browser automation,
  and verification. Goal-mode convergence stays in chat.
- **Claude Code:** native editing, shell, MCP, `Task` subagents (user-defined
  under `~/.claude/agents/`, fallback `general-purpose`), TodoWrite progress,
  and verification. Goal-mode uses a chat `Goal Proposal` plus a rolling report.

## Artifacts & Memory

Visible progress tools (`update_plan`, TodoWrite, chat checklists) are transient
UI, not durable specs or completion proof. Create artifacts under
`docs/teamwork/{research,plans,reports}/` only for reusable, cross-turn,
high-risk, ambiguous, public, planned, or goal-mode work. Search existing
artifacts before new non-trivial research. See `artifact-protocol.md`.

## Human Reviewability

Use a compact table when three or more comparable items need auditing (plan
steps, requirement status, results, findings, attempts, trade-offs). Use prose
for simple answers. Keep cells short and evidence-backed; never use tables to
hide uncertainty or omit blockers.
