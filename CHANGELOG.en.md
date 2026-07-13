# Changelog

[中文](CHANGELOG.md)

This changelog lists user-visible changes. Implementation details live in Git commits or pull requests.

## 2.17.0 - 2026-07-13

**Directly addresses plans that get reviewed over and over yet still take hours to converge.**

- **Important decisions align earlier.** A non-simple Plan inspects repository and configuration evidence first, then asks one genuinely user-owned question at a time with a recommendation. A short Decision Summary appears before the final Plan, reducing late discovery that the task was heading in the wrong direction.
- **Review no longer restarts indefinitely.** A task that needs independent acceptance gets at most one full review. After fixes, the same Reviewer performs one delta recheck limited to the original findings, declared fixes, and fix-introduced regressions instead of rescanning everything and opening another review cycle. Simple tasks may still self-verify directly.
- **No blocker means a clear finish.** Only a failed accepted criterion, protected-boundary breach, regression, or missing gating evidence can be a `BLOCKER`. Preferences, opportunistic improvements, and out-of-scope ideas remain visible without keeping the task permanently unaccepted.
- **Fixing one problem no longer restarts from Plan.** Known fixes return directly to Execute; unknown causes return to Debug; only a user-accepted scope change returns to Plan. Failed verification reruns only the affected stage.
- **The target cannot silently move during execution.** For non-simple, multi-stage Teamwork work, Plan, Execute, Review, and Goal inherit one versioned Task Contract with stable acceptance criteria. Every scope change must be explicit and versioned. Simple tasks do not need this contract.
- **The conversation is quieter.** Progress updates report only new decisions, blockers, verification results, and completion rather than repeatedly restating the plan or announcing another review.

Plan and Review have not been removed, and Codex role-model tiers have not been lowered. This release reduces workflow repetition, rework, and convergence time; it does not promise to eliminate GPT-5.6 Sol/high single-call latency. Compared with 2.16, this release removes the fixed zero-to-three question count and active/closed status ceremony in favor of asking only when a question is valuable; the 2.16 entry below records the historical behavior at that time.

## 2.16.0 - 2026-07-13

**Adds a discoverable `grill-me` interaction and fixes Codex subagent role-model routing.**

- `grill-me` is now a standalone skill that asks zero to three genuinely outcome-changing, user-owned questions. Reversible details such as language, file count, naming, and internal layout are not used to manufacture questions.
- Multi-turn grills keep explicit active/closed state. Stop, proceed, delegated judgment, and task replacement follow the user's authority; exhausting useful questions never grants implementation permission.
- Codex install, init, and update atomically migrate custom-agent routing so Explorer, Worker, Reviewer, and other roles use their configured model and effort instead of inheriting the root thread's reasoning tier.
- The Codex session limit is now 9 threads: one main thread plus up to eight subagents. Project-only installs still leave user-level config untouched, and an explicit opt-out remains available.
- Codex 0.144.0 was live-tested with eight overlapping Terra/medium Explorers and a fresh Sol/high Reviewer. Restart Codex before new tasks can load the routing change; cross-platform grill behavior remains static/offline-verified rather than claimed live.

## 2.15.0 - 2026-07-13

**Long tasks are less likely to drift and can play a sound when finished or
waiting for your attention.**

- Reduces duplicate collaboration and invalidates outdated work after corrections.
- No longer reports partial or unverified work as full completion.
- Optional Codex sounds notify only for the main task; background tasks stay silent.
- Read-only diagnostics help inspect agent setup and unusually long tasks without exposing conversation text.
- Sounds were tested on macOS; Claude Code remains unverified and Cursor is unsupported.

## 2.14.0 - 2026-07-11

This release **refreshes subagent model mappings for every platform and every
profile**.

- Codex `performance-first` uses GPT-5.6 Terra/Sol; `cost-first` uses
  Luna/Terra/Sol; new `gpt56-high` and `gpt56-xhigh` profiles pin all roles to
  Sol.
- `gpt56-role`, `gpt55-high`, and `gpt55-xhigh` remain compatibility names, but
  no Codex profile calls GPT-5.5 anymore.
- Cursor uses current native Composer 2.5, Sonnet 4.6, and Opus 4.8 mappings,
  with non-Fast Composer 2.5 for `cost-first`. Claude Code uses current
  `haiku`/`sonnet`/`opus` aliases and moves Deep roles to `max`.
