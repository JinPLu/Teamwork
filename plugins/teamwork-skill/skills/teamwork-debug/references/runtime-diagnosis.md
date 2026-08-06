# Runtime Diagnosis

Use this method when an unknown runtime, state, data-flow, event-flow,
asynchronous, or UI failure needs a temporary probe and the operating boundary
permits instrumentation.

Choose the smallest probe at the nearest owned boundary that distinguishes the
live causal explanations. Prefer an existing trace, debugger, metric, event
inspection, or narrowly scoped observation. Structured logging is one option,
not a default; use it only when the chosen fields separate the alternatives.

Before changing anything, state the probe location, what each material outcome
would mean, what would remain inconclusive, sensitive data to exclude, cleanup
needed, and the current authority. Change as little as possible and preserve the
raw observation before interpreting it.

Use the result to update the causal picture and choose the next discriminator.
An inconclusive observation does not justify a fix, broader tracing, or a target
change. Return the exact missing evidence when no deciding probe is available.

Remove temporary probes, flags, fixtures, logs, and generated traces before
returning whenever safe. Under fix authority only, apply the supported narrow
correction and rerun the original failure path. Under observe or instrument
authority, do not change product behavior.
