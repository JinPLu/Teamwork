# Subagent Contract

Prompt structure and packet schemas for dispatched subagents.
Dispatch decisions and platform fields → `subagent-dispatch.md`.

## Prompt

Every delegated prompt contains four fields:

```text
Mission:     one question, decision, slice, or review
Owned Scope: files and components to inspect or edit
Verify:      command, artifact, behavior, or checklist proving completion
Stop:        return packet once, then stop; orchestrator owns integration and final acceptance
```

Role Card (include when platform requires): Conceptual Role (Explorer|Designer|Judge|Worker|Reviewer); Native Fields per `subagent-dispatch.md`; Mode (read-only|workspace-write|review-only); Context Strategy (condensed-evidence-only|artifact-backed|owned-files-only|fresh-context-review|full-history-fork).

Forbidden always: scope expansion, unrelated cleanup, chaining subagents, final acceptance, monitoring after packet. Block on missing env/path/command/model/config/credentials/invariants; report, never invent defaults or mask them with fallbacks.

Lifecycle verdicts are `accept | revise | blocked`; `reject` is not a lifecycle verdict. Use rejected only for hypotheses, options, sources, memory candidates, or data buckets, with a reason.

## Packets

### Explorer Result Packet
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
Web/deep extras: Seed Expansion; Perspective Map; Search Plan; Queries Tried; Source Census; Sources Used; Sources Rejected; Coverage Audit; Citation Ledger. Cap each at 8; overflow → artifact pointer.

### Designer Decision Packet
```text
Role: Designer
Native Fields:
Decision Scope:
Decision:
Decision Rule:
Option Matrix:
Rejected Options:
Open Questions:
```

### Judge Plan Review Packet
```text
Role: Judge
Native Fields:
Verdict: accept | revise | blocked
Plan Source:
Evidence Adequacy:
Protected Boundary Adequacy:
Verification Adequacy:
Acceptance Gap:
Required Fixes:
Verdict Rationale:
```

### Worker Completion Packet
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
TDD Evidence:
Failing Test / Repro Evidence:
Root Cause Evidence:
Hypothesis Tested:
Instrumentation / Runtime Logs:
Verification Commands:
Verification Result: pass | fail | partial | not_run
Claim Supported By Evidence: yes | no
Review Loop Status: not_applicable | pending | spec_passed | quality_passed | final_reviewed
Deviations:
Protected Boundary Hits:
Concerns / Blockers:
Open Questions:
```

### Reviewer Verdict Packet
```text
Role: Reviewer
Native Fields:
Verdict: accept | revise | blocked
Review Target:
Base/Head or Diff Source:
Requirements / Evidence Map:
Issues:
Severity Crosswalk: blocker | major | minor
Verification Reviewed:
Manual Smoke Evidence:
Routing Conformance:
Residual Risk:
Next Route:
```

Optional memory fields (add when work may change durable memory):
```text
Memory Delta Candidate: none | current | plan | research | decision | supersede | compact | deferred
```
Subagents propose memory candidates only. They do not promote or recall into canonical Teamwork artifacts.

Optional goal-mode fields (add for goal-mode work or failed-goal recovery):
```text
Goal Anchor: Goal Text; Goal Invariants; active goal/report; Attempt Record source
Replay Preflight: done | not_applicable | blocked
Prior Attempts Reviewed:
Drift Verdict: on_goal | drifted | unclear
Retry Verdict: continue | replan | stop | blocked
```

## Closure
Each subagent must return one packet, then stop. Main agent records `Closure Evidence` in the Actual Dispatch Log after integrating each packet.
## Actual Dispatch Log
Record review-relevant dispatch. Progress: `dispatched -> returned -> closed`. Final status cannot remain `dispatched` or `returned`.

```text
Actual Dispatch Log:
- Role:
  Native Fields:
  Ownership:
  Status: dispatched | returned | closed | blocked | abandoned-after-discovery
  Closure Evidence: <packet integrated | blocker reported | discovery failed>
```
