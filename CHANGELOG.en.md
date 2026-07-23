# Changelog

[中文](CHANGELOG.md)

This changelog records user-visible changes; implementation details belong in Git history or pull requests.

## 4.4.0 - 2026-07-23

**Named Teamwork workflows now persist reusable results by default, with clearer boundaries for standalone documents, Design states, and instructions.**

- **Default persistence has a complete matrix.** In initialized writable projects, Grill, Design, Goal, Research, Debug, Plan, Review, and mutating Init/Update save reusable results by default. Ordinary chat, one-off native work, and clear code tasks do not force extra documentation; Explore creates no standalone report, and `no files`, off-record, read-only, or no-write overrides the default.
- **Standalone documents belong to Writer.** A simple model handles all normal standalone documents and rewrites, including drafting, organizing, summarizing, translating, and polishing. Research and decisions stay with the corresponding specialist roles, while code-related wording stays with coding roles.
- **Design states are visible to users.** A Design can remain `pending`, become `accepted`, or move to `blocked`; saving is not acceptance, only `accepted` may enter Plan, and existing Design records remain compatible.
- **Instructions stay light without losing boundaries.** Teamwork guidance stays concise without deleting decision, evidence, authority, or acceptance boundaries just to shorten the text.

Upgrade action: Codex Marketplace users re-add `JinPLu/Teamwork`, install `teamwork-skill@teamwork`, and run `$teamwork-update` in a new task. Checkout users run `git pull --ff-only`, `./install.sh all`, and `./scripts/check-update.sh --readiness`.

Important limit: Default persistence applies only when a named workflow is actually active, the project is initialized and writable, and Teamwork can save safely; `no files`, off-record, read-only, or no-write always wins. Persistence does not authorize implementation or release. When those conditions are missing, Teamwork still delivers the primary result first and reports that it was not saved.

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

**Teamwork 4.1.0 restores formal role routing; Grill and Design can still batch independent questions, while live cross-host dispatch remains unverified.**

- **Formal role routing is restored.** Research, Explore, Debug, Design, Plan, Worker, and Review again use host-native roles, while clear local work stays native. Codex preserves the user's existing concurrency limit, and live cross-host dispatch still awaits confirmation when quota permits.
- **Related decisions batch and resume cleanly.** Grill starts with a global decision map and asks at most three independent questions, each carrying its recommendation, downside, criticality, blocked outcome, dependencies, and closure signal; Design batches independent decisions and serializes dependent ones. One answered batch saves one complete update, existing discussion archives remain readable, and compact convergence diagrams show only route, status, and dependencies while reasons and evidence appear once outside them.
- **Cursor setup boundaries are explicit.** Cursor installs register `codegraph` and `gpu-broker` in `~/.cursor/mcp.json` by default; `--no-mcp` opts out, and servers still need enabling in Cursor Settings -> MCP. Project init writes `.cursor/rules/` and project `.cursor/mcp.json` only with explicit `--cursor-mcp` consent. `--readiness` shows the User Rules paste steps and clearer saving boundaries for Research, Explore, Goal, Update, Design, and Grill; unavailable CodeGraph MCP falls back to direct file reads, and `gpu-broker` rules load only for likely GPU projects.
- **Cursor profiles map models by role.** `performance-first` and `cost-first` rebalance models: Researcher uses terra/flash, Explorer uses flash, Debugger/Designer/Planner/Plan Reviewer/Reviewer switch among opus, sol, terra, luna, and fable by role, and Worker stays on composer-2.5-fast.

## 4.0.0 - 2026-07-20

**Teamwork is now a smaller set of focused capabilities, while clear local work stays with the host.**

