# Workflow Contract

Shared safety and acceptance rules for every Teamwork stage. Stage skills own
their methods; load other references only when their condition applies.

## Core Rules

1. **Act within authorization.** Once intent is clear, make routine reversible
   choices and proceed. Answer, research, diagnose, plan, and review do not
   authorize writes. Ask only when a remaining user decision could materially
   change scope, acceptance, public behavior, risk, or an irreversible action.
   Ordinary clarification never activates `grill-me`. Interaction transport is
   host-owned: use structured input when callable and concise text otherwise;
   Teamwork never enables or emulates a host capability.
   An explicit grill blocks only work dependent on an unresolved decision.
   Valuable read-only evidence gathering may continue when no answer can
   invalidate it; the root retains user-question ownership. Answering or closing
   by itself grants no route/effect authority or erases inherited authority;
   separately explicit wording may grant, revoke, or narrow it.
2. **Do not invent required state.** Required runtime values and invariants must
   come from the user, project instructions, source/config, tests, or an accepted
   plan. Inspect first; then ask when the user can supply the gap, otherwise
   block. A fallback is valid only when the accepted behavior names and verifies
   it.
3. **Stay in scope.** Do not modify unrelated files or broaden behavior to make
   a task pass. Get confirmation before destructive, credential-sensitive,
   paid, public, or external-system actions not already authorized.
4. **Use proportional evidence.** Ground material claims in source, tests,
   configuration, command output, artifacts, diffs, or primary external sources.
   Distinguish observation from inference when the difference affects a decision.
   Do not claim behavior or completion beyond what verification demonstrates.
5. **Keep code direct.** Before changing code, understand its owner, control
   flow, tests/config, and invariants. Prefer changing the existing path over a
   parallel mode, wrapper, compatibility branch, or masking fallback.
6. **Delegate economically.** Fan out only independent, clearly owned work whose
   evidence, time, or context-isolation value exceeds coordination cost. Main
   owns scope, integration, and final verification.

## Task Contract

For non-native Teamwork work, establish one task-level contract before the
first stage acts. Keep its Task Contract ID stable for the task and begin at
version `v1`; later stages inherit it rather than refreezing a stage card. Native
simple fast-path work needs no durable contract ceremony.

```text
Task Contract ID: stable task identifier
Version:        v1
Goal:           outcome to produce
Decision:       confirmed approach and material rejected alternatives
Scope:          owned surface, non-goals, and protected boundaries
Invariants:     behavior or constraints every stage must preserve
Acceptance:     stable AC IDs mapped to change, evidence, and verification
Truth identity: source/config/artifact version the work relies on
Authority:      permitted reads, writes, and external effects
Open blockers:  unresolved dependencies and affected actions
Replan:         evidence or Scope Delta that creates a new version
Stop:           completion, handoff, or blocker condition
```

Keep the contract in the current prompt or accepted artifact. A proposed action
outside it requires an explicit Scope Delta: new work, necessity, excluded
alternatives, cost/risk, changed acceptance evidence, and smallest next action.
Pause that action and obtain revised authority before proceeding, then issue the
same Task Contract ID at the next version. A user correction supersedes conflicting
premises and cancels any outstanding packet made invalid by it; integrate only
still-valid results.

## Risk Matrix

| Risk | Process | Acceptance |
|---|---|---|
| Low: clear, reversible, local; including mechanical multi-file work | Native or plan-as-you-go | Focused same-context verification |
| Medium: unfamiliar, ambiguous, repeated failure, or meaningful behavior change | Relevant Teamwork stage; plan or dispatch only when useful | Focused verification plus stated residual risk |
| High: public/shared contract, protected boundary, delegated writes, release, destructive action, or goal completion | Durable scope and explicit verification | Fresh-context review; report unavailable review as residual risk |

File count alone does not set risk. A tightly coupled critical path may stay
local; a one-file public-contract change may require planning and fresh review.

## Evidence and Completion

Use the closest direct evidence available and match check strength to the claim:
build-only proves buildability, not runtime behavior; a self-report proves
neither. External calibration is needed only when current platform, dependency,
model, API, or field behavior could have changed.

A dispatched subagent returns a bounded result; the main agent integrates it
and verifies the combined state. Same-context verification is sufficient for
low- and medium-risk work. Fresh review is required only for the high-risk row.

Evidence state is monotonic: keep `NOT VERIFIED`, failed, blocked, and
partial-tranche results visible until new direct evidence changes that exact claim.
Never upgrade them through synthesis, retry narration, or a broader completion
claim.

Create durable artifacts only when work is reusable, cross-turn, high-risk,
public, explicitly planned, or goal-mode; see `artifact-protocol.md`.
