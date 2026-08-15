# Runtime Diagnosis

Anchor a diagnosis to one stable failure signature: the observable symptom,
triggering path, relevant environment or version, and the boundary where the
expected and observed behavior first diverge. State the success signal before
repair work.

Keep a current set of evidence-bearing hypotheses. Its size follows the live
alternatives, not a quota. Mark each hypothesis `live`, `supported`,
`weakened`, `rejected`, or `superseded`, and retain the discriminator or
observation responsible for every standing change. Distinguish three things:
the expected branch an observation was designed to discriminate, its raw
result, and the diagnosis owner's interpretation. A Writer may preserve those
statements but never supply the interpretation. For a runtime unknown, use
structured logging first when it is the smallest discriminating observation.
Keep non-runtime or already-isolated failures probe-minimal.

Confirm cause only after evidence distinguishes the meaningful alternatives
and locates the first bad boundary owned by the authorized scope. If a fix is
authorized, record the exact repair, verify the same failing path against the
success signal, and remove temporary probes. Locating a cause does not expand
repair authority. A different signature is a separate diagnosis document, even
when it appears during the same session.

The document holds a current synthesis plus dated semantic history. It is not a
transcript, probe dump, schema-backed case, or substitute for direct evidence.
