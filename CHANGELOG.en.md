# Changelog

[中文](CHANGELOG.md)

This changelog records user-visible changes; implementation details belong in Git history or pull requests.

## 4.3.0 - 2026-07-21

**Describe the design problem normally; Teamwork Design now decides whether adversarial search is warranted.**

- **The problem selects the method.** Before, adversarial search required an explicit `$teamwork-design adversarial` command. After, `teamwork-design` upgrades automatically when at least two viable directions remain and costly or irreversible error or conflicting evidence makes one ordinary challenge inadequate.
- **No budget confirmation round.** The model states its reason and envelope, then uses default `B=3`; users no longer need to spell out the strategy, budget, or “do not enter Plan or implementation.” For exact control, `adversarial` still forces the method and `standard` disables it.
- **Ordinary Design stays lightweight.** Merely saying “high-risk,” “complex,” or `brainstorm` does not add agent work; requests below the automatic gate still receive one challenge pass.
- **Safety boundaries are unchanged.** Automatic selection authorizes only read-only Design search. Fresh isolation, paired critics, dual final audit, and durable Design / Plan / implementation boundaries remain intact.

Upgrade action: Codex Marketplace users re-add `JinPLu/Teamwork`, install `teamwork-skill@teamwork`, and run `$teamwork-update` in a new task. Checkout users run `git pull --ff-only`, `./install.sh all`, and `./scripts/check-update.sh --readiness`.

Important limit: automatic selection depends on the host model's semantic judgment of the request and evidence, so models need not make byte-identical choices; use `adversarial` or `standard` when the strategy must be deterministic.

## 4.2.0 - 2026-07-21

**Teamwork Design can now opt into budgeted adversarial search: ordinary design stays lightweight, while decisions that need stronger pressure-testing can use multiple hypotheses, paired independent critics, and dual closure audit.**

- **You choose the design intensity.** Before, `$teamwork-design` always used one challenge pass. After, that default remains unchanged and only an explicit `$teamwork-design adversarial` request starts adversarial search. Risk, complexity, or bare `brainstorm` language never adds the cost automatically.
- **The search has a visible ceiling.** Teamwork shows the goal, fitness function, taxonomy, and hypothesis-trial budget before dispatch; it recommends `budget=3` when none is supplied. Every actual hypothesis receives two fresh independent critics, a material revision consumes a new trial, and two new final auditors must both pass.
- **Failure cannot masquerade as a Design.** Unproven isolation, exhausted budget, audit disagreement, or interruption returns an explicit incomplete result instead of silently downgrading, extending the budget, or producing a durable Design.
- **Design, Grill, and Plan ownership stays intact.** Adversarial search remains inside `teamwork-design`, with no eleventh skill or new role. A passing chat conclusion is still not Plan-ready; a durable Design appears only after explicit user acceptance and an authorized controlled write.

Upgrade action: Codex Marketplace users re-add `JinPLu/Teamwork`, install `teamwork-skill@teamwork`, and run `$teamwork-update` in a new task. Checkout users run `git pull --ff-only`, `./install.sh all`, and `./scripts/check-update.sh --readiness`.

Important limit: this release fails closed on hosts that cannot prove fresh isolation. Static validation or one-host forward testing does not establish identical live behavior across Codex, Cursor, and Claude Code.

## 4.1.0 - 2026-07-20

**Teamwork 4.1.0 restores mandatory formal role-dispatch configuration and stable Codex `multi_agent` routing; Grill and Design can still batch independent key questions and keep dependent choices serial. Live cross-host dispatch verification is deferred pending Codex quota, so this release does not claim runtime-proven dispatch.**