- The installer, source templates, drift checker, platform docs, project-init
  guidance, and validation now agree across copy/link and global/project
  installs.

## 2.13.0 - 2026-07-10

This release is about **keeping quality for complex work without burdening simple tasks**.

- Well-specified tasks proceed directly instead of being forced to list hypotheses, draw tables, create durable records, or start independent review merely to satisfy a template.
- Only decisions that materially change the outcome and genuinely belong to the user interrupt progress. Test-first work, alternatives, durable memory, and fresh review now activate according to risk.
- Core collaboration instructions are substantially shorter across all three platforms, reducing the context spent rereading and restating process.
- Codex adds the role-tiered `gpt56-role`: Explorer uses Terra/medium, Worker uses Sol/medium, design and acceptance roles use Sol/high, and a few deep acceptance tasks use Sol/max instead of every role inheriting one high reasoning tier.
- When a model or reasoning tier is explicitly pinned but unavailable, the run fails clearly instead of silently switching models or lowering effort.

`2.12.0` was not released separately; the role-tiering capabilities shipped as part of `2.13.0`.

## 2.11.1 - 2026-07-08

This release is about **keeping small tasks direct without ignoring an explicit “ask me first” request**.

- Lightweight work such as a one-line fix still completes directly without extra questions, subagents, or durable plans.
- If you explicitly request `grill-me`, discussion first, or challenged assumptions, that instruction wins even when the task is small.
- Install and update work no longer continues past an unanswered material decision, preventing maintenance actions from bypassing confirmation.
- New lightweight regressions prevent future releases from reintroducing unnecessary questions, plans, or delegation.

## 2.11.0 - 2026-07-08

This release is about **confirming outcome-changing decisions first and making stale installs easier to detect**.

- For complex or uncertain work, Teamwork inspects repository and configuration evidence first, then brings back only unresolved user decisions with a recommendation.
- Research, Debug, Plan, Execute, Review, and Goal use the same confirmation boundary so one stage cannot keep acting after another promised to wait.
- Dedicated simple-task controls prevent ordinary requests from turning into unnecessary interviews. These offline checks are not presented as proof of live platform behavior.
- `check-update.sh` can detect actual global and project skill/agent content drift instead of comparing version numbers alone.
- Project update commands and profile examples are directly runnable, and a new `gpt55-high` option can pin Codex subagents to GPT-5.5/high.

## 2.10.0 - 2026-07-08

This release is about **making prompt optimization repeatable instead of subjective**.

- Maintainers can run the previous and candidate behavior on the same tasks before deciding whether to accept a change.
- Every candidate must record its model, configuration, verification, rollback path, and independent review instead of showcasing only the best output.
- Accepted and rejected candidates remain recorded so failed directions are not rediscovered and repeated later.
- The optimization tooling is limited to Teamwork maintenance and does not add another stage to ordinary user tasks.
- This release provides verifiable optimization infrastructure; it does not claim that Teamwork has already completed an automatic real-world optimization run.

## 2.9.0 - 2026-07-08

This release is about **giving Teamwork's own behavior upgrades reusable regression checks**.

- New cases cover simple tasks staying lightweight, complex coding, debugging, research, review, long-running goals, and cross-platform boundaries.
- The checks run fully offline without model calls, so maintainers can quickly catch accidentally broken rules or install assets.
- Behavior releases now require development evidence, a release audit, and recorded acceptance or rejection instead of shipping because a change merely looks good.
- Evaluation governs Teamwork maintenance only; it does not become a new stage in ordinary user work.
- Offline checks prove consistency with the recorded cases, not real Codex, Cursor, or Claude runtime behavior.

## 2.8.1 - 2026-07-08

This release is about **making “discuss first” and code-quality rules apply during execution, not only in planning**.

- When you ask to discuss first, dependent conclusions, direction choices, edits, and delegation wait for confirmation instead of only pausing code generation.
- Before editing code, Teamwork identifies the existing owner, control flow, tests, and configuration, reducing parallel implementations in the wrong place.
- Reviewers check unsupported branches, defaults, and fallback paths so a fix does not create more maintenance burden.
- Update checks can detect stale installed skills, agents, or global policy.
- Codex, Cursor, and Claude Code share the same confirmation and code-maintenance boundaries.

## 2.8.0 - 2026-07-08

This release is about **actually stopping to discuss when you explicitly ask to be grilled**.

