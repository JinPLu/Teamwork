---
name: run-analyze-optimize
description: Use when a request should enter an evidence-first run/analyze/optimize workflow, especially for research, planning, execution, review, or autonomous convergence.
---

# Run-Analyze-Optimize

This is the public entrypoint and goal controller for the package. Use it to
route a request to the narrowest stage skill, or to run a bounded autonomous
loop when the user asks for convergence.

The package preserves the original discipline:

- **Karpathy guardrails**: assumptions explicit, simplicity first, surgical
  edits, goal-driven verification.
- **Roundtable-style workflow**: role separation, multi-agent discussion when
  useful, independent review, dissent preservation, and budgeted stopping.
- **No full roundtable infrastructure**: do not import model registries,
  pricing caches, dispatch scripts, or thread ledgers unless the user asks.

## Route By Intent

| User intent | Route | Skill file |
|---|---|---|
| Research options, compare approaches, discuss tradeoffs, gather evidence | `run-analyze-design` with `mode: research` | `skills/run-analyze-design/SKILL.md` |
| Convert a chosen direction into an executable implementation plan | `run-analyze-design` with `mode: plan` | `skills/run-analyze-design/SKILL.md` |
| Execute an accepted plan with minimal edits and verification | `run-analyze-execute` | `skills/run-analyze-execute/SKILL.md` |
| plan-review: review a plan before execution | `run-analyze-review` with `mode: plan` | `skills/run-analyze-review/SKILL.md` |
| execution-review: review diffs, artifacts, tests, and results after execution | `run-analyze-review` with `mode: execution` | `skills/run-analyze-review/SKILL.md` |
| Iterate autonomously until verified success, budget exhaustion, or blocker | `run-analyze-optimize` with `mode: goal` | this skill |

Do not create separate plan-review and execution-review subskills. The single
`run-analyze-review` subskill has two explicit modes so reviewer orchestration
stays shared while the rubric changes by review target.

Do not create separate research, plan, or goal subskills. Research and planning
share `run-analyze-design` with hard mode boundaries; autonomous convergence is
the router's `mode: goal`.

## Routing Rules

Use the narrowest subskill that satisfies the request:

- If the user asks "what should we do?", "research", "compare", "discuss", or
  "find options", route to `run-analyze-design` with `mode: research`.
- If the user asks for a plan, route to `run-analyze-design` with `mode: plan`.
- If the user gives an accepted plan or says to implement/execute, route to
  `run-analyze-execute`.
- If the user asks to review a proposed plan, route to
  `run-analyze-review` with `mode: plan`.
- If the user asks to review a diff, patch, artifacts, test result, or completed
  execution, route to `run-analyze-review` with `mode: execution`.
- If the user asks to "run until it passes", "iterate until convergence",
  "keep going until done", or gives a verifiable target plus budget, stay in
  this skill and use `mode: goal`.

## Goal Mode

Use `mode: goal` only when the user gives a goal, command, artifact target, or
failure and wants autonomous progress to verified success or a clear stop.

Default budget when unspecified:

- Maximum 3 optimization iterations.
- Stop after 2 consecutive iterations with no evidence delta.
- Stop immediately on sacred-boundary conflict, destructive risk, auth failure,
  missing credentials, unavailable required resources, or ambiguous product
  intent that affects behavior.

Controller loop:

1. Initialize: state goal, assumptions, sacred boundaries, mutable scope,
   verification target, and budget.
2. Research/discuss only if causes or options are unclear: use
   `run-analyze-design` with `mode: research`.
3. Plan: use `run-analyze-design` with `mode: plan`.
4. Review the plan: use `run-analyze-review` with `mode: plan`; revise until
   pass or blocked.
5. Execute: use `run-analyze-execute` on the accepted plan.
6. Verify: run focused checks first and collect real evidence.
7. Review execution: use `run-analyze-review` with `mode: execution`.
8. Decide: accept only if verification and execution review pass; otherwise
   continue with a new hypothesis, stop at budget, or report a blocker.

Goal mode does not let one executor self-declare completion. Every completion
claim must pass execution review.

## Shared Contract

All subskills follow the same contract:

- State assumptions and sacred boundaries before committing to behavior.
- Read direct evidence: files, diffs, logs, tests, artifacts, or command output.
- Prefer the smallest producer-side fix over downstream cleanup.
- Keep mutable implementation details separate from protected principles,
  architecture, and public contracts.
- Use independent agents when subtasks are separable or a second view reduces
  risk; otherwise run distinct local passes.
- Preserve dissent in the final verdict instead of smoothing it away.
- Stop on verified success, budget exhaustion, repeated no-progress,
  unresolvable blocker, or sacred-boundary conflict.

## Route Output

After routing, report the selected subskill and why:

```text
Route: run-analyze-<stage>
Reason: <one sentence tied to user intent>
Mode: <research | plan | execution | goal, when applicable>
```

Then follow that subskill's instructions directly.

For `mode: goal`, end with:

```text
Goal:
- ...

Iterations:
- <n>: research/plan/execute/review summary

Verification:
- <command/artifact/check>: <result>

Review:
- Plan review: <verdict>
- Execution review: <verdict and dissent>

Unresolved:
- <none or blockers>

Conclusion:
- accept | blocked | budget exhausted | stopped
```
