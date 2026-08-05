# Strict Adversarial Search

Use this method only when the user explicitly requests strict adversarial
search, independent critics, or a comparable stress test. Root owns the search,
the user dialogue, and the recommendation. Challenger supplies isolated
critique; it never decides, plans, implements, persists, or accepts the result.

## Freeze The Search

Record the decision question, non-negotiable requirements, weighted preferences,
evidence, empirical gates, primary comparison axis, and a bounded search
envelope. Choose the envelope from the stakes and available host capacity; do
not apply a universal trial or agent count. State the planned coverage and the
limits before dispatch.

Build a map of materially distinct hypotheses. Exclude a hypothesis without a
trial only when direct evidence proves that it violates a non-negotiable
requirement. Record the evidence. Preference loss or intuition is not enough.

## Challenge The Candidates

For each hypothesis admitted by the envelope:

1. Give a fresh Challenger only the frozen decision criteria, that hypothesis,
   relevant direct evidence, and protected boundaries. Do not leak another
   critic's verdict or an expected answer.
2. Ask for `survives` or `fails`, the strongest objection, hidden assumptions,
   verdict-changing evidence, and confidence.
3. Update the coverage map. A materially revised hypothesis becomes a new
   hypothesis and consumes additional search capacity; a relabel or summary
   does not.

Use distinct Challenger contexts for critiques that are claimed to be
independent. If the required isolation or identity cannot be established,
report that limit and do not claim an independent result.

## Audit Closure

Before convergence, give a fresh Challenger that did not critique the selected
candidate the frozen criteria, coverage map, survivor, strongest comparator,
evidenced exclusions, and open empirical gaps. Ask for `PASS` or `FAIL`, the
largest coverage gap, strongest-comparator status, required qualification, and
confidence.

Converge only when the audit passes and no known material hypothesis inside the
declared envelope remains untested. Otherwise report the precise state:
coverage incomplete, audit failed, independence unavailable, evidence missing,
or search envelope exhausted. Never expand the envelope silently or describe a
partial search as exhaustive.

Return the leading candidate and strongest downside first, followed by tested
hypotheses, exclusions and evidence, dissent, empirical gaps, audit result, and
coverage limits. The result informs the user's choice; it does not make it.