- When you say grill me, ask first, or challenge assumptions, Teamwork asks at least one outcome-changing question and recommends an answer.
- Planning, implementation, long-running Goal work, and Worker delegation wait until you confirm or explicitly exit.
- Debug, Plan, Execute, Review, and Goal share the same pause rule, preventing background action after a promise to discuss first.
- Update checks begin comparing installed skill content, detecting cases where the version matches but the rules are still stale.
- Codex, Cursor, and Claude Code global installs share this interaction boundary.

## 2.7.1 - 2026-07-07

This release is about **keeping code edits and reviews concise, clear, and maintainable**.

- Execution and review now explicitly require understanding the existing owner,
  control flow, tests/config, and invariants before changing or accepting code.
- Workers and Reviewers push back harder on unevidenced branch, mode, wrapper, or
  fallback accumulation, guessed defaults, and defensive masking of missing state.
- Codex, Cursor, and Claude Code global policies now share the code-maintenance
  rule: prefer changing/deleting the current path; add branches or fallback only
  when accepted behavior requires and verifies them; fail fast when state is absent.

## 2.7.0 - 2026-07-01

This release is about **letting Codex explicitly maximize reasoning while reducing rushed answers and performative progress updates**.

- Added the `gpt55-xhigh` profile so quality-first Codex installs can render every
  Teamwork Codex subagent as `gpt-5.5` with `xhigh` reasoning; Cursor and Claude
  Code keep their native performance-first model tiers.
- Added the `project-codex-agents` target for refreshing only project-local
  `.codex/agents`, without touching Cursor or Claude Code project surfaces.
- Added Codex global think-first reasoning discipline: non-lightweight or
  evidence-sensitive work should not optimize for fast visible output over source
  reading, interpretation checks, and verification; optional progress narration
  should stay brief and tied to decisions, blockers, or verification.
- Tightened the shared workflow contract so routine route choices do not need gate
  labels, while material dispatch, review, and skipped actions remain auditable.
- Updated README, CODEX, init guidance, dispatch references, and validation to
  cover the new profile, project-local Codex agent target, and
  reasoning/commentary policy.

## 2.6.0 - 2026-06-23

This release is about **stronger rules, broader research, and clearer open-source product docs**.

- Research no longer treats a user-provided article, paper, URL, repo, or report as
  the boundary. Teamwork now treats it as a seed source, then expands toward primary
  sources, neighboring sources, counter-evidence, and still-uncovered questions.
- Design and planning now behave more like a research partner: check evidence
  coverage, counter-evidence, source quality, and open questions before
  recommending a direction or plan.
- Rules are stricter against fake success: when env vars, paths, ports, model names,
  hyperparameters, credentials, configs, or invariants are missing, the agent should
  ask, research, or block instead of inventing defaults or fallback behavior.
- Strict review and deslop are more useful: reviewers are guided to catch AI bloat,
  abnormal defensive branches, broad catches, silent defaults, fallback masking, and
  maintainability regressions.
- README, CODEX, CURSOR, CLAUDE, and changelog now read from the user's
  perspective: why to use Teamwork, when to use it, what improves, and where to
  find advanced platform details.
- Codex, Cursor, and Claude Code global policies now share the same safety baseline.

## 2.5.0 - 2026-06-22

This release is about **not blindly retrying long-running goals after failure**.

- Goal mode records each attempt's target, hypothesis, verification result, failure
  class, and next step so work can continue across turns.
- Failed attempts now trigger Replay Preflight and plan-adequacy checks before the
  next try, distinguishing missing evidence, stale plans, wrong scope, and execution drift.
- Added `scripts/init-project.sh` and improved project artifact defaults,
  structure, and project-local installation behavior.

## 2.4.1 - 2026-06-21

This release is about **making Cursor global-rule setup easier**.

- Added `./install.sh cursor-policy-copy` to copy Cursor User Rules policy text to
  the clipboard.
- Updated docs and readiness checks to make the manual Cursor User Rules paste step explicit.

## 2.4.0 - 2026-06-21

This release is about **more natural requests and better automatic routing**.

- Natural-language requests now map more reliably to research, debug, planning,
  execution, review, long-running goals, initialization, or updates.
- Simple tasks stay closer to the native fast path; larger tasks load only the
  stage and references they need.

## 2.3.0 - 2026-06-21

This release is about **diagnosing bugs before guessing fixes**.

- Added the `teamwork-debug` stage for logs, reproduction, hypotheses, and runtime
  evidence before implementation.
- Added debug, verification, and review lenses to separate root cause, symptoms,
  and insufficient proof.
