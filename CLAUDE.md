@AGENTS.md

# Teamwork for Claude Code

Teamwork adds focused methods for collaborative convergence, external research,
unknown-cause debugging, planning, review, and
long-running convergence. Claude Code keeps local evidence inspection and clear
authorized implementation on its native path and still controls tools,
permissions, agents, and prompts. There is no generic Execute or router skill.

## Quick setup

Install every supported host or Claude Code alone:

```bash
./install.sh all
./install.sh claude
```

Choose a lower-cost profile or notification behavior when needed:

```bash
./install.sh claude --profile cost-first
./install.sh claude --profile cost-first --notifications
./install.sh claude --no-notifications
```

The default `performance-first` profile balances routine work with deeper
review. Run `./install.sh --help` for advanced options, and use `--link` only
while developing Teamwork from this checkout.

## Everyday use

Ask for the outcome you want:

- "Inspect this repository and implement the requested validation change."
- "Research the current provider options from official sources and cite them."
- "Brainstorm a lower-maintenance onboarding flow with me, then ask the most useful next question."
- "Decide the public API boundary and recommend among the real alternatives."
- "This public API could be synchronous, queued, or hybrid; a wrong choice forces costly client migration and the evidence conflicts. Help me decide."
- "Diagnose why this test started failing, then verify the fix on the same path."
- "Turn the selected migration direction into a plan without changing files."
- "Review this diff against the requirements and direct evidence."
- "Keep working until this command is green."

Claude Code natively handles local repository, configuration, test, log,
runtime, and artifact inspection. Clear authorized implementation also stays
native. Use `teamwork-explore` for a distinct read-only local evidence question,
and `teamwork-research` only for external, current, multi-source, or
citation-backed research. Use `teamwork-collaborate` for natural discussion,
brainstorming, stress-testing, question-before-action, or an unsettled
consequential solution. Challenge and adversarial search are Collaborate
methods, not public mode names. Use `teamwork-plan` only after controlled
Collaborate records `acceptance: accepted`. Collaborate uses Explorer only for
an unresolved local constraint and sanitized external Research only for a named
external/current claim that can change the choice; it never runs both by
default. It compares 2-3 real alternatives or records safe-path evidence,
applies the needed challenge/adversarial method, and keeps the decision frontier
finite. It contributes
synthesis, candidate space, a decision map, or provisional recommendation before
asking. Its controlled transaction records `acceptance: pending`, `accepted`, or
`blocked`; persistence is not acceptance, and only `accepted` is Plan-ready.

Before asking, Root inspects discoverable state and acts on safe, reversible
defaults. If one undiscoverable user-owned value is required, Root asks for that
exact gap once, pauses only dependent work, and resumes the same workflow.
Latent preferences or unformed intent that can materially change the outcome
enter Collaborate, which contributes and recommends before asking. Leaf roles
never ask or activate Collaborate; they return an exact gap or reclassification
signal to Root, and the same question is not repeated across roles or stages.

Legacy-v1, old grill, Discussion, and Design records are Init/Update semantic
migration inputs only. Independent
Plan Review runs only on user request or a named material risk gate. It does not
implement the result or enter Plan silently.

Collaborate chooses its search strategy from the request and evidence. It uses
the internal read-only Designer for direction selection, a frozen-hypothesis
challenge, or a search-closure audit. It selects adversarial only when at least
two viable directions remain and costly or irreversible error or conflicting
evidence makes one challenge inadequate; “high-risk” or “complex” alone is
insufficient. `adversarial` forces the method and `standard` disables it. The
model states its reason and uses default `B=3` without another confirmation.
Every hypothesis then receives two fresh isolated Designer critics and two new
final auditors must both pass. Missing isolation, exhausted budget, or failed
closure returns an incomplete result whose controlled state remains `pending` or
becomes `blocked`; it cannot be `accepted` or Plan-ready. A passing chat
recommendation is not Plan-ready. Only a controlled Collaborate state with
`acceptance: accepted` may enter Plan.

Debug begins with the real failure and reproduction. Plan translates an
accepted Collaborate handoff into owned executable steps; Review does not edit the candidate and returns
`ACCEPT`, `REVISE`, or `BLOCKED`; Goal persists an explicit objective, success
signal, scope, budget, and attempts before it iterates. Clear authorized code
work remains result-first: change the canonical owner, reuse existing
patterns/built-ins/suitable dependencies, add the smallest complete logic, and
prove each Worker slice with proportional focused tests plus the real path.
After Root integrates and seals one candidate, an independent max Review runs
once only on user request or a named material risk gate; findings form one repair
batch with at most one delta recheck per candidate.

Skill selection remains model behavior rather than deterministic routing. Name
a skill when its exact method matters. Research, Collaborate, Plan, and Review do not
authorize candidate edits or external effects; their reusable artifacts still
persist by default under the named-workflow contract. Debug makes no change when
diagnosis alone was requested; an original request that already authorizes a fix
allows the evidenced narrow change. Approving a design or plan does not
authorize implementation.

