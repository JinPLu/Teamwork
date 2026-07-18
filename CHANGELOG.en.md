# Changelog

[中文](CHANGELOG.md)

This changelog explains what changed for users. Maintainer details belong in Git history.

## 3.4.2 - 2026-07-19

**Every user-facing document now leads with the outcome—and gets there faster.**

- Before: older changelog entries still read like engineering records, while the README and platform guides repeated internal workflow detail. After: all 44 historical releases begin with what users notice and keep only useful Before → After context, responsible subskills, upgrade actions, and material limits.
- The README now answers what Teamwork helps you accomplish and how to start quickly. The Codex, Cursor, and Claude Code guides keep only the setup, manual steps, everyday use, and troubleshooting specific to each host. Marketplace descriptions now explain the user benefit in a few sentences.
- Future public docs follow the same rule: brevity first, user outcome first, and internal architecture or maintenance detail only when it changes an action, boundary, or expectation.
- Codex Marketplace setup no longer recommends pinning one release tag. Before: `upgrade` could only refresh that same tag and could not advance to a newer release. After: remove the old `teamwork` Marketplace and add unpinned `JinPLu/Teamwork` once; future updates can advance normally. This fix is owned by `teamwork-update`.
- To upgrade: users on 3.4.1 need no update for existing capabilities. To fix future Marketplace updates, follow the README update sequence once to replace the pinned Marketplace.

Limit: shorter docs do not make natural-language skill selection deterministic. The host and model still choose which skill runs. After replacing the Marketplace, start a new task and invoke `$teamwork-update`.

## 3.4.1 - 2026-07-19

**Release notes now explain the experience first.**

The 3.4.0–3.1.0 entries now lead with what users notice, add a useful Before → After comparison, and name the responsible workflow only after the story. Future entries follow the same style.

This is documentation-only: Teamwork runtime behavior did not change. No upgrade is needed, and users on 3.4.0 gain no new runtime capability.

Limit: a named subskill explains the source of a change, but the host and model still decide which skill a natural-language request invokes.

## 3.4.0 - 2026-07-18

**Codex can install Teamwork in one step.**

- Before → After: Codex users no longer need a repository checkout to install all ten skills. Add `JinPLu/Teamwork@v3.4.0`, install `teamwork-skill@teamwork`, then invoke `$teamwork-update` in a new task. After approval, `teamwork-update` enables agents, routing, policy, and optional notifications together.
- Marketplace skills run from the plugin cache. Full configuration remains separately confirmed; only verified legacy Teamwork skills are removed, and Teamwork does not create `~/.agents/skills` copies.
- `grill-me` and the discussion workflow can save an explicit resume request, handoff, clear open comparison, or genuinely branching discussion. Clear authorized work still goes straight to `teamwork-execute`, which checks only the changed path or a named boundary.
- To upgrade in Codex: run `codex plugin marketplace add JinPLu/Teamwork@v3.4.0`, then `codex plugin add teamwork-skill@teamwork`; start a new task and invoke `$teamwork-update`. Checkout users may keep using `./install.sh all` and `./scripts/check-update.sh --readiness` during 3.4.x. Cursor and Claude Code installation did not change.

Limit: plugin installation does not silently rewrite user configuration or auto-trust hooks. Restart Codex after full activation. If notifications are enabled, trust only Teamwork `Stop` and `PermissionRequest` in `/hooks`. Malformed discussion history fails closed. Installation checks cannot guarantee a particular skill selection or identical runtime behavior across platforms.

## 3.3.0 - 2026-07-16

**Teamwork finishes the task before adding checks.**

- Before → After: a clear change or run request no longer expands automatically into research, planning, testing, review, and reporting. `teamwork-execute` takes the shortest real path, verifies the current blocker, changed path, or named high-risk boundary, then stops when the result exists.
- Natural requests such as “ask me first,” “find the cause,” and “continue with the accepted approach” route more reliably through `using-teamwork` to discussion, research, diagnosis, or execution.
- Replies lead with the conclusion and keep only decision-relevant support. `grill-me` records a discussion only when you explicitly ask to discuss first, the project is initialized, and there is something useful to resume; a plan alone creates no discussion record.
- `teamwork-update` refreshes global Teamwork, while `teamwork-init` owns one project’s instructions and context. Unsafe legacy cleanup stops before the new location is changed.
- To upgrade: run `./install.sh all`, then `./scripts/check-update.sh --readiness`. For full context and discussion records in an existing project, also run `./install.sh --project-root "<project-path>" init-project`.

