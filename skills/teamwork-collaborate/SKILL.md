---
name: teamwork-collaborate
description: Use when the user explicitly wants to discuss, brainstorm, compare options, or make a material preference decision, or when unclear intent needs guided clarification; do not use for clear execution or a single discoverable detail.
---

# Teamwork Collaborate

Root owns the conversation. Keep clear work native and activate Collaborate when
the user wants to think together, when an unresolved preference would materially
change the result, or when unclear intent needs guided clarification.

## Method

1. State the final goal, what is already settled, and the criteria that matter.
   Start from facts, constraints, and the goal. Name the strongest prior work on
   this question: what it already solved and where it stalls. Do not invent a
   stack from zero. Map the discussion from goal to stage to questions with a
   concise tree or list; use Mermaid when the option space needs that structure.
2. A stage is one dependency layer of user-owned decisions. Ask every
   independent, valuable question for that stage together and defer dependents
   later; host UI limits are not Teamwork limits.
3. Develop only meaningfully different options. For each, explain the main
   benefit, cost, assumption, and consequence. Answer three axes, or mark a weak
   axis: relative to priors, is this a new mechanism or packaging; whose pain
   gets lighter; is it a real hard problem for the domain. Practice first:
   unobserved local results are not done. Tests on disk are not verification.
4. Resolve facts directly. Ask the user only for preferences or authority that
   cannot be discovered. Use subagents only for bounded evidence gathering or a
   genuinely independent challenge. Use Explorer when available; otherwise use
   native local search. A handoff contains the objective, owned scope, settled
   user constraints, available evidence, and requested return. Settled user
   constraints must include recorded rejections and decisions, and the requested
   return must not change the topic. No fixed role or dispatch count is
   required, and an unavailable optional subagent does not block the discussion.
5. When this turn involves experiment scheduling, GPU or other scarce compute, or
   a paper / contribution table slot, follow `references/experiment.md`.
   Otherwise skip Experiment.
6. Recommend a direction when the evidence supports one. Lead with the claim,
   then checkable behavior. Define a new term in one sentence. No slogans; do
   not paper over holes with coinages. Record the user's decision and advance to
   the next dependent stage. Recorded rejections and decisions are the mainline;
   research or a subagent return must not restate them as a new question. After
   research, do not rewrite the question. Quote the user's decision or
   rejection; do not paraphrase it into a new problem. A fluent next step is not
   convergence. If a new direction is weak on the three axes, improve the
   anchored problem instead of reopening it.
7. End with the decision, unresolved points, and the next authorized action.
   Persist the checkpoint under Persistence before closeout; a host plan or
   question UI does not complete it. The next turn on the same subject reads the
   discussion document's current synthesis first when that document exists. If
   the document is missing, session recall may be used and must be marked as not
   persisted.

## Persistence

Cross-chat memory lives in one Markdown document from `references/discussion.md`
at `docs/teamwork/discussions/<YYYY-MM-DD>-<slug>.md`. Same identity means the
same final goal plus the same subject; reuse that path and name the document you
read. A different subject gets a new path.

Checkpoints: the turn ends with a question batch, recommendation, decision, or
next action that must survive the session. Keep user quotes separate from the
working understanding.

Prefer Writer, a helper role with its own writing contract, not a Skill. If
Writer is unavailable or returns a no-write, Root writes the same template to
the same path and marks Root fallback in the closeout. Primary discussion never
blocks on Writer; silently skipping a fired checkpoint is a Skill violation.
