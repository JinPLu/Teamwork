# Routing Policy

Use when stage choice is ambiguous, or when a user describes symptoms instead of
Teamwork stage names. Route from intent, evidence state, and risk.

## Natural Signals

| User signal | Route | Why |
|---|---|---|
| "What is this?", "where is X?", tiny edit, obvious local fix | native | Direct answer or low-risk edit needs no Teamwork ceremony. |
| "Why?", "which option?", "is this current?", unfamiliar API, unclear repro surface | research | Source of truth, facts, or scope need evidence before action. |
| Failing test, flaky run, CI failure, runtime log, UI symptom, regression, crash | debug | A real or likely repro can decide root cause. |
| "Design", "plan", cross-file behavior, public contract, architecture, risky refactor | plan | Scope, acceptance, verification, or dispatch must be locked before edits. |
| "Go ahead", "implement the plan", "continue", accepted checklist | execute | Scope is accepted; work is implementation and verification. |
| "Review", "check this diff", "did we miss anything?", strict quality, deslop | review | Acceptance, issues, or maintainability need read-only scrutiny. |
| "Keep going", "until green", "iterate until done", explicit budget | goal | The user wants autonomous convergence with stop rules. |
| "Set up Teamwork", AGENTS/CODEX/CURSOR/CLAUDE, migrate rules | init | Project instruction and install readiness work. |
| "Update Teamwork", version, release, refresh installed skills | update | Package/install surface maintenance. |
| "Grill me", "grill-me", "question-first", "stress-test", "challenge my assumptions", "ask before acting", "先问清楚" | grill mode | Interaction override before normal route selection; see `grill-mode.md`. |

## Tie-Breakers

- Symptom with unknown cause and runnable evidence beats plan/execute: route
  debug before speculative fixes.
- Unknown source of truth, dependency behavior, or repro surface beats debug:
  route research until the surface is clear enough to test.
- Known root cause plus non-trivial or protected fix beats execute: route plan.
- Known root cause plus accepted narrow fix routes execute; tiny obvious fixes
  may stay native.
- "Do not fix yet" means research, debug, or review only.
- "Do not grill", "act normally", or "just implement" disables grill mode unless
  normal required-state rules still ask or block.
- User does not need to say `teamwork-debug`, `teamwork-plan`, or any stage
  name. Stage names are internal handles and optional force switches.

## Smart Defaults

Act directly when evidence is enough. For uncertain, complex, or non-lightweight
tasks, ask before planning or acting when a decision/risk answer could change
scope, acceptance, public behavior, architecture, risk, verification, or an
irreversible action. Never invent runtime targets, model names, ports, data, or
credentials to force a stage to proceed.
Explicit grill mode is stricter: ask one decision/risk question with a
recommendation, then stop before planning or acting unless the user exits or
already confirmed a Shared Understanding Packet.