- **Native work and ordinary discussion stop taking detours.** Routine code inspection and authorized implementation no longer go through a generic Router or Execute wrapper; the ten public skills cover Research, Explore, Design, Debug, Plan, Review, Goal, Grill, Init, and Update when a distinct method is needed. Ordinary question-first discussion stays in conversation; explicit save, resume, or independently major discussion uses the single Grill record, which updates only for a real decision, open-question change, close, or replacement.
- **Evidence and Design keep distinct boundaries.** Explore handles local project evidence, Research handles external or current evidence, and Design expands only when a real tradeoff can change the result before freezing a traceable direction for Plan.
- **Workers prove their slice before Review.** Workers complete and verify their owned slice first; after the main task integrates a candidate, independent Review runs once only on user request or a named risk gate, with at most one focused recheck after fixes.
- **Codex installation and profiles follow roles.** Codex uses the Marketplace plugin as the default installation and update path, while checkout remains for Cursor, Claude Code, local development, or manual Codex setup. Under `performance-first`, Researcher, Explorer, Debugger, Planner, and Worker use `gpt-5.5/high`; Designer and Plan Reviewer use `gpt-5.6-sol/high`; Reviewer uses `gpt-5.6-sol/max`.

Upgrade action: v3.4.2 users rerun their applicable install command or `$teamwork-update`. Marketplace users remove and re-add `JinPLu/Teamwork`, install `teamwork-skill@teamwork`, then start a new task and run `$teamwork-update`; checkout users run `git pull --ff-only`, `./install.sh all`, and `./scripts/check-update.sh --readiness`.

Important limit: v4 has no legacy Router, Execute, or role aliases. Migration deletes only old files that Teamwork can prove it owns, and natural-language skill selection still belongs to the host model.

## 3.4.2 - 2026-07-19

**Public documentation became shorter and easier to use.**

- **Docs lead with outcomes.** The README, Codex, Cursor, Claude Code, and Marketplace docs lead with what users can accomplish and retain only the boundaries needed to use it.
- **Updates can keep advancing.** Codex Marketplace uses an unpinned `JinPLu/Teamwork`, so `$teamwork-update` can continue advancing to new releases.
- **Guides use a consistent voice.** Public documentation centers on user outcomes, actionable boundaries, and only necessary explanation.

## 3.4.1 - 2026-07-19

**Release notes now lead with the change users can feel.**

- **Entries lead with user-visible change.** Each entry starts with a summary and uses concise points for the source and user impact.
- **Runtime behavior is unchanged.** This release changes documentation style only; Teamwork runtime behavior is unchanged.

## 3.4.0 - 2026-07-18

**Codex can enable Teamwork from the Marketplace in one step.**

- **Marketplace enables Teamwork in one step.** Install `teamwork-skill@teamwork`, then run `$teamwork-update` in a new task to configure agents, routing, policy, and optional notifications.
- **Installation stays within bounds.** Marketplace installation does not silently rewrite configuration, trust hooks, or create extra skill copies.
- **Discussion can resume while work stays direct.** `grill-me` can save an explicitly requested continuation, while clearly scoped ordinary work proceeds directly.

## 3.3.0 - 2026-07-16

**The requested result comes first, so simple work stays light.**

- **Clear work takes the shortest path.** Clear change or run requests take the shortest real path, check only the current blocker, actual change, or named high-risk boundary, and stop when the result exists.
- **Natural language reaches the right capability.** Natural requests such as “ask me first,” “find the cause,” and “continue with the accepted approach” can reach discussion, research, diagnosis, or execution.
- **Discussion is saved only with a useful continuation.** `grill-me` saves a record only when discussion is explicitly requested and there is a useful continuation; an ordinary plan creates no discussion file.
- **Update responsibilities are separate.** `teamwork-update` owns global refreshes, while `teamwork-init` owns project instructions and context.

## 3.2.0 - 2026-07-16

**Discussion sounds more natural and resumes at the right question.**

- **Replies connect conclusions and evidence.** `using-teamwork` connects the conclusion, evidence, plain interpretation, and decision-relevant boundary while separating observation from inference.
- **Discussion remembers the continuation point.** `grill-me` remembers settled conclusions and the next comparison, measurement, or decision.

## 3.1.1 - 2026-07-15

**No update is needed; Teamwork works the same way.**

- **Only the release record changed.** This patch completes the 3.1.0 release record without changing any subskill or runtime behavior.

## 3.1.0 - 2026-07-15

**An interrupted discussion can resume at its open question.**

- **Discussion resumes from its open point.** `grill-me` keeps the goal, settled choices, open question, key evidence, and continuation point without re-asking settled choices.
- **Replies and initialization recover cleanly.** Ordinary replies lead with the conclusion and decision-relevant facts, while interrupted initialization recovers under the project lock or stops safely.