Limit: the host model still chooses whether to invoke a skill. These rules do not bypass release, migration, permission, security, or destructive-operation boundaries, and Cursor User Rules still require the prompted manual paste.

## 3.2.0 - 2026-07-16

**Discussion sounds more natural and resumes at the right question.**

- Before → After: replies no longer foreground internal labels, version detail, invented terms, or repeated caveats. Shared `using-teamwork` rules connect the conclusion, evidence, interpretation, and only the boundary that affects the decision, while keeping observation separate from inference.
- When `grill-me` settles one point but leaves one clear comparison, measurement, or decision open, it saves a compact continuation record first and tells you where the conversation resumes.
- To upgrade: run `./install.sh all --profile gpt56-role`, then `./scripts/check-update.sh --readiness`. Cursor User Rules still require the prompted manual paste; projects do not need Teamwork package copies.

Limit: this is not an academic-writing feature and adds no academic-writing dependency. Offline checks and one isolated Codex run do not guarantee identical reply quality or Cursor/Claude Code parity.

## 3.1.1 - 2026-07-15

**No update is needed: Teamwork behaves exactly as in 3.1.0.**

This patch records the already accepted evidence and limits for discussion continuity, audience-first replies, and safer initialization. Runtime behavior and all subskills are unchanged; existing projects need no Teamwork package copies.

Limit: the record covers offline evaluation, package validation, and one isolated Codex scenario, not real host compaction or Cursor/Claude Code parity.

## 3.1.0 - 2026-07-15

**An interrupted discussion can pick up where it left off.**

- Before → After: long or branching `grill-me` sessions keep one compact summary of the goal, settled choices, open question, key evidence, and continue point. A new session does not re-ask settled choices, and short discussions still create no file.
- Replies put the point first and omit process detail that does not change a decision.
- `teamwork-init` recovers under the project lock and rejects unknown files, malformed journals, and reused temporary resources instead of trusting partial state.
- To upgrade: run `./install.sh all`, then `./scripts/check-update.sh --readiness`. Projects need no package copies; use `./install.sh --project-root "<project-path>" init-project` only to refresh project context.

Limit: one isolated Codex scenario was run. Fresh-thread recovery was not a host compaction test and did not establish Cursor or Claude Code parity.

## 3.0.0 - 2026-07-15

**Replies are more direct, and project setup is simpler.**

- Replies now begin with the conclusion, why it matters, and the next step instead of versions, stages, invented labels, or repeated caveats.
- Eligible long discussions, handoffs, and material branches can keep a route map and Playback when Teamwork has write authority. Without it, Teamwork returns only a checkpoint candidate. Ordinary replies do not become engineering records, and internal rule changes must still name their owner, user effect, and verification.
- Before → After: the removed `project`, `project-codex-agents`, and `check-update --project` routes no longer copy skills or agents into projects. `init-project` refreshes global Teamwork and writes only project instructions, memory, and CodeGraph context.
- To upgrade: run `./install.sh all`, then `./scripts/check-update.sh --readiness`. Initialize context with `./install.sh --project-root "<project-path>" init-project`. Remove only confirmed Teamwork-generated legacy assets, never whole `.agents`, `.codex`, `.cursor`, or `.claude` directories.

Limit: offline package and installer checks support these changes. No paid or live model comparison established better answer quality or cross-platform runtime parity.

## 2.22.0 - 2026-07-15

**Teamwork became leaner and more portable without weakening its boundaries.**

