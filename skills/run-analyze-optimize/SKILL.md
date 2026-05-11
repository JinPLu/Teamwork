---
name: run-analyze-optimize
description: >-
  Run a command or workflow, observe real evidence, diagnose root causes, and
  iteratively improve implementation details while preserving protected
  principles and architecture. Use for autonomous run -> analyze -> optimize
  loops with minimal surgical edits, verification, and independent review.
disable-model-invocation: true
---

# Run-Analyze-Optimize

Lightweight self-iteration for coding agents. Given a command, workflow, or
artifact target, run it, read the evidence, diagnose the root cause, make the
smallest safe implementation change, verify, and review. Continue until the
target is reached or a real blocker is found.

This skill combines:

- **Karpathy guardrails**: think before coding, simplicity first, surgical
  changes, goal-driven execution.
- **Roundtable-lite discipline**: evidence first, role separation, independent
  review, dissent preservation, budgeted convergence.

It does **not** require agent-roundtable infrastructure, model registries,
dispatch ledgers, pricing caches, or multiple `SKILL.md` copies.

## Use When

- A command/test/generation run fails and can be rerun.
- A pipeline must produce verifiable artifacts.
- Prompts, parsers, schema validation, retry logic, thresholds, or error
  handling need evidence-driven iteration.
- The user wants autonomous convergence with clear stop conditions.

Do not use for open-ended product design, narrative decisions, UI taste
judgment, or work with no verifiable target.

## Operating Contract

- Work in English during the loop. Final reports may use the user's language.
- Do not ask mid-loop unless credentials, destructive action, external cost, or
  ambiguous product intent blocks safe progress.
- Preserve the sacred boundary: principles, architecture, public contracts, and
  user-stated constraints are protected.
- Change only mutable implementation details needed for the observed root cause.
- Prefer the smallest fix at the producer of the failure, not downstream cleanup.
- Before claiming success, verify with real command output or artifact evidence
  and run a distinct review pass.

## Inputs

The user may provide:

1. **Command**: what to run.
2. **Expected artifacts**: files, metrics, logs, UI state, or success criteria.
3. **Sacred boundary**: what must not change.
4. **Budget**: max iterations, wall time, token/cost ceiling, or stop signal.

If an input is missing, infer it from repository context and state the
assumption before iteration 1.

## Workflow

```text
Initialize boundary
  -> Run command
  -> Observe logs/tests/artifacts
  -> Diagnose root cause
  -> Plan minimal change
  -> Worker pass
  -> Verify
  -> Independent review
  -> Decide: success / continue / blocked / budget exhausted
```

### 1. Initialize

Before running or editing, identify:

- Exact command and working directory.
- Expected artifacts and verification method.
- Relevant logs, output directories, tests, entry points, and project guidance.
- Sacred boundary and mutable optimization scope.
- Budget and stop rules.

Default budget when unspecified:

- Max 3 optimization iterations.
- Stop after 2 consecutive iterations with no evidence delta.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing credentials, or unavailable required external resources.

Present a concise summary:

```text
Sacred Boundary:
- Principles: ...
- Design/contracts: ...

Expected Artifacts:
- ...

Optimization Scope:
- ...

Budget:
- ...

Entering iteration 1.
```

### 2. Run and Monitor

Run the command with the platform's shell tool. For long-running commands, keep
the session id or pid and poll output/logs/artifacts.

Suggested cadence:

- First check: about 15 seconds.
- Early checks: 20-30 seconds.
- Stable progress: 45-60 seconds.
- Never exceed 120 seconds between checks.

Kill or stop a run only on clear waste signals:

| Signal | Examples |
|---|---|
| Crash | traceback, unhandled exception, assertion failure |
| Irrecoverable API failure | auth error, model not found, exhausted retries |
| Resource exhaustion | OOM, disk full, container crash |
| Poisoned state | malformed output passed to a later stage |
| No progress | repeated identical error, no output/artifact movement after bounded stall |
| Wrong phase | command runs a stage that should have been skipped |

Do not kill only because output is slow. Confirm with logs or artifact movement.

### 3. Observe

Collect evidence before explaining or editing:

- Exit code and terminal output.
- Relevant log excerpts.
- Generated artifacts and their properties.
- Suspect source locations.
- Delta against the previous iteration.

Classify each symptom:

- **Fixed**: verified by artifact or test.
- **Improved**: measurable progress remains incomplete.
- **Unchanged**: same failure, no meaningful delta.
- **Regressed**: new failure introduced by the last change.
- **New**: unrelated symptom surfaced.

### 4. Diagnose

Trace each unresolved symptom to the producing mechanism. Classify the fix path:

- **Optimizable**: implementation detail; proceed.
- **Sacred**: would change protected principle/design/contract; log blocker.
- **Ambiguous**: try only if a safe implementation-level fix exists; otherwise
  log blocker.

