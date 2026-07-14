# Review Lenses

Use when review needs strict maintainability, explicit minimality or over-engineering scrutiny, AI-code cleanup, or a human-reviewable diff. These
lenses are gated: ordinary review does not become opportunistic refactor. Review
identifies slop; cleanup belongs to execute/Worker only when requested or accepted.

Apply these lenses only to accepted scope and protected boundaries. Report an
unaccepted cleanup as `SUGGESTION` or `out_of_scope`, not as a reason to expand
the candidate. A real introduced structural or security regression remains a
`BLOCKER` with its stable finding ID and direct evidence.

## Deslop

Use for explicit deslop/AI-code cleanup requests, or touched-diff residue after
implementation/debugging. Preserve intended behavior, accepted fallbacks, and
unrelated files.

Remove aggressively when local style supports it:

- Comments that narrate obvious code or advertise implementation phases.
- Abnormal defensive checks, broad catches, silent defaults, or fallback paths
  that hide missing required state or invariants.
- New branches, modes, wrappers, or compatibility paths that duplicate the
  existing owner instead of simplifying the current flow.
- `any`, `unknown`, casts, loose shapes, or optionality used to dodge a clear
  type boundary.
- Deep nesting that can become early returns or a direct flow.
- Temporary flags, one-off booleans, duplicate helpers, wrappers with no reader
  value, console/debug logs, dead code, TODOs, and scaffolding.

Escalate to strict review instead of rewriting when cleanup would change
architecture, public behavior, contracts, accepted fallback behavior, or broad
ownership.

## Allowed Fail-Fast Checks

Keep guard clauses, schema/type checks, explicit preconditions, and intentional
product fallback when evidence names the invariant and tests or acceptance
verify behavior. Remove only defensive masking: branches, casts, nullable
defaults, catch-alls, aliases, or provider/target switches that continue after
required state is absent.

## Strict Maintainability

Use when the user asks for strict/thermo review, acceptance finds structural
regression, or a diff is large/risky enough to deserve a maintainability pass.

Flag high-conviction issues:

- A simpler framing would delete branches, helpers, modes, or layers.
- The diff bypasses the canonical owner/pattern or adds machinery before showing
  a suitable host/platform built-in or installed dependency is insufficient.
- Special cases, feature checks, or nullable modes spread through unrelated
  flows.
- A single-use abstraction, config, mode, or new dependency has no accepted
  behavior or boundary need.
- A file crosses a healthy size boundary, especially near or above 1000 lines.
- Thin wrappers, magic generic handlers, duplicated helpers, or wrong-layer
  logic add reader load.
- Cast-heavy or fallback-heavy code hides the real invariant.
- Guessed default values replace a required value that should come from user
  input, source/config, tests, or an accepted plan.
- Sequential orchestration or partial updates make independent work harder to
  reason about.

Prefer directions that reduce concepts, move logic to the canonical owner,
make boundaries explicit, or turn repeated corrections into lint, tests,
scripts, schemas, or runtime guards.
Do not score minimality by LOC or file count. Justified abstractions, dependencies,
and multi-file changes are not slop when they improve cost without weakening proof.

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