- Shared guidance stopped being repeated across global rules, skills, agents, and project setup; each stage kept its responsibility, and simple work stayed direct.
- Public-package checks reject real home paths, session IDs, private network addresses, credential-shaped values, and force-tracked private artifacts while allowing explicit public transports and synthetic examples.
- New projects receive a compact Teamwork block and header-first index. Complete legacy indexes remain compatible and reruns preserve content byte for byte; partial hybrid layouts are rejected.
- Maintainers can compare prompt alternatives blind on fixed cases without publishing raw model output. Instruction size breaks only a complete tie, and this did not add a step to ordinary work.
- Historical 2.22.0 upgrade: run `./scripts/check-update.sh --readiness --project "$PWD"`, execute the printed `NEXT`, and repeat until `INSTALL_READY=yes`; paste Cursor User Rules when prompted. Version 3.0.0 later removed these project-local routes, so current users should follow 3.0.0 above.

Limit: offline package, installer, privacy, and comparison checks did not prove better live answers or cross-platform runtime parity.

## 2.21.1 - 2026-07-15

**Everyday behavior did not change; installed Codex runs became easier to inspect privately.**

Install, evaluation, and validation commands and outputs stayed the same. Maintainers gained an optional small-sample installed-run check using a private temporary home and retaining only a redacted summary. Teamwork runtime behavior did not change.

Historical 2.21.1 upgrade: run `./scripts/check-update.sh --readiness --project "$PWD"`, execute `NEXT`, and repeat until `INSTALL_READY=yes`; no new configuration was required, though Cursor User Rules still needed the manual paste. Version 3.0.0 later removed project-local update routes.

Limit: the sample did not show better ordinary answers, broad reliability, automatic activation, or cross-platform parity.

## 2.21.0 - 2026-07-15

**Long discussions could preserve their important decisions.**

- Long, cross-context, or branching `grill-me` sessions could save a `discussion/` artifact with a flowchart, keyed notes, and Playback. Research still owned evidence, and Plan still owned executable scope.
- Ordinary discussions created no file. Saved records captured material checkpoints, not transcripts, and never granted execution authority; without write permission, Teamwork returned only a candidate and warned that continuity was not guaranteed.
- `teamwork-init` preserved human-written docs, trackers, and custom content. `teamwork-update` refreshed installed files but could not publish a release without an explicit maintainer request.
- Historical 2.21.0 upgrade: run `./scripts/check-update.sh --readiness --project "$PWD"`, execute `NEXT`, and repeat until `INSTALL_READY=yes`; paste Cursor User Rules when prompted. Version 3.0.0 later removed project-local update routes.

Limit: offline scenarios did not prove perfect discussion understanding, compaction recovery, or cross-platform parity.

## 2.20.0 - 2026-07-14

**Simple changes stopped accumulating unnecessary code.**

- Work begins in the code that owns the behavior; wrappers, extra modes, fallbacks, duplicate modules, abstractions, and dependencies need a real requirement. Appropriate multi-file changes and tests remain welcome.
- One project install then prepared all ten skills for Codex, Cursor, and Claude Code while preserving unrelated content. Version 3.0.0 later removed project-local packages.
- Update checks named the platform and whether skills were missing, stale, or different. Unaccepted, superseded, or inapplicable plans no longer directed execution.
- Historical 2.20.0 upgrade: run `./scripts/check-update.sh --readiness`; add `--project <project-path>` for a project, execute `NEXT`, and repeat until `INSTALL_READY=yes`. Version 3.0.0 later removed these project routes.

Limit: these safeguards did not guarantee minimal model output or complete cross-platform runtime behavior.

## 2.19.0 - 2026-07-13

**Full setup could add completion and permission sounds automatically.**

`install.sh all` and `init-project` installed Codex and Claude Code sounds by default; direct platform installs stayed opt-in, and `--no-notifications` removed only Teamwork handlers. Readiness checks reported Codex hooks as trusted, review-required, or unverifiable and supplied a `/hooks` action when needed. `teamwork-init` and `teamwork-update` verified the exact notifier and trusted `Stop` and `PermissionRequest` separately—never trust-all or unrelated hooks.

Limit: the sound path was verified live only on macOS.

## 2.18.0 - 2026-07-13

**Teamwork asks only when the answer truly belongs to you.**

