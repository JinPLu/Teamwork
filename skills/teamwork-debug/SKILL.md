---
name: teamwork-debug
description: Use when a failure, regression, crash, flake, or unexpected result has an unknown cause that must be diagnosed before a safe fix; do not use when the cause and narrow fix are already clear.
---

# Teamwork Debug

Diagnose from the observed failure, not from a preset ceremony.
Read `references/runtime-diagnosis.md` for the detailed evidence and document
semantics.

## Method

1. Reproduce or directly inspect the failure and bound the first bad behavior.
2. Form only hypotheses supported by evidence. One hypothesis is enough when a
   direct observation isolates the cause.
3. Run the smallest observation that distinguishes the live alternatives. For a
   runtime unknown, use structured logging first when it is that discriminator;
   keep non-runtime or already-isolated failures probe-minimal.
4. Locate the first bad owned boundary and state the supported cause.
5. If the user authorized a fix, make the smallest complete repair and verify the
   same failing path. Remove temporary instrumentation.
6. If evidence reveals a different failure, split it explicitly instead of
   silently changing scope.

freeze observe, instrument, and fix permission in any diagnosis brief.
Diagnosis must not silently expand repair authority.

Do not guess a fix or retain temporary diagnostics.

## Persistence

When a listed checkpoint fires, write in the same response cycle. If separate
stable identities each cross a checkpoint, write each to its own path.

Cross-chat memory lives in one Markdown document from `references/debug.md`
at `docs/teamwork/debug/<slug>.md`. Same identity means the same
failure signature; reuse that path and name the document you read. A different
subject gets a new path.

Checkpoints: a cause is confirmed; an authorized fix is verified on the same
path; the case is blocked with a durable next discriminator; or evidence splits
a new failure with its own identity.
