---
name: teamwork-research
description: Use when the requested answer depends on external sources, including current web, API, library, platform, literature, market, or ecosystem facts, multi-source comparison, source verification, or citations; do not use for local repository/source/config/test/log/runtime/artifact inspection, supplied-text explanation, clear implementation, or unknown-cause debugging.
---

# Teamwork Research

Answer an external question with decision-relevant, traceable evidence. Research
is external-only: do not inspect private local repositories, logs, or artifacts;
Root supplies a sanitized public question when project context informs it.

## Root Handoff

Before any Research method step, Root's first role action after the sanitized
brief MUST be Researcher dispatch. Root MUST NOT browse, read research-probe
files, or execute research. In Codex, call `spawn_agent` with
`agent_type="teamwork_researcher"` and `fork_turns="none"`. In Cursor and Claude
Code, dispatch Researcher via the host mechanism before browsing. If dispatch is
unavailable, stop. Root MUST NOT call `wait_agent` until `spawn_agent` returns a
non-empty live agent id. Empty spawn evidence, unavailable spawn, or wait without
a live agent is STOP: unsupported role boundary.

## Choose Depth

Use the lightest adequate depth:

- `lookup`: one canonical or official source for a stable fact, with its date or
  version checked;
- `research`: a material-claim map, primary-source-first comparison, an
  independent source class where consequential, and explicit dissent or gaps;
- `deep`: a research brief, search axes, source census, per-claim ledger,
  contradiction challenge, coverage audit, and decision-sufficiency stop basis.

Load `references/deep-research.md` only for `deep`, broad seed expansion across
several source classes, or a strong material contradiction. The reference is an
advanced method for this Skill, not another workflow stage.

## Method

1. State the decision question, freshness cutoff, source policy, privacy
   exclusions, and material claims. Treat supplied URLs, papers, datasets,
   repositories, or reports as seed evidence, not the whole boundary.
2. Search by evidence gap. Prefer primary sources: official documentation and
   changelogs, standards, original papers, first-party data, regulators, and
   authoritative repositories. Use secondary sources for independent context.
3. Record each material claim's source, date/version, direct support,
   counterevidence, inference, confidence, and citation. For consequential or
   disputed claims, seek an independent source class or explain why one
   authoritative source is enough.
4. Follow decision-changing contradictions and rejected-source reasons instead
   of averaging them away. Distinguish source statements, direct observations,
   and inference. Never invent missing measurements, dates, or consensus.
5. Cite the direct supporting page near each important claim and record explicit
   not-found gaps. Source count is not claim coverage.
6. Stop when every material claim has support or an explicit gap and more search
   would not change the decision. If evidence is insufficient, return only the
   next decision-relevant discriminator.

Browse whenever freshness, precise attribution, or a referenced external source
matters. Do not browse merely to re-check stable common knowledge unless the user
asks for sources. Never send private source code, logs, credentials, personal
data, or proprietary artifacts to a public service.

Research does not authorize account changes, messages, purchases, uploads, or
publication. In an initialized writable project, each terminal cited answer
defaults to a research artifact unless the user says `no files`, `off-record`,
`read-only`, `no writes`, or equivalent. Researcher returns a bounded packet:
purpose/audience, facts/sources, citations, frozen decision/status,
style/structure, artifact kind/consumer, and preserve/forbid. Writer must use
`discussion-transaction.py artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply`;
the transaction derives the destination and registers the ordinary index. Writer
may rewrite expression but must not research, invent, or alter facts, citations,
authority, status, decisions, or acceptance. Missing project memory, Writer,
brief, authority, consumer, or transaction blocks only persistence: deliver the
answer and report it unsaved/blocked. No Researcher, Root, or Worker fallback writes it.

After the primary Researcher handoff, additional fan-out remains conditional:
use it only for separable source classes, required public/private isolation, or
one bounded verification of a consequential disputed claim. A normal comparison
keeps one adaptive Researcher and one synthesis owner.

Lead with the supported conclusion. Include source census, material-claim
coverage, citations, freshness, contradictions or rejected-source rationale,
gaps, confidence, and the stop basis in proportion to the selected depth.