- It inspects evidence first, asks only for missing user input or a material decision, and pauses only the dependent branch. Ordinary clarification does not require `grill-me`; subagent question candidates are rechecked and deduplicated by the root agent.
- The detailed task records from 2.17 were replaced by the minimum safe working facts: goal, scope, acceptance, authority, blockers, and stop conditions.
- Reviews still separate blockers from optional follow-ups, allow one focused recheck, and retry only affected Goal branches. Entering Codex Goal state still requires an explicit request or accepted proposal.
- A release without its tag or GitHub Release is called release-ready, never released. Ordinary users need no action.

Limit: offline three-platform checks and limited Codex evidence did not prove every question, natural deduplication, or cross-platform runtime parity.

## 2.17.0 - 2026-07-13

**Complex plans and reviews converge instead of restarting forever.**

- Non-simple planning checks evidence, asks one genuinely user-owned question at a time with a recommendation, and shows a short Decision Summary.
- Independent review gets one full pass and one focused follow-up. After fixes, the same reviewer rechecks the original findings and any fix-caused regressions. Only failed acceptance, protected-boundary breaches, regressions, or missing required evidence block completion; preferences do not.
- Known fixes return to implementation, unknown causes to diagnosis, and scope changes to planning. Progress updates mention only new decisions, blockers, verification, and completion.
- Larger tasks temporarily used versioned records; 2.18 replaced them with lighter working facts. Versions 2.17 and 2.18 also replaced 2.16’s fixed question count and explicit discussion status.

Limit: Plan and Review remained available, Codex role tiers were not lowered, and the release did not promise to remove GPT-5.6 Sol/high single-call latency.

## 2.16.0 - 2026-07-13

**Guided discussion became discoverable, and Codex subagents used their configured models.**

- `grill-me` asked zero to three outcome-changing questions and never manufactured questions about reversible details. It kept an explicit active/closed state, and silence never granted permission to implement. Versions 2.17–2.18 later replaced these rules.
- Codex subagents used the installation profile’s model and effort instead of inheriting the main thread’s effort. Capacity became nine threads: one main plus eight subagents; project-only installs left user configuration untouched, with an opt-out.
- Users had to restart Codex to load the routing change. It received a limited Codex 0.144.0 check; cross-platform discussion behavior was checked only offline.

## 2.15.0 - 2026-07-13

**Long work became less likely to drift, with optional sounds for attention.**

Corrections invalidate stale delegated work, and partial or unverified results remain visibly incomplete. Optional Codex sounds notify only for the main task; background tasks stay silent. Read-only diagnostics reveal agent setup and unusually long tasks without conversation text.

Limit: sounds were tested on macOS; Claude Code was unverified and Cursor unsupported.

## 2.14.0 - 2026-07-11

**Installation profiles gained refreshed model choices across all platforms.**

Codex `performance-first` used GPT-5.6 Terra/Sol, `cost-first` used Luna/Terra/Sol, and new `gpt56-high`/`gpt56-xhigh` profiles pinned all roles to Sol. Compatibility names `gpt56-role`, `gpt55-high`, and `gpt55-xhigh` remained, but no profile called GPT-5.5. Cursor used Composer 2.5, Sonnet 4.6, and Opus 4.8 mappings, with non-Fast Composer for `cost-first`; Claude Code used `haiku`, `sonnet`, and `opus`, with Deep roles at `max`. Copy, link, global, and then-current project installs shared these mappings; 3.0.0 later removed project-local packages.

## 2.13.0 - 2026-07-10

**Simple tasks stayed direct while risky work kept stronger controls.**

Well-specified tasks no longer required hypothesis lists, tables, durable records, or independent review. User questions, test-first work, alternatives, memory, and fresh review activate only when risk justifies them. Shorter shared instructions reduce repeated process across platforms. Codex `gpt56-role` assigns models and effort by job, and an unavailable pinned model or effort fails clearly instead of silently downgrading.

Release history: `2.12.0` was not released separately; its role-tiering features shipped in `2.13.0`.

## 2.11.1 - 2026-07-08

