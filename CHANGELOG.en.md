# Changelog

[中文](CHANGELOG.md)

This changelog explains what users get after upgrading, not just which files
changed. Version boundaries come from `VERSION`, plugin manifests, and GitHub
release tags.

## 2.15.0 - 2026-07-13

This release **adds controls designed to reduce long-task context waste and
optional notification sounds that never steer the workflow**. Comparative
token savings remain to be measured on matched real tasks.

- Fresh subagents default to no inherited history and a first wave of at most
  two agents: one packet, one return. User corrections cancel invalid work, and
  `NOT VERIFIED` or a completed tranche cannot become whole-goal completion.
- A Stage Entry Card freezes objective, scope, acceptance oracle, truth
  identity, authority, and stop rules. Generic Codex dispatch now sends only
  fields exposed by the live runtime schema.
- Codex profiles now state the leaf-only contract explicitly. A read-only
  routing readiness check validates required fields, nickname uniqueness,
  catalog model/effort support, and prompt loading without mutating the catalog
  or treating `multi_agent_version` as spawn-selector evidence.
- A privacy-safe Codex session auditor separates historical
  `performance-first` evidence from current `cost-first` and labels
  cached/replayed tokens as operational telemetry rather than billing.
- `--notifications` installs main-turn completion and permission-request hook
  configuration for Codex/Claude Code. Codex was live-smoked on macOS; Claude
  was installation-tested but its runtime events remain unverified. Subagents
  stay silent; the hook reads metadata, emits neutral JSON, and fails open.
  Cursor remains unsupported until its local hook path is live-verified.
- The design follows current GPT-5.6 guidance: outcome-first prompts, each rule
  stated once, and explicit success/permission/stop conditions. Static contract
  evals pass; matched same-task quality/resource measurement is still pending.

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

This release makes Teamwork **guardrail-first and conditionally progressive for
GPT-5.6 instead of template-driven**.

- The six core stages are now roughly 300-word stage cards. Authorization,
  required state, evidence, scope, verification, and stop rules remain; fixed
  hypothesis counts, mandatory tables/diagrams, mega-packets, automatic
  artifacts, and blanket fresh review do not.
- The router activates for explicit Teamwork, cross-stage work, or an unclear
  next stage. Complex but sufficiently specified work proceeds; only a real
  user-owned decision gap triggers a question, and grill mode remains explicit.
- Cross-platform role templates are about 39% smaller. TDD, source census,
  alternatives, fresh context, and durable memory are conditional.
- A provenance-rich Codex live trajectory pilot can pin `gpt-5.6-sol` at
  `medium`, `high`, or `max`; unavailable models/efforts fail explicitly and
  never silently fall back.
- Validation now checks semantic invariants, size budgets, and a complex-task
  autonomy control. The `gpt56-role` Terra/Sol/Deep `max` mapping is unchanged.

## 2.12.0 - 2026-07-10

This release is about **adding a role-tiered GPT-5.6 profile for Codex
subagents**.

- Added `gpt56-role`: Explorer uses `gpt-5.6-terra` at `medium`; Worker uses
  `gpt-5.6-sol` at `medium`; Designer, Judge, and Reviewer use `gpt-5.6-sol` at
  `high`; Deep Judge/Reviewer use `gpt-5.6-sol` at `max`.
- The profile preserves native performance-first tiers on Cursor and Claude
  Code. Existing `performance-first`, `cost-first`, and `gpt55-*` profiles keep
  their prior behavior.
- The installer, readiness drift checks, project init, Codex global policy,
  READMEs, and validation now cover the new profile without silently migrating
  older profiles.
- The role split follows current Codex model guidance: Terra for read-heavy
  scans, Sol for complex implementation and judgment, and `max` for deep
  single-task acceptance. Ultra is not pinned inside a subagent because it can
  delegate again.

## 2.11.1 - 2026-07-08

This release is about **tightening the priority boundary between question-first
/ grill-me and lightweight direct action**.

- Lightweight tasks still default to direct action, but `using-teamwork` and the
  routing policy now state explicitly that `grill-me` / question-first overrides
  the lightweight fast path.
- Added a "simple task + explicit grill-me" eval fixture so one-line typo tasks
  cannot bypass the question-first override.
- Hardened the lightweight control sample checks: they now reject extra
  questions, grill ceremony, subagent dispatch, and durable plans instead of
  relying on a narrow keyword check.
- Init/update skills now include active grill/question-first maintenance guards
  before install or release changes continue.

## 2.11.0 - 2026-07-08

This release is about **turning question-first / grill-me into a cross-stage interaction protocol and making installed-surface drift checks more trustworthy**.

