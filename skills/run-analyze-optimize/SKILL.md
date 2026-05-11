---
name: run-analyze-optimize
description: >-
  Router for run-analyze-optimize workflows. Dispatch to research, planning,
  execution, review, or autonomous goal convergence subskills based on the
  user's intent while preserving evidence-first, minimal-change discipline.
disable-model-invocation: true
---

# Run-Analyze-Optimize Router

This is the router skill for the run-analyze-optimize package. Use it to choose
the workflow-matched subskill instead of forcing every request through one
monolithic loop.

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
| Research options, compare approaches, discuss tradeoffs, gather evidence | `run-analyze-research` | `skills/run-analyze-research/SKILL.md` |
| Convert a chosen direction into an executable implementation plan | `run-analyze-plan` | `skills/run-analyze-plan/SKILL.md` |
| Execute an accepted plan with minimal edits and verification | `run-analyze-execute` | `skills/run-analyze-execute/SKILL.md` |
| plan-review: review a plan before execution | `run-analyze-review` with `mode: plan` | `skills/run-analyze-review/SKILL.md` |
| execution-review: review diffs, artifacts, tests, and results after execution | `run-analyze-review` with `mode: execution` | `skills/run-analyze-review/SKILL.md` |
| Iterate autonomously until verified success, budget exhaustion, or blocker | `run-analyze-goal` | `skills/run-analyze-goal/SKILL.md` |

Do not create separate plan-review and execution-review subskills. The single
`run-analyze-review` subskill has two explicit modes so reviewer orchestration
stays shared while the rubric changes by review target.

## Routing Rules

Use the narrowest subskill that satisfies the request:

- If the user asks "what should we do?", "research", "compare", "discuss", or
  "find options", route to `run-analyze-research`.
- If the user asks for a plan, route to `run-analyze-plan`.
- If the user gives an accepted plan or says to implement/execute, route to
  `run-analyze-execute`.
- If the user asks to review a proposed plan, route to
  `run-analyze-review` with `mode: plan`.
- If the user asks to review a diff, patch, artifacts, test result, or completed
  execution, route to `run-analyze-review` with `mode: execution`.
- If the user asks to "run until it passes", "iterate until convergence",
  "keep going until done", or gives a verifiable target plus budget, route to
  `run-analyze-goal`.

When intent spans multiple stages, use the controller:

```text
research/discuss if needed
  -> plan
  -> review plan
  -> execute
  -> review execution
  -> accept / continue / re-plan / block
```

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

## Output

After routing, report the selected subskill and why:

```text
Route: run-analyze-<stage>
Reason: <one sentence tied to user intent>
Mode: <plan | execution, only for run-analyze-review>
```

Then follow that subskill's instructions directly.
