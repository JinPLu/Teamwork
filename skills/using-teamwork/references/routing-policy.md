# Routing Policy

Use only when the next Teamwork stage is unclear. Route from user intent and the
missing evidence or decision; a clear task goes directly to its stage or native
execution.

## Natural Signals

| User signal | Route | Why |
|---|---|---|
| "What is this?", "where is X?", tiny edit, obvious local fix | native | Direct answer or low-risk edit needs no Teamwork ceremony. |
| "Why?", "which option?", "is this current?", unfamiliar API, unclear repro surface | research | Source of truth, facts, or scope need evidence before action. |
| Failing test, flaky run, CI failure, runtime log, UI symptom, regression, crash | debug | A real or likely repro can decide root cause. |
| "Design", "plan", public contract, architecture, risky refactor | plan | Scope, acceptance, verification, or dispatch must be locked before edits. |
| "Go ahead", "implement the plan", "continue", accepted checklist | execute | Scope is accepted; work is implementation and verification. |
| "Review", "check this diff", "did we miss anything?", strict quality, deslop | review | Acceptance, issues, or maintainability need read-only scrutiny. |
| "Keep going", "until green", "iterate until done", explicit budget | goal | The user wants autonomous convergence with stop rules. |
| "Set up Teamwork", AGENTS/CODEX/CURSOR/CLAUDE, migrate rules | init | Project instruction and install readiness work. |
| "Update Teamwork", version, release, refresh installed skills | update | Package/install surface maintenance. |

## Tie-Breakers

- Symptom with unknown cause and runnable evidence beats plan/execute: route
  debug before speculative fixes.
- Unknown source of truth, dependency behavior, or repro surface beats debug:
  route research until the surface is clear enough to test.
- Known root cause plus a public/protected or decision-heavy fix routes plan.
- Known root cause plus accepted narrow fix routes execute; tiny obvious fixes
  may stay native.
- "Do not fix yet" means research, debug, or review only.
- Explicit stage names are force switches unless they conflict with the user's
  requested action boundary.

## Smart Defaults

Act when evidence and authorization are enough. Ask only if a remaining user
decision could materially change scope, acceptance, public behavior, risk, or
an irreversible action. Missing facts route to research or debug when they are
discoverable; required user-owned values ask or block under the workflow
contract. Public interaction skills are selected before this stage policy.
