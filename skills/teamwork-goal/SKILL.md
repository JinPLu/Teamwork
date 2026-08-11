---
name: teamwork-goal
description: Use when the user explicitly asks the host to persist until a verifiable result, fix until green, converge without stopping, monitor through completion, or stay within a stated budget; do not infer Goal from difficulty or use it for ordinary one-shot work.
---

# Teamwork Goal

Goal is Teamwork's only orthogonal persistence modifier. It is never the current
stage and does not own Research, Debug, Plan, Review, or another stage method.
While Goal remains active, Root keeps at most one current stage Skill active,
suspends it when a different method is needed, switches stages, waits for that
result, and resumes the appropriate stage. Goal never broadens scope or effect
authority.

## Establish

Record the objective, observable success signal, scope, protected boundaries,
available budget, and hard stops. Resolve discoverable facts before requesting
input. If the outcome or a material preference is unformed, Root first makes
Collaborate the current stage and resumes Goal-directed work after the decision.

## Persist

1. Observe the current unmet success signal or direct failure.
2. Choose the smallest evidence-backed next action and the one stage method that
   actually fits it.
3. Run the nearest real success path.
4. When it fails, use the new evidence to change the hypothesis, method, or
   strategy. Do not repeat an unchanged attempt.
5. Continue while an authorized, evidence-backed action remains and no budget
   or hard stop has been reached.

Complete only when the real success signal passes and protected boundaries
still hold. Stop with the exact observed state when the next action needs user
input, access, or authority; would cross a destructive, security, or scope
boundary; exceeds the budget; or no evidence-backed strategy remains.

Missing or broken required Teamwork capability is installation drift, not a
reason for Root to imitate a leaf role. Suspend the current stage, switch to
Update, wait for readiness repair, and then resume. If Update itself cannot
repair the capability or lacks authority, return that hard stop.

## Codex Role Dispatch

On Codex, dispatch Writer through `spawn_agent.agent_type` as
`teamwork_writer`. Use `fork_turns` set to `none` or a bounded recent context,
then observe a live child start; never silently substitute an unavailable role.

When context is omitted or bounded, the brief must include every still-applicable
settled user constraint. A child cannot infer that a missing constraint was relaxed.

## Goal Report

When the success signal, a material strategy change, a decisive result, or a
real blocker first becomes reusable, Root assigns Writer a typed Report with
kind Goal. Keep the objective, success signal, boundaries, current observed
state, decisive evidence, material strategy changes, budget or hard-stop state,
and remaining action. Do not record every attempt. Writer cannot declare
completion; only Root may do so from the observed success signal.

Lead the user-facing result with success evidence or the exact blocker and
remaining action.