- Complex, uncertain, or non-lightweight tasks now ask an outcome-changing
  decision/risk question before planning or execution. Explicit `grill-me` /
  question-first requests inspect discoverable facts first, ask one recommended
  question, then stop until confirmation or exit.
- Research, debug, plan, execute, review, goal, init, update, and the
  Codex/Cursor/Claude Explorer, Designer, Judge, Worker, and Reviewer templates
  now share question-first override guards.
- Added question-first eval fixtures and three-platform static samples covering
  explicit grill, ordinary complex uncertainty, and lightweight direct-action
  control. The docs now state these are offline fixture/static-sample gates, not
  proof of live model behavior.
- `check-update.sh` now renders expected agent files from the installer profile
  and compares them byte-for-byte, so readiness and the normal report detect
  global/project agent content drift.
- Update/init commands are now directly runnable: project-local refresh uses
  `--project-root`, profile examples include `<profile> <target>`, and policy
  output targets no longer rewrite the checkout `.teamwork-profile`.
- Added the `gpt55-high` profile to pin Codex Teamwork subagents to gpt-5.5 high
  reasoning.

## 2.10.0 - 2026-07-08

This release is about **giving Teamwork a reusable SkillOpt-Lite/HarnessOpt-Lite candidate loop foundation**.

- Added `scripts/optimize-teamwork.py` to initialize optimizer workspaces, export
  result JSONL into file-native markdown samples, summarize scores, and apply a
  deterministic candidate gate.
- `scripts/eval-teamwork.py` now supports an optional `optimizer-candidates.jsonl`
  schema plus a standalone `--optimizer-ledger` validator; real candidates must
  carry provider/model/config, baseline/treatment, rollback, validation, reviewer,
  and related evidence instead of `not_applicable` placeholders.
- `scripts/validate.sh` now smokes the optimizer helper, valid/invalid candidate
  ledgers, score summaries, and gate decisions while cleaning temporary files.
- Review/update/eval-gate rules now state that actual SkillOpt-Lite/HarnessOpt-Lite
  participation requires trajectory samples, same-case baseline/treatment, gate,
  rollback, ledger, release audit, and fresh review.
- This is a verifiable optimization-pipeline foundation; it does not claim the
  scaffold itself is a completed real optimizer pilot.

## 2.9.0 - 2026-07-08

This release is about **using a file-native harness to govern and improve Teamwork's own skill behavior**.

- Added `evals/teamwork/` with tracked cases, rubrics, and ledgers for reusable
  behavior expectations across lightweight native controls, complex coding,
  debug, research, review, goal, release gates, and platform scope.
- Added `scripts/eval-teamwork.py`, an offline no-model runner that validates
  eval fixtures, dev/release splits, target surfaces, rubrics, and ledger schemas.
- `scripts/validate.sh` now checks the eval harness inventory and runs the dev
  split so skill/harness assets cannot drift silently.
- Added `eval-gate.md`, which makes evals maintenance evidence rather than a new
  runtime stage; ordinary lightweight user tasks are not forced through evals.
- `teamwork-review` and `teamwork-update` now require eval, ledger, and non-empty
  release split evidence for package behavior and release changes.

## 2.8.1 - 2026-07-08

This release is about **making grill mode and code-maintenance rules reach every critical execution entrypoint**.

- `grill me` now pauses research synthesis, design selection, goal handoff,
  edits, and planning/design/execution agent dispatch, not only planning and implementation.
- Research, plan, goal, review, Designer, Judge, Worker, and Reviewer rules now
  share the Shared Understanding Packet precondition before synthesis, direction
  choice, or delegation.
- Code maintenance is now a precondition for every code write path: understand
  owner, control flow, tests/config, and invariants before editing the current path.
  Reviewers check that baseline for every code diff.
- `check-update.sh` and validation now inspect policy and agent content anchors,
  so stale installed global/project surfaces are detected.
- Codex, Cursor, and Claude Code global policies, agent templates, and
  project-local installs now share the hardened rules.

## 2.8.0 - 2026-07-08

This release is about **actually asking first when the user explicitly asks to be grilled**.

- Added an explicit grill/question-first protocol: when the user says grill me,
  ask before acting, challenge assumptions, or similar, Teamwork must ask at
  least one decision/risk question and include a recommended answer.
- Grill mode pauses planning, implementation, goal start, and Worker dispatch
  until the user confirms a Shared Understanding Packet or explicitly exits grill mode.
- Plan, execute, goal, review, and debug stages now share the constraint so the
  system does not claim it will clarify first and then immediately start doing.
- `check-update.sh` now checks installed skill file content drift, including
  project-local skill content drift; validation adds a regression for that path.
- Installed Codex, Cursor, and Claude Code global policies now include grill
  mode and a leaner dispatch boundary.

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
