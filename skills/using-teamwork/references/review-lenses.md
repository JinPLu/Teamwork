# Review Lenses

Use when review needs strict maintainability, AI-code cleanup, or a diff
presentation optimized for human review. These lenses are gated: ordinary review
does not become opportunistic refactor.

## Deslop

Use for explicit deslop/AI-code cleanup requests, or touched-diff residue after
implementation/debugging. Preserve intended behavior and avoid unrelated files.

Remove aggressively when local style supports it:

- Comments that narrate obvious code or advertise implementation phases.
- Abnormal defensive checks, broad catches, silent defaults, or fallback paths
  that hide missing state.
- `any`, `unknown`, casts, loose shapes, or optionality used to dodge a clear
  type boundary.
- Deep nesting that can become early returns or a direct flow.
- Temporary flags, one-off booleans, duplicate helpers, wrappers with no reader
  value, console/debug logs, dead code, TODOs, and scaffolding.

Escalate to strict review instead of rewriting when cleanup would change
architecture, public behavior, contracts, or broad ownership.

## Strict Maintainability

Use when the user asks for strict/thermo review, acceptance finds structural
regression, or a diff is large/risky enough to deserve a maintainability pass.

Flag high-conviction issues:

- A simpler framing would delete branches, helpers, modes, or layers.
- Special cases, feature checks, or nullable modes spread through unrelated
  flows.
- A file crosses a healthy size boundary, especially near or above 1000 lines.
- Thin wrappers, magic generic handlers, duplicated helpers, or wrong-layer
  logic add reader load.
- Cast-heavy or fallback-heavy code hides the real invariant.
- Sequential orchestration or partial updates make independent work harder to
  reason about.

Prefer directions that reduce concepts, move logic to the canonical owner,
make boundaries explicit, or turn repeated corrections into lint, tests,
scripts, schemas, or runtime guards.

## Reviewer Comprehension

For PR walkthroughs or large diffs, present by reviewer value, not file order:
core logic first, wiring/integration next, mechanical or generated churn last.
For dense logic, add pseudocode or a concrete before/after trace only where it
helps expose behavior. Reserve callouts for subtle, breaking, race, perf, or
security risks.

## Multi-Lens Review

For high-risk diffs, consider parallel reviewers with separate lenses:
correctness/security and maintainability/deslop. Give both the same evidence,
then dedupe findings. Do not let maintainability review approve correctness, or
correctness review approve structural quality.
