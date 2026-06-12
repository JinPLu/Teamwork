# Subagent Packets

Specify delegated subagent output or material dispatch. Local native-flow work
does not need packet formatting unless a durable artifact, goal loop, delegated
track, public contract, or required acceptance gate needs it. Ask for
`Memory Delta Candidate` only when work may change durable memory.

## Result Packets

Explorer Result Packet:
```text
Role: Explorer
Native Fields:
Question:
Files / Commands Read:
Research Fields when web/deep research: Search Plan; Queries Tried; Source Classes; Source Census when broad; Sources Used; Sources Rejected; Contradictions; Coverage Gaps; Citation Ledger
Artifact Pointer / Evidence Store:
Observed:
Inferred:
Claimed:
Confidence:
Dissent / Risks:
Open Questions:
Clarification Relevance:
Decision Relevance:
Suggested Next Step:
```

Broad Explorer packets cap `Sources Used`, `Observed`, and `Citation Ledger` to
the requested budget, default max 8 each. Put source census, matrices, ledgers,
and raw notes in the artifact pointer; report omissions as Coverage Gaps.

Designer Decision Packet:
```text
Role: Designer
Native Fields:
Decision Scope:
Constraints:
Success Criteria:
Decision:
Decision Rule:
Option Matrix:
Rejected Options:
Recommendation:
Plan Decomposition Notes:
Acceptance Implications:
Evidence Used:
Risks / Dissent:
Protected Boundaries:
Open Questions:
Clarification Relevance:
```

Judge Plan Review Packet:
```text
Role: Judge
Native Fields:
Verdict: accept | revise | blocked
Plan Source:
Requirements Mapping Adequacy:
Assumption Safety:
Evidence Adequacy:
Protected Boundary Adequacy:
Plan Completeness:
Routing Adequacy:
Verification Adequacy:
Guardrails / Stop Conditions:
Stop Rule Adequacy:
Acceptance Gap:
Clarification Gap:
Required Fixes:
Verdict Rationale:
Residual Risks:
```

Worker Completion Packet:
```text
Role: Worker
Native Fields:
Status: done | done_with_concerns | blocked | needs_context
Plan Source:
Owned Scope:
Plan Step Mapping:
Files Changed:
Implemented:
Mode: behavior_change | bug_failure | mechanical | planned_implementation
TDD Evidence: not_applicable | red_seen | red_green_refactor | impractical_with_reason
Failing Test / Repro Evidence:
Root Cause Evidence: not_applicable | summarized
Hypothesis Tested:
Verification Commands:
Verification Result: pass | fail | partial | not_run
Claim Supported By Evidence: yes | no
Review Loop Status: not_applicable | pending | spec_passed | quality_passed | final_reviewed
Deviations:
Protected Boundary Hits:
Concerns / Blockers:
Open Questions:
```

Reviewer Verdict Packet:
```text
Role: Reviewer
Native Fields:
Verdict: accept | revise | blocked
Review Target:
Base/Head or Diff Source:
Requirements / Evidence Map:
Acceptance Mapping:
Requirement Misses:
Clarification Gap:
Issues:
Severity Crosswalk: blocker | major | minor
Feedback / Thread Disposition:
Verification Reviewed:
CI / Log Provenance:
Manual Smoke Evidence:
Routing Conformance:
Re-review Status:
Pushback / Dissent:
Residual Risk:
Next Route:
```

Optional durable-memory fields:
```text
Memory Delta Candidate: none | current | plan | research | decision | supersede | compact | deferred
Memory Delta Evidence:
Protected Data Status: clear | redacted | blocked | not_checked
```

Subagents propose memory candidates only. They do not promote external memory,
docs graph output, or recall into canonical Teamwork artifacts.

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
