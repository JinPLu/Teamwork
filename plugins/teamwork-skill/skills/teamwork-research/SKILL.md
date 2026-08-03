---
name: teamwork-research
description: Use when a request or active workflow depends on external sources, including current web, API, library, platform, literature, market, or ecosystem facts, multi-source comparison, source verification, or citations; do not use for local repository/source/config/test/log/runtime/artifact inspection, supplied-text explanation, clear implementation, or unknown-cause debugging.
---

# Teamwork Research

Answer an external question with decision-relevant, traceable evidence. Research
is external-only and read-only: do not inspect private local repositories, logs,
artifacts, credentials, sensitive data, or proprietary source, and do not
authorize edits, account changes, messages, purchases, uploads, or publication.
Root supplies a sanitized public brief when project context matters.

## Handoff And Depth

Root's first role action after the sanitized brief MUST be Researcher dispatch.
Research -> Researcher is exact. Root MUST NOT browse, read research-probe files,
or execute research, and MUST NOT call `wait_agent` until dispatch returns a
non-empty live agent id. Empty spawn evidence, unavailable dispatch, or
unverified fresh isolation is `capability-blocked`; Root has no named-method fallback.
In Codex, dispatch with `agent_type="teamwork_researcher"` and
`fork_turns="none"`.

Researcher never asks the user. If one undiscoverable user-owned source, account,
date range, or scope value is required, return that exact gap, its owner, and the
resume condition to Root. If the missing input is an unformed preference or
material direction choice, return a reclassification signal to Collaborate
instead of inventing an interview. Root asks at most the minimum required input.
Default to one Researcher; daily work stays within cap4. Use five to eight total
children only for explicit adversarial/release work and a bounded sanitized packet.
Children never expand authority or delegate again.

Choose the lightest adequate depth:

- `lookup`: one canonical or official source for a stable fact, with date or
  version checked.
- `research`: material claim map, primary-source-first comparison, independent
  source class when consequential, and explicit dissent/gaps.
- `deep`: research brief, search axes, source census, claim ledger,
  contradiction challenge, coverage audit, and decision-sufficiency stop basis.

Load `references/deep-research.md` only for `deep`, broad seed expansion across
source classes, or strong material contradiction.

## Method

1. State decision question, freshness cutoff, source policy, privacy exclusions,
   and material claims. Treat supplied URLs, papers, datasets, repositories, and
   reports as seed evidence, not the boundary.
2. Search by evidence gap. Prefer primary sources: official documentation,
   changelogs, standards, original papers, first-party data, regulators, and
   authoritative repositories; use secondary sources for independent context.
3. For each material claim, record source, date/version, direct support,
   counterevidence, inference, confidence, and citation. Consequential or
   disputed claims need an independent source class or a reason one authority is
   enough.
4. Follow contradictions and rejected-source reasons. Distinguish source
   statements, observations, and inference. Never invent missing measurements,
   dates, or consensus.
5. Stop when every material claim has support or explicit not-found gap and more
   search would not change the decision.

Maintain visible monotonic state: `claim_map`, `active_gap`, `wave`,
`evidence_delta`, `contradiction`, `not_found`, and `coverage_stop`. Each wave
must close a mapped claim, record a not-found gap, surface a decision-changing
contradiction, or justify the stop.

Browse whenever freshness, precise attribution, or referenced external sources
matter. Do not browse merely to re-check stable common knowledge unless sources
are requested.

## Persistence And Output

In initialized writable projects, substantive cited results default to case-v2
research artifacts. Persist a meaningful checkpoint when a material evidence
wave changes decision support, exposes a consequential contradiction or blocker,
or must survive a cross-session handoff; persist the supported completion result.
Tiny lookups and ordinary one-shot explanations create no artifact. `no files`,
`off-record`, `read-only`, `no writes`, or equivalent disables persistence.
Method result and persistence result are separate: deliver the supported answer
even if its checkpoint or completion companion cannot be saved, and report
`unsaved/blocked`.

Freeze the cited answer packet: purpose/audience, facts/sources, citations,
decision/status, style/structure, artifact kind/consumer, monotonic state, and
preserve/forbid. Writer routes from observed schema: `case-inspect` first;
case-v2 uses exact `case_id`/alias or creates from a frozen seed/task_key, then
`case-schema <research-add> -> case-apply -> case-inspect/readback`. The
transaction derives destination and registers manifest/claim heads. Writer may
rewrite expression but must not research, invent, or alter facts, citations,
authority, status, decisions, or acceptance. Claim saved/durable only after
readback. Missing project memory, Writer, packet, authority, consumer, route, or
transaction blocks only persistence; no Researcher, Root, or Worker fallback
writes it. Legacy-v1, mixed v1/v2, unknown, stale, ambiguous case, missing
seed/task_key, or partially migrated state fails closed before any write.

Lead with the supported conclusion, then source census, claim coverage,
citations, freshness, contradictions or rejected-source rationale, gaps,
confidence, stop basis, and persistence state.