Collaborate selects `dialogue` or `brainstorm`, contributes before
asking, and never asks the user to name a mode. Open questions stay in prose; a
host-native choice surface is appropriate only for a genuine finite decision
with two or three mutually exclusive options. Sustained pressure-testing follows
the complete global -> boundary -> detail map, batches at most three independent
decisions, serializes dependent decisions, and applies one semantic Collaborate
update per answered batch.

In an initialized writable project, named Teamwork workflows persist reusable
checkpoints and results by default; `no files`, off-record, read-only, or
no-write overrides that default. One-shot explanations, casual fact questions,
and tiny native work create no standalone artifact. Collaborate, Goal, Research,
Debug, Plan, Plan Review, Review, mutating Init/Update, and a terminal execution
handoff with an explicit consumer and no active Goal write their selected
case-v2 artifact. An active Goal suppresses duplicate execution artifacts.
Explore creates no standalone report; its evidence is folded into the consuming
artifact or answer.

Teamwork 6.0 is a hard cut for normal runtime: runtime writes use v2 case
bundles under `docs/teamwork/cases/c-<64hex>/`, where
Collaborate, Plan, Research, Debug, Review, Goal, and execution results attach
to one case. legacy-v1 is not a compatible runtime mode. Init/Update may read
legacy-v1 and old grill/Discussion/Design records only as semantic migration
input during an exact one-time project-root migration. Update/install alone
never claims to migrate, rewrite, or delete existing `docs/teamwork`; the
cold-archive and restore-drill gates remain.

Research, Explore, Debug, Plan, and Review require their owning leaf. If Claude
Code cannot provide that capability, the workflow returns capability-blocked
instead of falling back to Root or another role. Collaborate and Goal remain
Root-owned.

Sustained Collaborate intent plus a substantive synthesis, candidate space, or
decision map and an unresolved question or unaccepted direction defaults to one
semantic checkpoint after reading `docs/teamwork/index.json`: v6 writes the
selected case manifest and `live/collaborate.md` through case transactions.
Frozen legacy-v1, old grill, Discussion, and Design records remain readable
only as Init/Update migration inputs.
Unchanged state is a no-op. Collaborate never stores a transcript or substitutes
a report/conclusion; `no files`, off-record, read-only, or no-write wins.

## Initialize a project

```bash
./install.sh --project-root /path/to/project init-project
```

Initialization changes only the selected repository. It establishes
Teamwork-managed project instructions, memory entry points, ignore rules, and
CodeGraph context when available. It does not refresh global skills, agents,
policy, routing, or notifications, and it does not copy Teamwork skills or
agents into the project. Use `teamwork-update` or `./install.sh all` separately
for global setup.

## Agents and profiles

Teamwork may use nine Claude Code roles—Researcher, Explorer, Debugger,
Designer, Planner, Worker, Writer, Plan Reviewer, and Reviewer—when separate
context, standalone document writing, or independent acceptance is worth the
coordination cost. Default dispatch is one child, everyday work is capped at
four, and five to eight children are reserved for explicit adversarial or
release work when Claude Code supports that concurrency. Writer uses a simple
`haiku`/`medium` profile and a frozen
bounded packet for standalone docs and runtime artifacts. It may draft,
organize, summarize, translate, and polish, but must not research, invent,
paraphrase, or change frozen facts, citations, decisions, authority, status, or
acceptance; missing route/readback fails closed as unsaved. Code
comments, docstrings, tests, schemas, manifests, machine config, inline config
text, and other code-coupled wording stay with implementation owners. The main turn owns scope,
integration, and the final answer. Routine local work does not require an agent handoff.
`performance-first` and `cost-first` select Claude Code-native host templates;
they do not promise the Codex model or reasoning-effort mapping on Claude Code.

## Policy and notifications

Claude installs maintain only the Teamwork-owned block in
`~/.claude/CLAUDE.md` and preserve unrelated content. Inspect the block without
installing it with:

```bash
./install.sh claude-policy
```

Notifications cover main-turn completion and permission requests; subagents are
silent. `--no-notifications` removes only Teamwork-owned handlers. Hook
activation still depends on Claude Code trust. Static installation checks do
not prove live event delivery.

Teamwork does not override Claude Code permissions, MCP, tests, tools, UI, or
model behavior. Required paths, ports, credentials, commands, models, and
execution modes must come from the user or project evidence.

## Update and troubleshoot

```bash
./scripts/check-update.sh --readiness
./install.sh all
```

Use `teamwork-update` for a guided global refresh and `teamwork-init` only for
one repository's context. If skill selection is wrong, invoke the skill by
name. If notifications do not fire, check hook trust and the selected
notification setting. Readiness covers Teamwork-managed files and bounded
configuration; it cannot prove live hook delivery, model behavior, or
deterministic skill selection.

See the [main README](README.en.md) for the shared capability overview and the
[changelog](CHANGELOG.en.md) for upgrade details.
