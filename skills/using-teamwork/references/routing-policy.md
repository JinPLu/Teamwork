# Routing Policy

Use only when the next Teamwork stage is unclear. Route from user intent and the
missing evidence or decision; a clear task goes directly to its stage or native
execution.

## Natural Signals

| User signal | Route | Why |
|---|---|---|
| "What is this?", "where is X?", tiny edit, obvious local fix | native | Direct answer or low-risk edit needs no Teamwork ceremony. |
| "Why?", "which option?", "is this current?", unfamiliar API, unclear repro surface | research | Source of truth, facts, or scope need evidence before action. |
| Failure with unknown cause, flaky run, unclear CI/runtime symptom | debug | Only discriminating runtime evidence can choose a safe fix. |
| "Design", "plan", unresolved public choice, protected boundary | plan | A material choice or boundary must be settled before edits. |
| "Build", "fix", "change", "go ahead", "implement", "continue" | execute | The request authorizes direct result-producing work; a plan is optional. |
| "Review", "check this diff", "did we miss anything?" | review | The user requested a read-only verdict. |
| "Keep going", "until green", "iterate until done", explicit budget | goal | The user wants autonomous convergence with stop rules. |
| "Set up Teamwork", AGENTS/CODEX/CURSOR/CLAUDE, migrate rules | init | Project instruction and install readiness work. |
| "Update Teamwork", version, release, refresh installed skills | update | Package/install surface maintenance. |

## Tie-Breakers

- A supplied error with a clear narrow fix may execute directly; use Debug only
  while unknown cause blocks a safe change.
- Unknown source of truth, dependency behavior, or repro surface beats debug:
  route research until the surface is clear enough to test.
- Known root cause plus a public/protected or decision-heavy fix routes plan.
- Known root cause plus authorized narrow fix routes execute; clear fixes may
  stay native regardless of file count.
- "Do not fix yet" means research, debug, or review only.
- Explicit stage names select a method but do not replace or expand the user's
  requested action boundary.

## Smart Defaults

Act when evidence and authorization are enough. Missing facts route to research
or debug when they are discoverable; unresolved questions follow the Ask Gate
in `workflow-contract.md`. Public interaction skills are selected before this
stage policy.
