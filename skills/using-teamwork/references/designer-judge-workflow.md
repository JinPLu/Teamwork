# Designer And Judge Workflow

Use for ambiguous design, plan synthesis, or plan adequacy review. This owns
Teamwork's compact Design Synthesis, Planning Synthesis, Parallel Dispatch, and
Skill Authoring gates.

## Designer

Designer owns decision quality, not implementation acceptance.

1. Frame: restate Decision Scope, constraints, success criteria, protected
   boundaries, and current evidence.
2. Compare: give 2-3 viable options unless evidence leaves only one. Use an
   option matrix: tradeoffs, risks, verification impact, routing impact.
3. Choose: state the decision rule, recommendation, rejected options, and the
   reason rejected options lost.
4. Decompose: name plan slices, file or component boundaries, independent
   tracks, and expected proof for each slice.
5. Escalate: mark open questions when public behavior, data contracts,
   security, unfamiliar APIs, or user intent are not evidence-grounded.

Do not copy full external design scripts into prompts. Load this reference only
when a design choice is real.

## Judge

Judge owns plan adequacy before execution, not architecture invention.

Return `accept` only when the plan is runnable, scoped, and testable. Return
`revise` when the plan can be fixed. Return `blocked` when missing evidence,
credentials, authorization, or protected-boundary conflict prevents a safe
plan.

Check:

- requirements map to observed evidence or explicit verification;
- assumptions are safe or called out;
- scope and protected boundaries are preserved;
- no placeholders, ellipses, vague tasks, or hidden broad refactors remain;
- routing economics, prompt packets, ownership, and output schema are adequate;
- expected output, guardrails, retry/stop conditions, and escalation triggers
  are explicit;
- verification commands or artifact checks include expected results;
- acceptance gap is stated with required fixes and residual risk.

Judge may suggest the smallest correction needed for `revise`; do not replace
Designer by redesigning the whole path.