- Formal Research, Explore, Debug, Design, Plan, Worker, and Review policy again routes through host-native roles in skill instructions and host templates; clear local work remains on the native path.
- Grill now starts with a global decision map, then asks at most three independent questions; each question carries its recommendation, downside, criticality, blocked outcome, dependencies, and closure signal.
- Design uses the same finite frontier rule: independent decisions can be answered together, while one answer that changes another question's options forces a later turn.
- Discussion persistence uses schema v2 `frontier` and `current_batch` state; one answered batch produces one atomic semantic update, while existing v1 archives remain readable.
- Codex activation uses the stable `[features] multi_agent = true` setting and preserves existing `[agents] max_threads` limits; deterministic tests and full package validation cover these configuration changes, while the 104-record live cross-host matrix stays deferred until Codex quota allows rerunning it.
- Cursor installs now register `codegraph` and `gpu-broker` in `~/.cursor/mcp.json` by default; use `--no-mcp` to opt out and enable servers in Cursor Settings -> MCP.
- Project init can write `.cursor/rules/` and project `.cursor/mcp.json` with explicit `--cursor-mcp` consent.
- Convergence diagrams stay short: they show route, status, and dependencies, while full reasons and evidence appear once in readable text.
- Cursor `performance-first` and `cost-first` profiles now rebalance models per role: Researcher uses terra/flash, Explorer uses flash, and Debugger/Designer/Planner/Plan Reviewer/Reviewer switch among opus, sol, terra, luna, and fable by role while Worker stays on composer-2.5-fast.
- `--readiness` now surfaces the exact Cursor User Rules paste steps; Research, Explore, Goal, Update, and Design/Grill transaction-path skill boundaries are clearer; CodeGraph MCP failures fall back to direct file reads; and `gpu-broker` rules load only on likely GPU projects.

## 4.0.0 - 2026-07-20

**Teamwork is now a smaller set of focused capabilities, while clear local work stays with the host.**

- Routine code inspection and authorized implementation no longer go through a generic Teamwork Router or Execute wrapper; when a task needs a distinct method, the ten public skills cover Research, Explore, Design, Debug, Plan, Review, Goal, Grill, Init, and Update.
- Explore handles local project evidence, while Research handles external or current evidence; Design expands only when a real tradeoff can change the result, then freezes a traceable direction before Plan.
- Workers complete and verify their owned slice first; after the main task integrates a candidate, independent Review runs once only on user request or a named risk gate, with at most one focused recheck after fixes.
- Codex uses the Marketplace plugin as the default installation and update path; checkout installation remains for Cursor, Claude Code, local development, or manual Codex setup.
- Codex `performance-first` now assigns models by role: Researcher, Explorer, Debugger, Planner, and Worker use `gpt-5.5/high`; Designer and Plan Reviewer use `gpt-5.6-sol/high`; Reviewer uses `gpt-5.6-sol/max`.
- Ordinary question-first discussion stays in conversation. Explicit save, resume, or independently major discussion uses the single Grill record, and it updates only for a real decision, open-question change, close, or replacement.

To upgrade, v3.4.2 users rerun their applicable install command or `$teamwork-update`. Marketplace users remove and re-add `JinPLu/Teamwork`, install `teamwork-skill@teamwork`, then start a new task and run `$teamwork-update`; checkout users run `git pull --ff-only`, `./install.sh all`, and `./scripts/check-update.sh --readiness`.

Compatibility boundary: v4 has no legacy Router, Execute, or role aliases. Migration deletes only old files that Teamwork can prove it owns, and natural-language skill selection still belongs to the host model.

## 3.4.2 - 2026-07-19

**Public documentation became shorter and easier to use.**

- The README, Codex, Cursor, Claude Code, and Marketplace docs lead with what users can accomplish and retain only the boundaries needed to use it.
- Codex Marketplace uses an unpinned `JinPLu/Teamwork`, so `$teamwork-update` can continue advancing to new releases.
- Public-document guidance now centers on user outcomes, actionable boundaries, and only necessary explanation.

## 3.4.1 - 2026-07-19

**Release notes now lead with the change users can feel.**

- Each entry starts with a summary and uses concise points for the source and user impact.
- This release changes documentation style only; Teamwork runtime behavior is unchanged.

## 3.4.0 - 2026-07-18

**Codex can enable Teamwork from the Marketplace in one step.**

