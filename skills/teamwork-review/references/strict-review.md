# Strict Review

Load this reference only for a named release, security, permission, data,
destructive-risk, public-contract, or similarly accepted strict gate. Do not load
another reference or Skill.

Freeze the exact candidate, threat or failure boundary, acceptance criteria,
protected invariants, direct evidence, and explicitly accepted fallbacks. Review
correctness first: authorization, data flow, failure behavior, compatibility,
regression, and the real-path proof required by the gate. Then apply the normal
changed-scope cohesion and residue lens without widening into unrelated debt.

For each stable `R-*` finding, state the violated criterion, direct evidence,
user or system impact, and smallest correction route. Missing required access or
evidence yields `BLOCKED`; a plausible but unobserved concern is not proof. A
second independent reviewer may cover a separable high-risk lens only when the
gate requires it; the root owner deduplicates findings. Reviewers remain
read-only and never accept the overall task on the implementer's behalf.
