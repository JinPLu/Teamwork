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
3. Run the smallest observation that distinguishes the live alternatives.
4. Locate the first bad owned boundary and state the supported cause.
5. If the user authorized a fix, make the smallest complete repair and verify the
   same failing path. Remove temporary instrumentation.
6. If evidence reveals a different failure, split it explicitly instead of
   silently changing scope.

A Debugger or Explorer subagent may help when parallel evidence gathering is
useful. Give it the objective, failing scope, current constraints, observations,
and expected return. Their availability is not a readiness gate: Root may
continue the same method with available tools.

Do not guess a fix or retain temporary diagnostics.

When a durable diagnosis is useful or requested, Root may ask Writer to
maintain one Markdown document per stable failure signature from
`references/debug.md`. Every wake-up supplies the document
kind and path, failure-signature identity, authoritative diagnosis owner,
owner-certified semantic delta, read-only context, and expected base. Writer
only compresses literally, locates, deduplicates the current synthesis and
pending delta, updates the current synthesis, and appends dated history.
Existing history is immutable. It cannot reinterpret an observation,
change hypothesis standing, confirm a cause, authorize a fix, claim
verification or completion, or alter authority, next action, or mainline.
Missing state or a conflicting base produces a no-write exact gap. Writer
unavailability or conflict does not block diagnosis or repair; if the document
was explicitly requested, only its delivery remains incomplete.
