# Subagent Contract

Use only after `subagent-dispatch.md` decides delegation has net value. The
parent owns scope, integration, user questions, and final acceptance.

## Prompt

Every delegated prompt contains four fields:

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
defaults or masking them with fallbacks.

Lifecycle verdicts are `accept | revise | blocked`. Reserve `rejected` for a
hypothesis, option, source, or data item and include the reason.

## Base Result

Return the smallest result that preserves the parent's decision evidence:

```text
Role:
Status or Verdict:
Result:
Evidence / Verification:
Files Changed: <paths | none>
Risks / Blockers:
Next: <parent decision, follow-up evidence, or none>
```

## Conditional Role Fields

- **Explorer:** question, sources/files read, direct findings, material
  inference, confidence, dissent, and coverage gap. Add a source census or
  citation ledger only for broad/deep research.
- **Designer:** decision, decision rule, real alternatives and tradeoffs, open
  user-owned decisions.
- **Judge:** plan source, evidence/scope/verification adequacy, acceptance gap,
  and smallest required fixes.
- **Worker:** owned scope, implemented change, focused verification, deviations,
  protected-boundary hits, and blocker. Add repro, root-cause, TDD, or cleanup
  evidence only when that protocol was used.
- **Reviewer:** review target, requirements/evidence map, actionable findings
  with severity, verification reviewed, and residual risk.

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
