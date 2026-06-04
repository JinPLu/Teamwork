# Subagent Packets

Specify subagent output or dispatch. Ask for `Memory Delta Candidate` only when work may change durable memory.

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
Decision Relevance:
Suggested Next Step:
```

Designer Decision Packet:

```text
Role: Designer
Native Fields:
Decision Scope:
Decision:
Decision Rule:
Options:
Rejected Options:
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
Stop Rule Adequacy:
Acceptance Gap:
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
Protected Boundary Hits:
Concerns / Blockers:
```

Reviewer Verdict Packet:

```text
Role: Reviewer
Native Fields:
Verdict: accept | revise | blocked
Review Target:
Acceptance Mapping:
Requirement Misses:
Issues:
Verification Reviewed:
Manual Smoke Evidence:
Routing Conformance:
Residual Risk:
Next Route:
```

Optional durable-memory fields:
```text
Memory Delta Candidate: none | current | plan | research | decision | supersede | compact | deferred
Memory Delta Evidence:
```

## Actual Dispatch Log
Record review-relevant dispatch. Final status cannot remain `dispatched` or
`returned`.

```text
Actual Dispatch Log:
- Role:
  Native Fields:
  Context Strategy:
  Ownership:
  Prompt Packet:
  Returned Packet:
  Status: dispatched | returned | closed | blocked | abandoned-after-discovery
  Closure Evidence: <packet integrated | blocker reported | discovery failed>
```
