# Subagent Packets

Use when specifying subagent output or recording actual dispatch.

## Result Packets

Explorer Result Packet:

```text
Role: Explorer
Native Fields:
Question:
Files / Commands Read:
Observed:
Inferred:
Claimed:
Confidence:
Dissent / Risks:
Open Questions:
Suggested Next Step:
```

Designer Decision Packet:

```text
Role: Designer
Native Fields:
Decision:
Options:
Recommendation:
Evidence Used:
Risks / Dissent:
Protected Boundaries:
Open Questions:
```

Judge Plan Review Packet:

```text
Role: Judge
Native Fields:
Verdict: accept | revise | blocked
Plan Source:
Evidence Adequacy:
Routing Adequacy:
Verification Adequacy:
Required Fixes:
Residual Risks:
```

Worker Completion Packet:

```text
Role: Worker
Native Fields:
Status: done | done_with_concerns | blocked | needs_context
Plan Source:
Owned Scope:
Files Changed:
Implemented:
Verification:
Deviations:
Concerns / Blockers:
```

Reviewer Verdict Packet:

```text
Role: Reviewer
Native Fields:
Verdict: accept | revise | blocked
Review Target:
Acceptance Mapping:
Issues:
Verification Reviewed:
Routing Conformance:
Residual Risk:
Next Route:
```

## Actual Dispatch Log

Record when dispatch affects review:

```text
Actual Dispatch Log:
- Role:
  Native Fields:
  Context Strategy:
  Ownership:
  Prompt Packet:
  Returned Packet:
  Status:
```