- Install `teamwork-skill@teamwork`, then run `$teamwork-update` in a new task to configure agents, routing, policy, and optional notifications.
- Marketplace installation does not silently rewrite configuration, trust hooks, or create extra skill copies.
- `grill-me` can save an explicitly requested continuation, while clearly scoped ordinary work proceeds directly.

## 3.3.0 - 2026-07-16

**The requested result comes first, so simple work stays light.**

- Clear change or run requests take the shortest real path, check only the current blocker, actual change, or named high-risk boundary, and stop when the result exists.
- Natural requests such as “ask me first,” “find the cause,” and “continue with the accepted approach” can reach discussion, research, diagnosis, or execution.
- `grill-me` saves a record only when discussion is explicitly requested and there is a useful continuation; an ordinary plan creates no discussion file.
- `teamwork-update` owns global refreshes, while `teamwork-init` owns project instructions and context.

## 3.2.0 - 2026-07-16

**Discussion sounds more natural and resumes at the right question.**

- `using-teamwork` connects the conclusion, evidence, plain interpretation, and decision-relevant boundary while separating observation from inference.
- `grill-me` remembers settled conclusions and the next comparison, measurement, or decision.

## 3.1.1 - 2026-07-15

**No update is needed; Teamwork works the same way.**

- This patch completes the 3.1.0 release record without changing any subskill or runtime behavior.

## 3.1.0 - 2026-07-15

**An interrupted discussion can resume at its open question.**

- `grill-me` keeps the goal, settled choices, open question, key evidence, and continuation point without re-asking settled choices.
- Ordinary replies lead with the conclusion and decision-relevant facts, while interrupted initialization recovers under the project lock or stops safely.

## 3.0.0 - 2026-07-15

**Replies became more direct, and projects stopped carrying a Teamwork copy.**

- Ordinary replies lead with the conclusion, important reason, and next step; eligible long discussions can keep a compact route and replay when authorized.
- `init-project` writes project instructions, memory, and CodeGraph context without copying the Teamwork package into the project.

## 2.22.0 - 2026-07-15

**Shared rules became leaner and portable without weakening boundaries.**

- Global rules, skills, agents, and project initialization keep their own responsibilities, with compact project instructions and indexes.
- Public-package checks reject real user paths, session identifiers, private addresses, and credential-shaped values.
- Maintainers can compare prompt candidates without publishing raw model output.

## 2.21.1 - 2026-07-15

**Maintenance entry points stayed compatible while runtime behavior stayed unchanged.**

- Maintainers gained a small private-install check that retains only a redacted summary.

## 2.21.0 - 2026-07-15

**Long discussions are easier to recover after compression, pause, or handoff.**

- A long discussion can keep accepted directions, open decisions, and key evidence without storing a transcript or granting execution authority.
- Initialization protects human documents and custom content, while refreshing installed content remains separate from publishing a release.

## 2.20.0 - 2026-07-14

**Changes reuse the existing owner and avoid unnecessary wrappers and fallbacks.**

- Implementation starts in the path that owns the behavior; extra modes, wrappers, fallbacks, and dependencies need a real requirement.
- Install and update checks distinguish missing, stale, and drifted skills and agents across platforms.
- Expired, unaccepted, or irrelevant records no longer direct current work.

## 2.19.0 - 2026-07-13

**Completion and permission reminders became available by default while hooks stayed narrowly trusted.**

- Full Codex and Claude Code installs can enable completion and permission sounds, while direct platform installs remain selectable.
- Readiness checks distinguish trusted, review-required, and unverifiable hooks and handle `Stop` and `PermissionRequest` separately.

## 2.18.0 - 2026-07-13

**Teamwork checks evidence first and asks only when your decision is required.**

- It asks only for necessary input, observation, or material decisions; independent read-only work can continue while one branch waits.
- Working facts keep only the goal, scope, acceptance, authority, blockers, and stop conditions that matter.
- Review blocks only boundary violations, regressions, or missing evidence, and Goal starts only after an explicit request or accepted proposal.

