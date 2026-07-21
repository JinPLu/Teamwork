# Adversarial Search

Use this advanced method when the owning Design selects it automatically or an
explicit adversarial override forces it. Root owns orchestration, reflection,
the live taxonomy/coverage ledger, and the final recommendation. Designer leaves
receive only a frozen challenge or audit; they never choose the global result,
ask the user, persist, plan, or implement.

## Freeze The Envelope

Show the goal, hard requirements, weighted preferences, empirical gates, primary
taxonomy axis, and maximum hypothesis-trial budget `B`. Accept a user override
only when `2 <= B <= 5`; reject an out-of-range override. If omitted, set
`B = 3`. The maximum adversarial
critic/auditor cost is `2B + 2` fresh dispatches: two per actual trial plus two
final auditors. Declare
any separately justified evidence wave and add it to the total envelope. State
the selected strategy, reason, and envelope before critic dispatch, but do not
request confirmation. Selection authorizes only read-only Design search, not
persistence, planning, implementation, or release.

## Search And Reflect

1. Map materially distinct cells on the frozen primary axis. Track tested,
   rejected, surviving, replaced, and known-untested cells. Exclude a material
   cell without a trial only when named direct evidence proves a frozen hard
   requirement violation; record that evidence for final audit. Preference loss,
   weak assumption, or Root inference cannot exclude it. If the initial map has
   more non-excluded material cells than `B`, report insufficient budget before
   dispatch; do not merge, demote, or silently skip cells to manufacture closure.
2. Trial one frozen hypothesis at a time. Every actual hypothesis gets exactly
   two fresh Designer critics in separate isolated leaf contexts. For Codex use
   separate `spawn_agent` calls with `fork_turns="none"`; for Cursor or Claude
   Code use separate native Task/subagent contexts. Record distinct returned
   identities/handles when exposed. If separate leaves cannot be created or
   distinguished, stop `capability-blocked`.
3. Give each critic only the frozen goal/fitness function, its hypothesis/cell,
   direct evidence, and protected boundaries—never another verdict, expected
   answer, or prior conclusion. Require `verdict: survives|fails`, strongest
   objection, hidden assumption, verdict-changing evidence, and confidence.
4. After both critics, Root retains, rejects, or revises and updates the ledger.
   A materially revised hypothesis is a new trial, consumes `B`, and gets two new
   critics. A rerun, relabel, summary, or echo is not fresh evidence. New cells
   may replace an untested queued cell within budget; never exceed `B` or mark an
   untested cell covered.

## Audit Closure

Request closure only when a candidate meets the fitness function and no known
material cell remains untested. Launch exactly two final Designer auditors who
joined no trial. Give each the frozen envelope, full ledger including evidenced
exclusions, survivor, strongest comparator, and empirical gaps, with no expected
verdict. Each independently returns `PASS|FAIL`, coverage gap,
strongest-comparator status, required qualification, and confidence.

Converge only when both final auditors return `PASS`. Adversarial failure states:
budget-exhausted | audit-failed | freshness-unproven | capability-blocked |
interrupted. Using the final unit of `B` is valid closure when the ledger is
complete and both audits pass; `budget-exhausted` applies only when another trial
or audit repair is still required. Any disagreement, missing/reused identity,
known coverage gap, interrupted leaf, unproven isolation, unavailable host
capability, or such budget exhaustion ends without durable Design. Report the
state and evidence; never add budget silently, downgrade strategies, reuse a
leaf, or call partial search success.

Closure is bounded, not exhaustive. Lead with the survivor and strongest
downside, then tested taxonomy, coverage limit, dissent, empirical gaps, and both
audits. If nothing survives, return the failed fitness gate. Chat closure remains
non-durable and cannot enter Plan until the owning skill's controlled acceptance
and persistence boundary succeeds; never store raw agent transcripts.
