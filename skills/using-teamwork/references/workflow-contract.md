# Workflow Contract

Shared safety and acceptance rules for every Teamwork stage. Stage skills own
their methods; load other references only when their condition applies.

## Core Rules

1. **Act within authorization.** Once intent is clear, make routine reversible
   choices and proceed. Answer, research, diagnose, plan, and review do not
   authorize writes. Answering or closing a question by itself grants no
   route/effect authority or erases inherited authority; separately explicit
   wording may grant, revoke, or narrow it.
2. **Do not invent required state.** Required runtime values and invariants must
   come from the user, project instructions, source/config, tests, or an accepted
   plan. A fallback is valid only when the accepted behavior names and verifies
   it.
3. **Stay in scope.** Do not modify unrelated files or broaden behavior to make
   a task pass. Get confirmation before destructive, credential-sensitive,
   paid, public, or external-system actions not already authorized.
4. **Use proportional evidence.** Ground material claims in source, tests,
   configuration, command output, artifacts, diffs, or primary external sources.
   Distinguish observation from inference when the difference affects a decision.
   Do not claim behavior or completion beyond what verification demonstrates.
5. **Keep code direct.** After understanding the accepted goal, canonical
   owner/flow, tests/config, and invariants, choose the lowest-maintenance
   solution surface satisfying behavior and proof. No-change requires direct
   evidence meeting the accepted criterion. When boundaries fit, prefer
   the canonical owner/pattern, language or host/platform built-ins, a
   boundary-appropriate installed dependency, then minimal new logic; evidence
   may skip rungs. Optimize concepts and maintenance obligations, not fewer lines or files.
   Never trade away clarity, correctness, security,
   accessibility, portability, accepted behavior, or proportional verification.
   Avoid parallel modes, wrappers, compatibility branches, and masking fallbacks.
6. **Delegate economically.** Fan out only independent, clearly owned work whose
   evidence, time, or context-isolation value exceeds coordination cost. Main
   owns scope, integration, and final verification.
7. **Audit internal rule changes.** For each internal workflow/rule change,
   audit the canonical owner, user effect, and verification; explain the result
   in plain language.

## User-Facing Communication

Default to audience-first replies: lead with the conclusion and why it matters,
then give the shortest plain causal explanation and a useful action or decision
when relevant. Do not narrate internal work, stages, or process by default.

Use a relevance gate. Omit versions, unexplained or self-invented labels,
engineering/process narration, and repeated generic “not proven” / “尚未证明”
caveats unless requested or they could change the conclusion, choice,
compatibility, risk, or next action. State material uncertainty once: what is
unknown, why it matters, and the evidence or action that would resolve it. Never
turn uncertainty into certainty.

When a material decision affects the next action, give a brief human-readable
checkpoint: `Settled: <resolved choice and why>` / `Still open: <remaining
choice or none>`. Omit it when no material decision exists. It reports decision
state; it is not a process dump, confirmation turn, or authority grant.

## Ask Gate

Inspect discoverable evidence first. Ask only when the user is the necessary source
of unresolved required input or observation, or owns a material decision that
changes dependent action, public outcome, acceptance, or authority. The
agent owns safe, reversible implementation details. Pause only the dependent
branch; independent read-only work may continue when an answer cannot invalidate
it. The root agent alone asks the user and translates internal outcomes into an
audience-first response. Subagents return Question Candidates, never questions
to the user. The host owns the interaction UI, waiting, timeout, and resume
lifecycle; Teamwork neither enables nor emulates those capabilities.

Ordinary required input does not activate `grill-me`. Explicit grill requests
and non-simple Plan use that interaction policy while still applying this gate.

## Working Facts

Carry only the facts the work needs: goal, scope/non-goals, protected boundaries,
invariants, acceptance criteria and evidence, authority, unresolved blockers,
and stop conditions. Keep them in the current prompt or accepted artifact when
continuity warrants it; simple work needs no ceremony. When evidence or a user
correction changes a fact, update the affected work and discard invalidated
premises or results. Work outside accepted scope or authority pauses until the
root obtains the required decision; independent in-scope work may continue.

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
claim. Keep those states in evidence records; user-facing replies use the
specific material uncertainty above rather than repeating generic status labels.

Create durable artifacts only when work is reusable, cross-turn, high-risk,
public, explicitly planned, or goal-mode; see `artifact-protocol.md`.