## 2.17.0 - 2026-07-13

**Important directions align early, and fixes and reviews converge faster.**

- Planning checks evidence, asks one genuinely user-owned question at a time, and gives a recommendation.
- Review gets one full pass, then a focused check of the original findings and new regressions after fixes.
- Known causes return to implementation, unknown causes to diagnosis, and scope changes to planning.

## 2.16.0 - 2026-07-13

**`grill-me` became a discoverable skill for questions that change the result.**

- Discussion stays on decisions the user must own instead of filling a quota with reversible wording or internal layout.
- Codex subagents use the model and reasoning effort from their installation profile, with up to nine concurrent threads.

## 2.15.0 - 2026-07-13

**Corrections stop stale work immediately.**

- Background work does not continue on an outdated direction, and partial or unverified results remain visibly incomplete.
- Optional sounds notify only the main task; read-only diagnostics reveal agent setup and unusually long tasks without conversation text.

## 2.14.0 - 2026-07-11

**Codex model profiles moved to GPT-5.6 with clearer quality tiers.**

- `performance-first`, `cost-first`, `gpt56-high`, and `gpt56-xhigh` provide distinct model and reasoning combinations.
- Cursor and Claude Code use native platform mappings, while compatibility profile names remain available.

## 2.13.0 - 2026-07-10

**Sufficient information moves work forward without adding ceremony.**

- Hypothesis lists, tables, durable records, independent review, test-first work, and alternatives activate according to risk and need.
- Codex `gpt56-role` assigns model and effort by responsibility and fails clearly when a pinned choice is unavailable.

## 2.11.1 - 2026-07-08

**Small fixes stay fast, while “discuss first” is honored.**

- Small tasks do not gain automatic questions, subagents, or durable plans; an explicit `grill-me` or discussion request still pauses them.
- Unanswered material installation and update decisions stop progress.

## 2.11.0 - 2026-07-08

**Complex work checks evidence before returning the decisions that belong to you.**

- Research, Debug, Plan, Execute, Review, and Goal share one confirmation boundary.
- `check-update.sh` compares installed content as well as versions across global and project surfaces.

## 2.10.0 - 2026-07-08

**Candidate Teamwork behavior became comparable without changing everyday work.**

- Maintainers can compare old and candidate behavior on the same tasks and keep model, configuration, verification, rollback, and independent-review evidence.

## 2.9.0 - 2026-07-08

**Offline regression and release checks cover the full work boundary.**

- Fixed cases cover simple work, debugging, research, review, goals, installation, and platform rules, with acceptance or rejection recorded before release.

## 2.8.1 - 2026-07-08

**“Discuss first” pauses every dependent decision during implementation.**

- Analysis, direction choices, edits, and delegation wait for confirmation.
- Code changes begin in the existing owner, and review rejects unsupported branches, defaults, and fallbacks.
- Update checks detect stale skills, agents, and global policy.

## 2.8.0 - 2026-07-08

**An explicit request to be grilled starts discussion before background work.**

- “Grill me,” “ask first,” or “challenge assumptions” produces at least one outcome-changing question with a recommendation.
- Root, delegated, and Goal work waits for an answer or opt-out.
- Content-aware update checks detect stale rules even when versions match.

## 2.7.1 - 2026-07-07

**Changes and reviews became more direct and maintainable.**

- Implementation and acceptance start from the existing owner and its verification path.
- All three platforms reject unsupported branches, modes, wrappers, defaults, and fallbacks.

## 2.7.0 - 2026-07-01

**Codex gained a higher-reasoning profile, and replies became less rushed.**

- `gpt55-xhigh` gives Codex subagents GPT-5.5 with xhigh reasoning; Cursor and Claude Code keep their native tiers.
- Evidence-sensitive work reads, interprets, and verifies before answering, while progress stays tied to decisions, blockers, and checks.

## 2.6.0 - 2026-06-23

