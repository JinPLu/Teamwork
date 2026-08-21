---
status: active
superseded-by:
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
declared-slot:
adjudicated-slot:
---

# Experiment: <claim draft>

## Declaration

Frozen once written. Do not edit this section after the first save.

### Probe (minimum to run)

A probe may run with only these three fields. The full declaration below is
required for main-table or appendix-hygiene eligibility, not for running.

- Claim draft: <one falsifiable sentence>
- Kill criterion: <when to stop the matching claim or scale-up>
- Budget: <compute / time / money>

### Full declaration (main-table / appendix-hygiene)

- Falsifiable claim: <one sentence>
- Declared slot: <main table / appendix hygiene / exploratory probe / unused>
- Primary metric: <formula over valid outputs; include parse rules>
- Decision threshold: <pass / fail rule>
- Kill criterion: <stop the matching claim or scale-up>
- Outcome-neutral checks: <pre-result instrumentation and sanity>
- Budget: <compute / time / money>
- Config:
  - Model IDs / checkpoint hashes: <ids>
  - Seeds: <seeds>
  - Hyperparameter search range and selection method: <range and rule>
  - Exact reproduce command: <command>

## Adjudication

Fill after the run. Reviewer or Challenger is the right role for this
adjudication; it is not a mandatory ceremony.

HARKing detector: diff the frozen declared claim against any post-hoc claim.

Registered Reports Stage 2:

1. Can the observed data test the frozen declared claim?
2. Is the reported claim the same as the frozen declaration (no silent shift)?
3. Were the declared procedures, metric, and parse rules followed, with
   deviations labelled?
4. Are any unregistered analyses labelled exploratory rather than confirmatory?
5. Is the conclusion licensed by the declared claim and the observed result,
   including a negative or killed outcome?

Mayo severity: If this claim were false, would this experiment probably have
shown it?

- Adjudicated slot: <main table / appendix hygiene / exploratory probe / unused / tombstone>
- Rationale: <why this slot, including any demotion>

Demotion needs no permission. Promotion to main table requires all five Stage 2
questions passing.

## Result / tombstone

- Numbers with error-bar provenance (std vs SEM, and the variability source):
  <values>
- Run IDs: <ids>
- Reproduce command: <command>
- If killed: which assumption broke, and revisit conditions: <or none>

## History

<Append only. Never rewrite or remove; a correction is a new dated entry.>

### <date/time — semantic change>

<declaration freeze, adjudication, result, or tombstone delta>
