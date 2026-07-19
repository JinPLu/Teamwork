# Runtime Diagnosis

Load this reference only when existing evidence cannot distinguish the leading
runtime hypotheses and the fixed dispatch authority permits instrumentation. Do
not load another reference or Skill.

## Instrumented Loop

Freeze the real failure, environment, leading hypotheses, discriminating signal,
probe location, cleanup obligation, and authority before adding a probe. Choose
the smallest reversible observation at the nearest owned boundary. Change one
variable at a time and avoid broad tracing, production exposure, sensitive-value
logging, or a probe that changes the behavior being measured.

If the next observation requires a human-only UI, credential, device, or remote
state, pause with the exact action and expected observation. Resume the same
diagnosis from the returned value; do not restart or infer it.

Record the hypothesis each probe supports or rejects. Remove every temporary
probe, flag, log, fixture, and generated trace before completion, including on a
blocked path when safe. Under `fix` authority only, apply the narrow causal fix
and rerun the original failure path. Under `observe` or `instrument`, stop at the
supported diagnosis and do not mutate product behavior.