Use independent subagents when symptoms are separable or a second view reduces
risk. Subagent prompts must be self-contained: include evidence, paths, sacred
boundary, and requested return format.

### 5. Karpathy Gate

Before editing, pass all four checks:

| Check | Question |
|---|---|
| Think before coding | Are assumptions and ambiguity explicit? |
| Simplicity first | Is this the minimum code that solves the observed problem? |
| Surgical changes | Does every changed line trace to the target? |
| Goal-driven execution | What command or artifact proves success? |

If a simpler approach exists, say so and use it. If the goal is ambiguous in a
way that affects behavior, stop and ask instead of guessing.

### 6. Plan

Write a precise modification plan before editing:

```text
Root cause:
- <one sentence with file/function if known>

Fix:
1. <file/module> - <minimal change> - targets <root cause>

Verification:
- <focused command/check>
- <broader command/check if warranted>

Risk:
- <regression risk and mitigation>
```

Reject plans that rely on downstream cleanup when the producer can be fixed.
Reject broad refactors unless they are required by the root cause.

### 7. Worker Pass

Implement exactly the approved plan:

- Touch only necessary files.
- Match existing style.
- Do not improve adjacent code, comments, or formatting.
- Do not delete pre-existing dead code unless asked.
- Remove only imports/variables/functions made unused by your own change.
- If regression appears, revert or rework only the causal change.

Use a separate worker subagent when the platform supports it and the task is
well scoped. Otherwise run an explicit worker pass in the parent agent.

### 8. Verify

Run focused verification first. Add broader validation when shared behavior,
public contracts, or user-facing workflows are affected.

Verification requires actual command output or artifact properties. "Looks
good" is not evidence.

If verification fails, capture the failure, compare it with the prior
iteration, and continue only with a new hypothesis or measurable progress.

### 9. Review

Before completion, run a distinct review pass:

- Read the diff and relevant source directly.
- Re-check expected artifacts and verification evidence.
- Look for regressions, scope creep, missing coverage, brittle assumptions, and
  downstream cleanup masking a producer bug.
- Preserve dissent from independent reviewers even if it does not block.

Use the strongest available reviewer model for final review. Use a cheaper
independent reviewer for blind dissent on high-risk work.

### 10. Decide

Continue only when:

- Expected artifacts are missing and there is a concrete optimizable root cause.
- Verification improved but has not reached target.
- Review found a fixable regression.

Exit when:

- Expected artifacts are produced, verified, and review passes.
- Budget is exhausted.
- Two consecutive iterations show no evidence delta.
- Only sacred or unresolvable blockers remain.
- The user stops the loop.

## Optional Journal

For non-trivial loops, create:

```text
.run-analyze-optimize/<timestamp>-<slug>/
  RUN.md
  ITERATIONS.md
  BLOCKERS.md
```

For small one-iteration fixes, an in-chat summary plus the repository diff is
enough. Do not create files merely for ceremony.

## Logical Roles

These are roles, not separate subskills:

| Role | Purpose |
|---|---|
| Triage | Summarize logs/artifacts and list distinct symptoms |
| Diagnostician | Trace root cause and classify fix path |
| Planner | Produce minimal implementation plan |
| Worker | Edit code according to the approved plan |
| Reviewer | Independently review diff, evidence, and residual risk |
| Cheap dissent | Optional second review for missed edge cases |

Suggested local aliases:

| Role | Alias |
|---|---|
| Final reviewer | `opus` |
| Planner / worker | `sonnet` |
| Triage / cheap dissent | `haiku` |

Treat these as local model aliases. Verify current availability and pricing from
the user's configured toolchain before making cost or benchmark claims.

## Blocker Format

```markdown
## Iteration <N> - <timestamp>

### <issue title>
- Type: Sacred | Ambiguous | Unresolvable
- Location: <file:line or command/artifact>
- Description: <what happened>
- Why blocked: <why it cannot be resolved autonomously>
- Agent judgment: <what you would do if permitted>
```

## Final Report

Report once on loop exit:

```text
Boundary:
- Sacred Boundary: untouched / blocked at <issue>

Artifacts:
- <artifact>: produced / missing - <verification evidence>

Changes:
- Iteration 1: <files changed and why>
- Iteration 2: ...

Verification:
- <commands and key results>

Review:
- <verdict, dissent, residual risk>

Unresolved:
- <blockers or none>

Conclusion:
- accept / blocked / budget exhausted / stopped
```

## Anti-Patterns

| Trap | Correct approach |
|---|---|
| Adding full roundtable infrastructure | Use roundtable-lite roles and evidence discipline |
| Optimizing before reading evidence | Observe first, then diagnose |
| Fixing bad output with downstream cleanup | Fix the producer when possible |
| Retrying without a changed hypothesis | Diagnose or stop |
| Broad refactor for a narrow failure | Minimal origin-level change |
| Reviewer trusts worker summary | Reviewer reads source and evidence directly |
| Continuing after no progress | Stop at the configured stall budget |
