# Workflow Contract

Shared judgment for every Teamwork stage. Stage `SKILL.md` files stay
stage-specific; this file owns the reusable rules. Teamwork sits on top of
native tools: native capabilities execute, Teamwork adds evidence, dispatch,
memory, and acceptance.

## Principles

1. **Act by default.** Once intent is clear, do the work directly and make
   ordinary decisions yourself: tool/MCP choice, naming, formatting,
   safe/reversible defaults, and equivalent approaches. No gate labels,
   ceremony, or permission-seeking for routine choices.
2. **Ask only when it matters.** Ask for real obstacles, unobtainable
   information, or core decisions not resolvable from request, code, or context:
   scope, acceptance, irreversible/destructive actions, public contracts,
   architecture, or conflicts. Batch questions. Do not ask about routine choices.
3. **Grill mode overrides act-by-default only when explicit.** For user requests
   to grill, question-first, stress-test, challenge assumptions, or ask before
   acting, follow `grill-mode.md`: ask one decision/risk question with a
   recommendation; do not plan or implement until the packet is confirmed or the
   user exits.
4. **No silent defaults or invariant-masking fallback.** Routine tool, naming,
   formatting, and reversible defaults are allowed; required code/runtime values
   and invariants are not. Never invent env vars, paths, commands, ports,
   models, hyperparameters, credentials, configs, execution modes, providers,
   datasets, schemas, or nullability. Ask for user-supplied gaps; otherwise
   block. Product fallback is allowed only when user input, source/config, tests,
   or an accepted plan names and verifies it.
5. **Maintain code by reducing concepts.** Before edits or review, understand
   owner, control flow, tests/config, and invariants. Change/delete current path;
   add branches/modes/wrappers/fallback only when accepted behavior requires and
   verifies them. Keep logic direct; fail fast when state is absent.
6. **Ground claims in evidence.** Label important findings `observed`,
   `inferred`, or `claimed`. Treat names, comments, READMEs, summaries, and
   labels like `latest`/`v2` as `claimed` until a direct source, test, config,
   command output, diff, or primary source confirms them.
7. **Think first; narrate only what matters.** Match reasoning depth to task
   risk. For non-trivial or evidence-sensitive work, read sources, compare
   plausible interpretations, and verify before final answers or edits. Keep
   narration brief: user decisions, blockers, material dispatch/review handoffs,
   evidence, or verification. Routine route choices need no gate labels;
   consequential dispatch, review, or skipped actions stay auditable.
8. **Fan out when it pays.** Dispatch only for non-lightweight work when an
   independent owned track has net evidence, time, or context-isolation value.
   Main owns orchestration, integration, and final verification. See
   `subagent-dispatch.md`.
9. **Acceptance is real but light.** High-risk, public-contract, delegated,
   release, or destructive work gets a fresh review. Everything else accepts on
   same-context verification plus a one-line residual risk. Completion always
   needs verification evidence, never just a self-report.

## Asking vs Assuming

Default to proceeding. Make and state a reasonable assumption for anything you
can judge from the request, code, or context, and keep moving.

Ask only when the answer is beyond the model's reach and would change the
outcome: a blocker, missing information, or a core decision on scope,
acceptance, constraints, protected boundaries, public/data contracts,
architecture, or irreversible/destructive action. Batch these into one short
question. Missing required values ask only when the user can supply them and you
cannot find them; otherwise block. Do not interrupt for routine choices.

## Evidence

Cross-check at least one direct evidence category before an important decision:
source call path, tests, configuration, command output, artifact properties,
git diff, or primary external source. Use local files, diffs, logs, tests, and
prior artifacts first. Add external calibration when current platform,
dependency, model, API, or field practice could change the answer.

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

A dispatched subagent is bounded: it returns one packet, then stops. Main owns
scope, integration, final verification, and acceptance. Main records returned
packets or blocker rationale for delegated tracks.
Same-context self-review does not accept non-lightweight work; use a fresh
Reviewer, or name residual risk when unavailable. Dispatch rules live in
`subagent-dispatch.md`, packet shapes in `subagent-contract.md`, role methods in
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

Use a compact table when three or more comparable items need auditing. Use
prose otherwise. Keep cells short and evidence-backed; never hide uncertainty
or blockers in tables.
