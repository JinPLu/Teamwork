# Runtime Diagnosis

Load this reference only when an unknown runtime, state, data-flow, event-flow,
async, or UI failure needs a temporary probe and the current operating mode
permits instrumentation.

## Choose The Smallest Probe

Instrument the nearest owned boundary that distinguishes the active hypotheses.
Prefer an existing trace, debugger, metric, event inspection, or narrowly scoped
probe. Use a temporary structured log when its fields clearly separate the
leaders; it is optional rather than a universal first step.

Freeze the experiment before changing anything:

```text
Experiment E-*
- Competing hypotheses:
- Probe location:
- Observation predicted by each hypothesis:
- Inconclusive result:
- Sensitive fields to exclude:
- Cleanup obligation:
- Operating mode:
```

Change one variable at a time. Avoid broad tracing, production exposure,
sensitive-value logging, or probes that alter the behavior being measured. Do
not start another experiment before preserving the current result.

After the probe, record the raw observation and update the named hypotheses to
`supported`, `weakened`, or `rejected`. An inconclusive result does not justify
a fix, broader tracing, or a target change. Choose a different discriminator or
return `blocked` with the exact missing evidence.

Remove every temporary probe, flag, fixture, log, and generated trace before
completion, including on a blocked path when safe. Under `fix` only, apply the
narrow causal correction and rerun the original failure path. Under `observe`
or `instrument`, do not change product behavior.