**Research looks beyond the first source, and missing values are not guessed.**

- Research seeks primary and neighboring sources, counter-evidence, gaps, and open questions before recommending.
- Missing paths, ports, models, hyperparameters, credentials, configuration, or invariants cause a question, investigation, or stop.
- Review flags unnecessary code, broad defenses, silent defaults, hidden fallbacks, and regressions.

## 2.5.0 - 2026-06-22

**Long-running Goal work stopped retrying failures blindly.**

- Goal keeps attempt history and classifies missing evidence, stale plans, wrong scope, and implementation errors before retrying.
- `scripts/init-project.sh` prepares project context and installation.

## 2.4.1 - 2026-06-21

**Cursor's manual global setup became easier to complete.**

- `./install.sh cursor-policy-copy` copies the Cursor User Rules text, and readiness checks call out the required paste.

## 2.4.0 - 2026-06-21

**Natural-language requests reach the needed Teamwork capability while simple work stays light.**

- Everyday wording maps more consistently to research, diagnosis, planning, execution, review, Goal, initialization, or update.
- Small tasks stay close to the host's fast path, while larger tasks load only the guidance they need.

## 2.3.0 - 2026-06-21

**Bug reports collect root-cause evidence before a fix is chosen.**

- `teamwork-debug` gathers reproduction, logs, hypotheses, and runtime evidence, separates cause from symptom, and cleans up temporary probes.
- Upstream-remote detection in `scripts/check-update.sh` is corrected.

## 2.2.0 - 2026-06-16

**Installation freshness became directly checkable.**

- `scripts/check-update.sh`, version markers, `--project-root`, and broader project installation support make platform state visible.
- Installation contents and documentation begin tracking the same multi-platform surface.

## 2.0.0 - 2026-06-16

**Clear requests move forward with fewer interruptions.**

- Teamwork asks about blockers and core decisions, keeps delegation rules focused, and avoids ceremony around ordinary work.
- Package-integrity checks remain part of platform installation.

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

**Skills load progressively, so simple requests use less context.**

- Deep research returns only useful evidence, while installation updates and current library and API lookups become more capable.

## 1.5.0 - 1.10.0 - 2026-06-05

**Teamwork gained durable context and safer decision boundaries.**

- Long-running work can keep important context across sessions, with careful external-memory import and project initialization protection.
- Missing required values fail clearly instead of becoming guessed defaults, while reviewability is preserved.

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

**Codex installation gained cost and performance preferences.**

- `performance-first` and `cost-first` set subagent defaults for the selected preference.

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

**The multi-role collaboration skeleton took shape.**

- Research, implementation, acceptance, and delegated handoffs became separate responsibilities.

## 0.14.0 - 2026-06-01

**Codex Teamwork authorization became reusable across projects.**

- A managed block in `~/.codex/AGENTS.md` carries subagent permission without repeating it in each project.

## 0.13.0 - 2026-05-31

**Codex parallel delegation gained clearer authorization boundaries.**

- Subagent authorization rules make parallel work safer to dispatch.

## 0.12.0 - 2026-05-28

**Claude Code became a first-class Teamwork platform.**

- Teamwork gained Claude Code installation, documentation, role support, and maintenance checks.

## 0.11.0 - 2026-05-27

**Cursor became a first-class Teamwork platform.**

- Teamwork gained Cursor installation, documentation, subagent collaboration, and long-running Goal support.

## 0.10.0 - 2026-05-27

**Teamwork checks capabilities before dispatching or accepting delegated work.**

- It verifies dispatch options instead of declaring subagents unavailable early, and independent acceptance must come from fresh context.

## 0.9.0 - 2026-05-27

**Teamwork became an installable, versioned collaboration package.**

- `teamwork-init`, focused skills, automatic routing, durable records, and evidence-based review establish the package.

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

**Teamwork grew from one optimization prompt into a collaboration system.**

- Research, planning, implementation, review, and long-running goals became separate capabilities with evidence checks, durable plans, Goal commands, and Codex routing.