## 3.0.0 - 2026-07-15

**Replies became more direct, and projects stopped carrying a Teamwork copy.**

- **Replies lead with the conclusion.** Ordinary replies lead with the conclusion, important reason, and next step; eligible long discussions can keep a compact route and replay when authorized.
- **Projects stop copying the package.** `init-project` writes project instructions, memory, and CodeGraph context without copying the Teamwork package into the project.

## 2.22.0 - 2026-07-15

**Shared rules became leaner and portable without weakening boundaries.**

- **Project guidance is lean and portable.** Projects receive compact, portable instructions and indexes instead of duplicated rules.
- **Public packages exclude sensitive data.** Real user paths, session identifiers, private addresses, and credential-shaped values do not enter the public package.

## 2.21.1 - 2026-07-15

**Installation and runtime behavior stay unchanged in this patch.**

- **No user action is required.** Installation and runtime behavior stay unchanged, and public content contains no raw private data.

## 2.21.0 - 2026-07-15

**Long discussions are easier to recover after compression, pause, or handoff.**

- **Discussion keeps only necessary state.** A long discussion can keep accepted directions, open decisions, and key evidence without storing a transcript or granting execution authority.
- **Initialization stays separate from release authority.** Initialization protects human documents and custom content, while refreshing installed content remains separate from publishing a release.

## 2.20.0 - 2026-07-14

**Changes reuse established paths and avoid unnecessary wrappers and fallbacks.**

- **Changes reuse established paths.** Implementation starts in the established behavior path; extra modes, wrappers, fallbacks, and dependencies need a real requirement.
- **Installation drift is visible.** Install and update checks distinguish missing, stale, and drifted skills and agents across platforms.
- **Expired records stop directing work.** Expired, unaccepted, or irrelevant records no longer direct current work.

## 2.19.0 - 2026-07-13

**Completion and permission reminders became available by default while hooks stayed narrowly trusted.**

- **Reminders stay platform-selectable.** Full Codex and Claude Code installs can enable completion and permission sounds, while direct platform installs remain selectable.
- **Hook trust state is visible.** Readiness checks distinguish trusted, review-required, and unverifiable hooks and handle `Stop` and `PermissionRequest` separately.

## 2.18.0 - 2026-07-13

**Teamwork checks evidence first and asks only when your decision is required.**

- **Only necessary decisions are asked.** It asks only for necessary input, observation, or material decisions; independent read-only work can continue while one branch waits.
- **Working state stays compact.** Working facts keep only the goal, scope, acceptance, authority, blockers, and stop conditions that matter.
- **Review and Goal have explicit gates.** Review blocks only boundary violations, regressions, or missing evidence, and Goal starts only after an explicit request or accepted proposal.

## 2.17.0 - 2026-07-13

**Important directions align early, and fixes and reviews converge faster.**

- **One decision is asked at a time.** Planning checks evidence, asks one genuinely user-owned question at a time, and gives a recommendation.
- **Review goes full once, then focused.** Review gets one full pass, then a focused check of the original findings and new regressions after fixes.
- **Work returns to the right path.** Known causes return to implementation, unknown causes to diagnosis, and scope changes to planning.

## 2.16.0 - 2026-07-13

**`grill-me` became a discoverable skill for questions that change the result.**

- **Questions stay on user-owned decisions.** Discussion stays on decisions the user must own instead of filling a quota with reversible wording or internal layout.
- **Codex profiles control subagents.** Codex subagents use the model and reasoning effort from their installation profile, with up to nine concurrent threads.

## 2.15.0 - 2026-07-13

**Corrections stop stale work immediately.**

- **Stale directions stop immediately.** Background work does not continue on an outdated direction, and partial or unverified results remain visibly incomplete.
- **Reminders stay on the main task.** Optional sounds notify only the main task; read-only diagnostics reveal agent setup and unusually long tasks without conversation text.

## 2.14.0 - 2026-07-11

**Codex model profiles moved to GPT-5.6 with clearer quality tiers.**

- **Codex offers four quality tiers.** `performance-first`, `cost-first`, `gpt56-high`, and `gpt56-xhigh` provide distinct model and reasoning combinations.
- **Other hosts keep native mappings.** Cursor and Claude Code use native platform mappings, while compatibility profile names remain available.