- Added debug cleanup rules so temporary logs, probes, and touched-diff residue do
  not become new technical debt.
- Fixed upstream remote detection in `scripts/check-update.sh`.

## 2.2.0 - 2026-06-16

This release is about **making installs and updates checkable**.

- Added `scripts/check-update.sh` to check whether local skills, agents, policy,
  and project installs are stale.
- Added installed-version markers, `--project-root`, and broader project-local install support.
- Improved consistency across Codex, Cursor, and Claude Code agents, policy blocks,
  manifests, docs, and validation.

## 2.0.0 - 2026-06-16

This release is about **less interruption and more direct progress**.

- Consolidated Teamwork around act-by-default routing: proceed on clear tasks and
  ask only for real blockers or core decisions.
- Replaced scattered subagent rules with focused dispatch, contract, and role
  playbook references.
- Slimmed validation while keeping package layout, manifest, skill, memory,
  platform, and install-smoke checks.

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

These releases are about **progressive skills and context-efficient deep research**.

- Expanded `teamwork-update` package refresh behavior and validation coverage.
- Made skills load detailed rules only when the task needs them.
- Added research context budgets for Explorer and deep research packets so recall
  can stay broad while the main thread receives only useful evidence.
- Added optional docs MCP policy for current library/API documentation lookup.

## 1.5.0 - 1.10.0 - 2026-06-05

These releases are about **turning Teamwork from workflow prompts into a system with memory and acceptance**.

- Strengthened durable memory, clarification gates, evidence-first fallback positioning,
  and role fan-out guidance.
- Added full-feature memory and init gates plus external-memory promotion safeguards.
- Introduced fail-fast no-defaults guidance, then reduced workflow overhead while
  keeping reviewability.

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

These releases are about **letting users choose cost/performance profiles**.

- Added install-time Codex model profiles: `performance-first` and `cost-first`.
- Optimized Codex custom agent model defaults and strengthened Explorer, Designer,
  Worker, and other role workflows.

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

These releases are about **building the Teamwork collaboration skeleton**.

- Refined collaboration orchestration and stage responsibilities.
- Added delegated-track lifecycle closure contracts so subagents have clear packet
  and closure expectations.
- Updated Codex Worker model mapping.
- Added runtime README pointer guidance.

## 0.14.0 - 2026-06-01

This release is about **making Codex Teamwork authorization reusable globally**.

- Installed a managed Teamwork global policy block into `~/.codex/AGENTS.md`.
- Removed the need to repeat subagent authorization in every project.

## 0.13.0 - 2026-05-31

This release is about **tightening Codex subagent authorization**.

- Updated Codex subagent authorization policy so parallel-agent boundaries are clearer.

## 0.12.0 - 2026-05-28

This release is about **making Claude Code a first-class platform**.

- Added Claude Code parity with Claude plugin metadata, `CLAUDE.md`, Claude install
  targets, and Claude agent templates.
- Extended validation to cover Claude manifests, skill installs, and agent templates.

## 0.11.0 - 2026-05-27

This release is about **making Cursor a first-class platform**.

- Added Cursor platform parity with `CURSOR.md`, Cursor install support, Cursor Task
  subagent mapping, and Cursor goal-mode documentation.
- Reframed docs around platform-native capabilities instead of Codex-only behavior.

## 0.10.0 - 2026-05-27

This release is about **not declaring subagents unavailable too early, and not treating self-checks as acceptance**.

- Added dispatch discovery gates before declaring subagents unavailable.
- Required explicit dispatch exceptions and fresh-review labeling for non-lightweight
  acceptance paths.

## 0.9.0 - 2026-05-27

This release is about **Teamwork becoming its first versioned workflow package**.

- Released the first versioned Teamwork workflow-gates package.
- Added project initialization workflow support through `teamwork-init` and
  project-init references.
- Split responsibilities into focused skills for research, planning, execution,
  review, goal iteration, init, update, and auto-routing.
- Added evidence-first gates, durable artifacts, review-oriented acceptance, and
  automatic subagent routing.

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

This history is about **evolving from one optimization skill into Teamwork**.

- Started from a single optimization workflow.
- Gradually split out research, plan, execute, goal, and review router subskills.
- Added goal runtime commands, evidence gates, durable plan artifacts, and Codex auto-routing.
- Renamed the package to Teamwork and narrowed it to a Codex-first skill package
  before later re-expanding to multi-platform support.