**Small fixes stayed fast, but “discuss first” could no longer be ignored.**

One-line changes still need no extra questions, subagents, or durable plan. An explicit request for `grill-me`, discussion, or challenged assumptions pauses even small work, and unanswered material install/update decisions stop progress. Maintainer checks guard against unnecessary questions, plans, and delegation without adding any ordinary-user action.

## 2.11.0 - 2026-07-08

**Material decisions were confirmed consistently, and stale installs became visible.**

Complex work checks evidence before returning only genuinely user-owned decisions with a recommendation; the same confirmation boundary holds throughout the task. Ordinary work avoids unnecessary interviews, though offline evidence did not prove live behavior. `check-update.sh` compares content as well as versions across global and then-current project installs. Historical project commands and profile examples became runnable, and `gpt55-high` could pin Codex subagents to GPT-5.5/high; 3.0.0 later removed project-local routes.

## 2.10.0 - 2026-07-08

**Prompt changes became comparable without changing everyday Teamwork behavior.**

Maintainers could run old and candidate behavior on the same tasks, record model, configuration, verification, rollback, and independent review, and retain accepted or rejected outcomes. This added no user-facing workflow stage: runtime behavior for ordinary tasks did not change, and users needed no action.

Limit: the comparison machinery did not itself prove a real-world optimization.

## 2.9.0 - 2026-07-08

**Release checks became reusable without changing everyday Teamwork behavior.**

Maintainers gained offline cases for simple and complex work, debugging, research, review, goals, installation, and platform boundaries, plus recorded acceptance or rejection. These checks added no stage to ordinary runtime behavior and required no user action.

Limit: offline consistency did not prove actual Codex, Cursor, or Claude Code behavior.

## 2.8.1 - 2026-07-08

**“Discuss first” and maintainable-code rules now apply during implementation.**

A discussion request pauses dependent conclusions, choices, edits, and delegation. Changes begin in the existing implementation, and review rejects guessed defaults, unsupported branches, wrappers, and fallbacks. Freshness checks detect stale skills, agents, or global policy across Codex, Cursor, and Claude Code.

## 2.8.0 - 2026-07-08

**An explicit request to be grilled now pauses dependent work.**

When you say “grill me,” “ask first,” or “challenge assumptions,” Teamwork asks at least one outcome-changing question with a recommendation. Dependent root, delegated, and Goal work waits until you answer or opt out. Content-aware update checks catch stale rules even when versions match, and the same boundary applies across all three platforms.

## 2.7.1 - 2026-07-07

**Code changes and reviews became more direct and maintainable.**

Teamwork changes the existing owner instead of adding a parallel implementation without evidence. Reviews reject unsupported modes, wrappers, fallbacks, guessed defaults, and hidden missing state. All three platforms fail clearly when required state is absent and add alternatives only when accepted behavior requires and verifies them.

## 2.7.0 - 2026-07-01

**Codex gained a quality-first profile, and replies became less rushed.**

`gpt55-xhigh` set every Codex subagent to GPT-5.5 with `xhigh` reasoning; Cursor and Claude Code kept native performance-first tiers. The historical `project-codex-agents` target refreshed only project `.codex/agents` and was removed in 3.0.0. Evidence-sensitive work reads, interprets, and verifies before answering; progress stays tied to decisions, blockers, or checks. Routine replies hide internal routing labels, while important delegation, review, and skipped actions remain traceable.

## 2.6.0 - 2026-06-23

**Research looks beyond the first source, and missing values are no longer guessed.**

A supplied paper, URL, repository, or report is a starting point: `teamwork-research` seeks primary and neighboring sources, counter-evidence, gaps, and open questions before recommending. Missing paths, ports, models, hyperparameters, credentials, configuration, or invariants cause a question, research, or stop—not an invented default. Review flags unnecessary code, broad error handling, silent defaults, hidden fallbacks, and regressions. Public guides became outcome-first, and all three global policies share these safety rules.

Limit: offline checks and limited runtime evidence did not prove equivalent behavior across Codex, Cursor, and Claude Code.

## 2.5.0 - 2026-06-22

