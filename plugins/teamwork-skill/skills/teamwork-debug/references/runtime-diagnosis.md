# Runtime Diagnosis

Load this reference only when existing evidence cannot distinguish the leading
runtime hypotheses and the fixed dispatch authority permits instrumentation. Do
not load another reference or Skill.

## Frozen Probe Contract

Before adding a probe, freeze the failure signature and one active experiment:

```text
Experiment E-*
- Competing hypotheses: H-* vs H-*
- Probe location:
- If H-* is true, observe:
- If H-* is false, observe:
- Result that would remain inconclusive:
- Cleanup obligation:
- Authority:
```

Choose the smallest reversible observation at the nearest owned boundary.
Change one variable at a time. Do not add broad tracing, production exposure,
sensitive-value logging, or a probe that changes the behavior being measured.
Do not start a second experiment while the first lacks a result.

If the next observation requires a human-only UI, credential, device, or remote
state, pause with the exact action and expected observation. Resume the same
diagnosis from the returned value; do not restart or infer it.

After each probe, record the raw observation and update each named hypothesis to
`supported`, `weakened`, or `rejected`. An inconclusive result does not justify
a fix, a Review verdict, broader tracing, or a target change. Select a different
discriminator or stop `blocked`.

Remove every temporary probe, flag, log, fixture, and generated trace before
completion, including on a blocked path when safe. Under `fix` authority only,
apply the narrow causal fix and rerun the original failure path. Under `observe`
or `instrument`, stop at the supported diagnosis and do not mutate product
behavior.
