# Strict Review

Load this reference only for an explicitly named release, security, permission,
data, destructive-risk, public-contract, or comparable high-consequence gate.

Freeze the candidate identity, protected boundary, acceptance criteria, direct
evidence, threat or failure model, and explicitly accepted fallbacks. Review in
this order:

1. authorization and permission boundaries;
2. data flow, destructive behavior, and failure handling;
3. public contracts, compatibility, migration, and rollback;
4. real-path proof and regression evidence; and
5. changed-scope cohesion and temporary residue.

For each finding, state the failed criterion, direct evidence, impact, and
smallest correction route. Missing required access or evidence yields
`BLOCKED`; a plausible but unobserved concern is not proof. Add independent
reviewers only for separable risk lenses where independence materially improves
the gate, and deduplicate their findings under one review owner.

Reviewer stays read-only. Return the supported verdict, unresolved findings,
residual risk, evidence gaps, and the exact proof needed to close the gate.