**Long-running Goal work stopped retrying failures blindly.**

Goals retain enough attempt history to continue safely, and a failure is classified as missing evidence, stale plan, wrong scope, or implementation error before retrying. The historical `scripts/init-project.sh` also prepared project context and a project-local package; 3.0.0 later removed project-local installation.

## 2.4.1 - 2026-06-21

**Cursor’s required manual setup became harder to miss.**

`./install.sh cursor-policy-copy` copies the Cursor User Rules text to the clipboard, and readiness checks call out the required paste. Teamwork runtime behavior did not change.

## 2.4.0 - 2026-06-21

**Natural-language requests route more reliably while simple work stays light.**

Everyday wording maps more consistently to the needed Teamwork capability. Small tasks stay close to the host’s native fast path, while larger tasks load only the guidance they need.

## 2.3.0 - 2026-06-21

**Bug reports now produce evidence before guessed fixes.**

The new `teamwork-debug` uses reproduction, logs, competing explanations, and runtime evidence. It separates root cause, symptoms, and unsupported conclusions, and removes temporary probes afterward. This release also fixed upstream-remote detection in `scripts/check-update.sh`.

## 2.2.0 - 2026-06-16

**Installation freshness became directly checkable.**

`scripts/check-update.sh` reports stale installs. Version markers, `--project-root`, and broader project-local support made behavior more consistent across platforms; 3.0.0 later removed project-local package installation.

## 2.0.0 - 2026-06-16

**Clear requests move forward with fewer interruptions.**

Teamwork asks only about blockers or core decisions, applies delegation rules consistently without burdening ordinary work, and keeps package-integrity checks lean. Users needed no action for the maintenance checks.

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

**Skills load progressively, and deep research returns a smaller useful context.**

`teamwork-update` refreshes more of the installed package. Detailed guidance loads only when needed, broad research returns only its best evidence to the main conversation, and an optional lookup policy supports then-current library and API information.

## 1.5.0 - 1.10.0 - 2026-06-05

**Teamwork gained durable context and safer decision boundaries.**

Project memory lets important work survive sessions. External memory is imported carefully, consequential choices require confirmation, and missing required state stops clearly instead of producing a guessed default. Later releases reduced the overhead without removing reviewability.

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

**Codex users could choose cost or performance at installation time.**

The new `performance-first` and `cost-first` profiles set subagent defaults to match that choice.

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

**Teamwork established reliable routing and clearer delegated handoffs.**

Requests reach the right kind of help more consistently, while ownership and completion expectations help delegated work finish cleanly.

## 0.14.0 - 2026-06-01

**Codex authorization became reusable across projects.**

A managed Teamwork block in `~/.codex/AGENTS.md` means users no longer repeat subagent permission in every project.

## 0.13.0 - 2026-05-31

**Codex users gained clearer boundaries for parallel delegation.**

Work could be distributed across subagents with more explicit authorization.

## 0.12.0 - 2026-05-28

**Claude Code became a first-class Teamwork platform.**

Teamwork added installation, documentation, subagent support, and package checks for Claude Code.

## 0.11.0 - 2026-05-27

**Cursor became a first-class Teamwork platform.**

Teamwork added Cursor installation, documentation, subagent mappings, and long-running Goal guidance, using platform-specific terms instead of assuming Codex behavior.

## 0.10.0 - 2026-05-27

**Teamwork checks available capabilities and requires genuinely independent acceptance.**

It no longer declares subagents unavailable before checking dispatch options. Larger tasks cannot treat self-review as independent acceptance, and skipping an independent reviewer must be explained.

## 0.9.0 - 2026-05-27

**Teamwork became an installable, versioned workflow package.**

It gained repeatable installation, `teamwork-init`, focused on-demand skills, automatic routing, durable records, and evidence-based review for larger work.

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

**Teamwork grew from one optimization prompt into a collaboration system.**

Research, planning, implementation, review, and long-running goals became separate capabilities. Evidence checks, durable plans, Goal commands, and automatic Codex routing enabled reliable continuation. The package was renamed Teamwork, became Codex-first, and later expanded to multiple platforms.
