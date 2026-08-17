# Experiment (condition-gated)

Enable this reference only when the current Collaborate turn involves experiment
scheduling, GPU or other scarce compute reservation, or a paper / contribution
table slot. Skip it for ordinary preference discussion.

Before running any experiment or applying for / occupying scarce compute,
write the intended slot so the user can check it at any time:

> **This experiment feeds which contribution slot: main table / appendix hygiene /
> exploratory probe / unused.**

"Unused" must not take large-scale scarce compute. Uncertain slot = unused.

| Slot | Criterion |
| --- | --- |
| Main table | Controllable, repeatable evidence with independent ground truth for the claim the paper would assert; or a fixed-consumer ranking / false-release / regret metric the reader can audit |
| Appendix hygiene | Contract calibration, unit / coordinate / timing cleanup. Short and cheap; a gate, not a contribution |
| Exploratory probe | Mechanism smoke: small scale + same-budget control + explicit kill; state "mechanism not selected; measuring headroom only" |

Hard rules when this gate is active:

- Do not treat observational logs without controllable counterfactual ground
  truth as main-table evidence; use them for appearance, distribution, or
  qualitative failure buckets only.
- Do not reopen a settled mainline because something "runs." Unfrozen mechanism
  work stays out of training or large-scale runs until agreed gates pass.
- Cross-domain or cross-embodiment mismatch results stay exploratory; they do
  not count as repeatable gap evidence for a settled claim.

Stop conditions (hit any, stop; do not force the story through):

1. A contract or instrumentation error already explains the anomaly → withdraw
   that case as model-failure evidence.
2. On controllable paired setups, a strong baseline already crosses the claimed
   critical boundary → the problem does not hold; stop.
3. A simple same-budget baseline (state / rule / retrieval / critic) ties the
   proposed system → do not claim the proposed system is irreplaceable.
