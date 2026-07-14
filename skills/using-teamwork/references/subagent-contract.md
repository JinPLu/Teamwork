# Subagent Contract

Use only after `subagent-dispatch.md` decides delegation has net value. The
parent owns scope, integration, user questions, and final acceptance. Subagents
never interact with the user or operate an interaction lifecycle.
All prompt, result, question-candidate, and dispatch shapes in this reference are
internal coordination records, not mandatory user-facing packets.

## Prompt

Every delegated prompt covers four facts, in any compact form:

```text
Mission:     one question, decision, owned slice, or review
Owned Scope: files/components to inspect or edit, plus protected boundaries
Verify:      command, artifact, behavior, or checklist that supports the result
Stop:        return one result and stop; the parent integrates and accepts
```

The prompt is one self-contained packet: include the relevant facts and source
paths instead of relying on inherited history. Add role, mode, or output details
only when they change the work. Subagents do not expand scope, clean up
unrelated code, chain more agents, accept the overall task, or continue after
return. They report missing execution-critical values instead of inventing
defaults or masking them with fallbacks. A sole recheck exception may reuse the
same initial Judge/Reviewer thread once, with its prior finding IDs, claimed
fixes, and new direct evidence; it must inspect no unrelated surface, delegate
nothing, and return again immediately.

Lifecycle verdicts are `accept | revise | blocked`. Reserve `rejected` for a
hypothesis, option, source, or data item and include the reason.

## Question Candidate

When work encounters a possible Ask Gate trigger, do not ask. Return this compact
candidate to the parent, which decides whether the root should ask and lets the
host own UI, wait, timeout, and resume:

```text
Question Candidate:
- Checked: <evidence/config/source already inspected>
- Remaining unknown: <required input, observation, or decision>
- Why user-owned/required: <why the agent cannot own or discover it>
- Consequence: <dependent action, public outcome, acceptance, or authority>
- Recommendation: <evidence-backed choice or requested observation>
- Blocked branch: <only the dependent work>
```

## Base Result

Return the smallest internal result that preserves the parent's decision evidence:

```text
Role:
Status or Verdict:
Conclusion:
Direct Evidence:
Unresolved Impact: <none, or unknown and why it changes the work>
Next Action:
Files Changed: <paths | none>
```

The parent uses this internal record to integrate the work. The root translates
it into an audience-first response for people; do not expose the packet or its
labels unless the user asks for them.

## Conditional Role Fields

- **Explorer:** question, sources/files read, direct findings, material
  inference, confidence, dissent, and coverage gap. Add a source census or
  citation ledger only for broad/deep research.
- **Designer:** decision, decision rule, real alternatives and tradeoffs, and
  any Question Candidate.
- **Judge:** plan source, evidence/scope/verification adequacy, acceptance gap,
  and smallest required fixes.
- **Worker:** owned scope, acceptance-criterion change/evidence map, verification
  proportional to the changed surface and risk, discovery classification (`regression`,
  `accepted_scope_violation`, `pre_existing`, `out_of_scope`, or `suggestion`), deviations,
  protected-boundary hits, and blocker. Add repro, root-cause, TDD, or cleanup
  evidence only when that protocol was used.
- **Reviewer:** review target, fresh/recheck status, requirements/evidence map,
  stable-ID actionable findings classified `BLOCKER`, `FOLLOW-UP`, or
  `SUGGESTION`, verification reviewed, and residual risk.
  `ACCEPT` requires no open `BLOCKER`; follow-ups do not block acceptance. A
  recheck covers proportional regression risk, while materially expanded scope
  receives a fresh review.

For goal retries, add Goal Invariants, prior failed evidence, strategy delta,
drift, and retry/stop verdict. For durable-memory work, subagents may propose a
`Memory Delta Candidate`; only the parent promotes memory.

## Dispatch Record

Record only review-relevant delegation outcomes:

```text
- Role / ownership: <role and scope>
  Status: returned | blocked | skipped_after_discovery
  Result or blocker: <compact evidence-backed summary>
```