## 2.13.0 - 2026-07-10

**Sufficient information moves work forward without adding ceremony.**

- **Extra process follows risk.** Hypothesis lists, tables, durable records, independent review, test-first work, and alternatives activate according to risk and need.
- **Unavailable pinned models fail clearly.** Codex `gpt56-role` assigns model and effort by responsibility and fails clearly when a pinned choice is unavailable.

## 2.11.1 - 2026-07-08

**Small fixes stay fast, while “discuss first” is honored.**

- **Small work does not gain automatic process.** Small tasks do not gain automatic questions, subagents, or durable plans; an explicit `grill-me` or discussion request still pauses them.
- **Material install and update decisions pause work.** Unanswered material installation and update decisions stop progress.

## 2.11.0 - 2026-07-08

**Complex work checks evidence before returning the decisions that belong to you.**

- **Confirmation boundaries stay consistent.** Research, Debug, Plan, Execute, Review, and Goal share one confirmation boundary.
- **Updates compare versions and content.** `check-update.sh` compares installed content as well as versions across global and project surfaces.

## 2.10.0 - 2026-07-08

**Candidate Teamwork behavior became comparable without changing everyday work.**

- **Everyday use stays unchanged.** Candidate behavior can be compared consistently before adoption without changing ordinary task behavior.

## 2.9.0 - 2026-07-08

**Pre-release protection covers the full work boundary.**

- **Every task class gets release protection.** Simple work, debugging, research, review, goals, installation, and platform rules are all covered before adoption.

## 2.8.1 - 2026-07-08

**“Discuss first” pauses every dependent decision during implementation.**

- **Dependent actions wait.** Analysis, direction choices, edits, and delegation wait for confirmation.
- **Code changes start with the established path.** Code changes begin in the path already responsible for the behavior, and review rejects unsupported branches, defaults, and fallbacks.
- **Stale installation state is visible.** Update checks detect stale skills, agents, and global policy.

## 2.8.0 - 2026-07-08

**An explicit request to be grilled starts discussion before background work.**

- **Discussion requests really trigger.** “Grill me,” “ask first,” or “challenge assumptions” produces at least one outcome-changing question with a recommendation.
- **Execution waits for confirmation.** Plan, implementation, Goal, and Worker delegation wait for an answer or opt-out.
- **Same-version drift is detectable.** Content-aware update checks detect stale rules even when versions match.

## 2.7.1 - 2026-07-07

**Changes find the established behavior path before work begins.**

- **Established paths and verification come first.** Implementation and acceptance start from the existing behavior path and its verification route.
- **Unsupported complexity is rejected.** All three platforms reject unsupported branches, modes, wrappers, defaults, and fallbacks.

## 2.7.0 - 2026-07-01

**Codex gained a higher-reasoning profile, and replies became less rushed.**

- **Codex gains an xhigh tier.** `gpt55-xhigh` gives Codex subagents GPT-5.5 with xhigh reasoning; Cursor and Claude Code keep their native tiers.
- **Evidence-sensitive work stops rushing.** Evidence-sensitive work reads, interprets, and verifies before answering, while progress stays tied to decisions, blockers, and checks.

## 2.6.0 - 2026-06-23

**Research looks beyond the first source, and missing values are not guessed.**

- **Research keeps checking.** Research seeks primary and neighboring sources, counter-evidence, gaps, and open questions before recommending.
- **Missing values are not guessed.** Missing paths, ports, models, hyperparameters, credentials, configuration, or invariants cause a question, investigation, or stop.
- **Review flags excess defense.** Review flags unnecessary code, broad defenses, silent defaults, hidden fallbacks, and regressions.

## 2.5.0 - 2026-06-22

**Long-running Goal work stopped retrying failures blindly.**

- **Goal classifies failure before retrying.** Goal keeps the objective, assumptions, verification results, failure class, and next step in its attempt history, then distinguishes missing evidence, stale plans, wrong scope, and implementation errors before retrying.
- **Project initialization prepares context.** Project initialization begins preparing project records and installation.

## 2.4.1 - 2026-06-21

**Cursor's manual global setup became easier to complete.**

- **Cursor rules can be copied.** `./install.sh cursor-policy-copy` copies the Cursor User Rules text, and readiness checks call out the required paste.

## 2.4.0 - 2026-06-21

**Natural-language requests reach the needed Teamwork capability while simple work stays light.**

- **Natural language reaches the right capability.** Everyday wording maps more consistently to research, diagnosis, planning, execution, review, Goal, initialization, or update.
- **Guidance loads on demand.** Small tasks stay close to the host's fast path, while larger tasks load only the guidance they need.

## 2.3.0 - 2026-06-21

**Bug reports collect root-cause evidence before a fix is chosen.**

- **Root-cause evidence is collected completely.** `teamwork-debug` gathers reproduction, logs, hypotheses, and runtime evidence, separates cause from symptom, and cleans up temporary probes.
- **Update remote detection is fixed.** Upstream-remote detection in `scripts/check-update.sh` is corrected.

## 2.2.0 - 2026-06-16

**Installation freshness became directly checkable.**

- **Installation state is visible.** `scripts/check-update.sh`, version markers, `--project-root`, and broader project installation support make platform state visible.
- **Three-platform content and docs align.** Installation contents and documentation begin tracking the same multi-platform surface.

## 2.0.0 - 2026-06-16

**Clear requests move forward with fewer interruptions.**

- **Action comes first.** Teamwork asks about blockers and core decisions, keeps delegation rules focused, and avoids ceremony around ordinary work.
- **Installation still avoids incomplete content.** Platform installs remain protected from incomplete package content.

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

**Skills load progressively, so simple requests use less context.**

- **Skills load progressively.** Simple requests use less context, and deep research returns only useful evidence to the main conversation.
- **Updates and current lookups improve.** Installation updates and then-current library and API documentation lookups become more capable.

## 1.5.0 - 1.10.0 - 2026-06-05

**Teamwork gained cross-session collaboration, safer decision boundaries, and completion checks.**

- **Durable context became safer.** Long-running work can keep important context across sessions; external-memory import became more careful, while clarification boundaries, multi-role evidence requirements, and project initialization protection strengthened.
- **Missing required values fail clearly.** Required values do not become guessed defaults, while reviewability is preserved and process overhead is reduced.

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

**Codex installation gained cost and performance preferences.**

- **Installation preference controls subagent defaults.** `performance-first` and `cost-first` set subagent defaults for the selected preference.

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

**The multi-role collaboration skeleton took shape.**

- **Responsibilities and handoffs became separate.** Research, implementation, acceptance, and delegated handoffs became separate responsibilities, making complex work easier to close.

## 0.14.0 - 2026-06-01

**Codex Teamwork authorization became reusable across projects.**

- **Authorization can be reused across projects.** Codex Teamwork authorization installs once globally instead of being repeated in every project.

## 0.13.0 - 2026-05-31

**Codex parallel delegation gained clearer authorization boundaries.**

- **Parallel dispatch boundaries became clearer.** Subagent authorization rules make parallel work safer to dispatch and reduce delegation outside authorized scope.

## 0.12.0 - 2026-05-28

**Claude Code became a first-class Teamwork platform.**

- **Claude Code support landed end to end.** Teamwork gained Claude Code installation, guidance, and role support.

## 0.11.0 - 2026-05-27

**Cursor became a first-class Teamwork platform.**

- **Cursor support landed end to end.** Teamwork gained Cursor installation, documentation, subagent collaboration, and long-running Goal support, described according to platform capabilities.

## 0.10.0 - 2026-05-27

**Teamwork checks capabilities before dispatching or accepting delegated work.**

- **Capabilities are checked before fresh acceptance.** It verifies dispatch options instead of declaring subagents unavailable early, and independent acceptance must come from fresh context.

## 0.9.0 - 2026-05-27

**Teamwork became an installable, versioned collaboration package.**

- **The installable package foundation took shape.** `teamwork-init` added project initialization; research, planning, implementation, review, Goal, initialization, and update became focused capabilities alongside automatic routing, durable records, and evidence-based review.

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

**Teamwork grew from one optimization prompt into a collaboration system.**

- **Collaboration capabilities split over time.** Research, planning, implementation, review, and long-running goals became separate capabilities, with evidence checks, durable plans and records, Goal commands, and Codex routing added over time.
